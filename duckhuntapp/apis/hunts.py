from flask import Blueprint, request, jsonify
from .. import db
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above
import math


hunts_bp = Blueprint('hunts', __name__)
table_name = 'hunts'


@hunts_bp.route('/hunts', methods=['POST'])
@token_required(manager_and_above)
def add_row(user):
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"error": "Input json is empty in " + base_identifier}), 400

    # check to make sure there isn't already another hunt on the same day
    existing = db.read_custom(f"SELECT id FROM {table_name} WHERE hunt_date = '{data_in['hunt_date']}'")
    if existing is None:
        return jsonify({"message": "Internal error"}), 500
    if existing:
        return jsonify({"message": f"Cannot modify this hunt because hunt {existing[0][0]} already exists on date {data_in['hunt_date']}"}), 400

    # check to make sure there is only one hunt at a time in these status levels (hunt_closed will have many)
    if 'status' in data_in and data_in['status'] in ('signup_open', 'signup_closed', 'draw_complete', 'hunt_open'):
        existing = db.read_custom(f"SELECT id, status FROM {table_name} WHERE status = '{data_in['status']}'")
        if existing is None:
            return jsonify({"message": "Internal error"}), 400
        if existing:
            return jsonify({"message": f"Cannot add this hunt because hunt {existing[0][0]} already has status {data_in['status']}"}), 400

    # database interaction #2 - write
    db.add_row(table_name, data_in)
    return jsonify({"message": "New hunt started"}), 201


@hunts_bp.route('/hunts', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    results = db.read_all(table_name)
    return jsonify({"hunts": results}), 200


@hunts_bp.route('/hunts/active', methods=['GET'])
@token_required(all_members)
def get_all_active(user):
    results = db.read_custom(
        f"SELECT * FROM {table_name} WHERE hunts.status != 'hunt_closed' ORDER BY hunt_date")

    if results is not None:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        results_dict = db.format_dict(None, results, table_name)
        time_keys = ["signup_closed_time", "hunt_open_time", "hunt_close_time"]
        for item in results_dict:
            for key in time_keys:
                item[key] = convert_time(item[key].seconds)
        return jsonify({"hunts": results_dict}), 200
    else:
        return jsonify({"error": f"unknown error trying to read hunts"}), 400


@hunts_bp.route('/hunts/signup_open', methods=['GET'])
@token_required(manager_and_above)
def get_signup_open(user):
    results = db.read_custom(f"SELECT id, hunt_date FROM {table_name} WHERE hunts.status = 'signup_open'")

    if results is not None:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["id", "hunt_date"]
        results_dict = db.format_dict(names_all, results)
        return jsonify({"hunts": results_dict}), 200
    else:
        return jsonify({"error": f"unknown error trying to read hunts"}), 400


def convert_time(time_of_day_sec):
    sec_in_min = 60
    sec_in_hr = sec_in_min * 60
    hours = math.floor(time_of_day_sec / sec_in_hr)
    minutes = math.floor((time_of_day_sec - hours*sec_in_hr) / sec_in_min)
    return f"{hours:02d}:{minutes:02d}"


@hunts_bp.route('/hunts/<hunt_id>', methods=['GET'])
@token_required(all_members)
def get_one_row(users, hunt_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE id={hunt_id}")

    if result and len(result) == 1:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = [a_dict["name"] for a_dict in db.tables[table_name].table_cols]
        results_dict = {name: result[0][col] for col, name in enumerate(names_all)}
        return jsonify({"hunt": results_dict}), 200
    else:
        return jsonify({"error": f"Could not find id {hunt_id} in table {table_name}"}), 400


@hunts_bp.route('/hunts/<hunt_id>', methods=['PUT'])
@token_required(manager_and_above)
def update_row(user, hunt_id):
    data_in = request.get_json()

    # check to make sure there isn't already another hunt on the same day
    if 'hunt_date' in data_in:
        existing = db.read_custom(f"SELECT id FROM {table_name} WHERE id != {hunt_id} AND hunt_date = '{data_in['hunt_date']}'")
        print(f"Alpha:{existing}")
        if existing is None:
            return jsonify({"message": "Internal error"}), 400
        if existing:
            return jsonify({"message": f"Cannot modify this hunt because hunt {existing[0][0]} already exists on date {data_in['hunt_date']}"}), 400

    # check to make sure there is only one hunt at a time in these status levels (hunt_closed will have many)
    if 'status' in data_in and data_in['status'] in ('signup_open', 'signup_closed', 'draw_complete', 'hunt_open'):
        existing = db.read_custom(f"SELECT id, status FROM {table_name} WHERE id != {hunt_id} AND status = '{data_in['status']}'")
        print(f"Bravo:{existing}")
        if existing is None:
            return jsonify({"message": "Internal error"}), 400
        if existing:
            return jsonify({"message": f"Cannot modify this hunt because hunt {existing[0][0]} already has status {data_in['status']}"})

    if db.update_row(table_name, hunt_id, data_in):
        return jsonify({'message': f'Successful update of id {hunt_id} in {table_name}'}), 200
    else:
        return jsonify({"message": f"Unable to update id {hunt_id} of table {table_name}"}), 400


@hunts_bp.route('/hunts/<hunt_id>', methods=['DELETE'])
@token_required(manager_and_above)
def del_row(user, hunt_id):
    if db.del_row(table_name, hunt_id):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {hunt_id} from table {table_name}"}), 400
