from flask import Blueprint, request, jsonify
from .. import db
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above

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
    # mandatory keys
    mandatory_keys = ('hunt_date',)
    for key in mandatory_keys:
        if key not in data_in:
            return jsonify({"error": f"Input json missing key '{key}' in " + base_identifier}), 400
    # there can only be one hunt open at a time
    existing = db.read_custom(f"SELECT id FROM {table_name} WHERE status != 'hunt_closed'")
    if existing is None:
        return jsonify({"error": "Internal error"}), 400
    if existing:
        return jsonify({"error": f"Cannot start new hunt because hunt {existing[0][0]} is already active"})

    # database interaction #2 - write
    db.add_row(table_name, data_in)

    return jsonify({"message": "New hunt started"}), 201


@hunts_bp.route('/hunts', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    results = db.read_all(table_name)
    return jsonify({"hunts": results}), 200


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
    if 'status' in data_in and data_in['status'] in ('signup_open', 'signup_closed', 'draw_complete', 'hunt_open'):
        # check to make sure there isn't already another hunt open
        # there can only be one hunt open at a time
        existing = db.read_custom(f"SELECT id FROM {table_name} WHERE id != {hunt_id} AND status != 'hunt_closed'")
        if existing is None:
            return jsonify({"error": "Internal error"}), 400
        if existing:
            return jsonify({"error": f"Cannot modify this hunt because hunt {existing[0][0]} is already active"})

    if db.update_row(table_name, hunt_id, data_in):
        return jsonify({'message': f'Successful update of id {hunt_id} in {table_name}'}), 200
    else:
        return jsonify({"error": f"Unable to update id {hunt_id} of table {table_name}"}), 400


@hunts_bp.route('/hunts/<hunt_id>', methods=['DELETE'])
@token_required(manager_and_above)
def del_row(user, hunt_id):
    if db.del_row(table_name, hunt_id):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {hunt_id} from table {table_name}"}), 400
