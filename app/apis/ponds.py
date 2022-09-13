from flask import Blueprint, request, jsonify
from .. import db, cache
from .auth_wraps import token_required, manager_and_above, owner_and_above, all_members, admin_only

ponds_bp = Blueprint('ponds', __name__)
table_name = 'ponds'


@ponds_bp.route('/ponds', methods=['POST'])
@token_required(owner_and_above)
def add_row(user):
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"error": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    mandatory_keys = ('name',)
    for key in mandatory_keys:
        if key not in data_in:
            return jsonify({"error": f"Input json missing key '{key}' in " + base_identifier}), 400
    # check for duplicates
    existing = db.read_custom(f"SELECT * FROM {table_name} WHERE name = '{data_in['name']}'")
    if existing is None:
        return jsonify({"error": "Internal error"}), 400
    if existing:
        return jsonify({"error": "Entry " + data_in["name"] + " already exists in " + table_name})

    # database interaction #2 - write
    db.add_row(table_name, data_in)
    cache.delete("delta")

    return jsonify({"message": data_in["name"] + " successfully added to " + table_name}), 201


@ponds_bp.route('/ponds', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    results = db.read_all(table_name)
    return jsonify({"ponds": results}), 200


@ponds_bp.route('/ponds/<pond_id>', methods=['GET'])
@token_required(all_members)
def get_one_row(users, pond_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE id={pond_id}")

    if result and len(result) == 1:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = [a_dict["name"] for a_dict in db.tables[table_name].table_cols]
        results_dict = {name: result[0][col] for col, name in enumerate(names_all)}
        return jsonify({"pond": results_dict}), 200
    else:
        return jsonify({"error": f"Could not find id {pond_id} in table {table_name}"}), 400


@ponds_bp.route('/pond_status', methods=['GET'])
@token_required(all_members)
def get_pond_status(users):
    results = db.read_custom(f"SELECT id, name, status FROM {table_name} ORDER BY property_id")

    if results:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["id", "name", "status"]
        results_dict = db.format_dict(names_all, results)
        return jsonify({"ponds": results_dict}), 200
    else:
        return jsonify({"error": f"unknown error trying to read pond status"}), 400


@ponds_bp.route('/ponds/<pond_id>', methods=['PUT'])
@token_required(owner_and_above)
def update_row(user, pond_id):
    data_in = request.get_json()
    if db.update_row(table_name, pond_id, data_in):
        cache.delete("delta")
        return jsonify({'message': f'Successful update of id {pond_id} in {table_name}'}), 200
    else:
        return jsonify({"error": f"Unable to update id {pond_id} of table {table_name}"}), 400


@ponds_bp.route('/ponds', methods=['PUT'])
@token_required(manager_and_above)
def update_many_rows(user):
    data_in = request.get_json()
    for d in data_in:
        # this API only allows the status field to change
        if len(d) == 2 and "id" in d and "status" in d:
            pond_id = d["id"]
            if not db.update_row(table_name, pond_id, d):
                return jsonify({"error": f"Unable to update id {pond_id} of table {table_name}"}), 400

    # if you made it here, the operation was a success
    cache.delete("delta")
    return jsonify({'message': f'Successful update of {table_name}'}), 200


@ponds_bp.route('/ponds/<pond_id>', methods=['DELETE'])
@token_required(admin_only)
def del_row(user, pond_id):
    if db.del_row(table_name, pond_id):
        cache.delete("delta")
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {pond_id} from table {table_name}"}), 400


@ponds_bp.route('/ponds/reset_selections', methods=['GET'])
@token_required(manager_and_above)
def reset_selections(user):
    if db.update_custom(
        f"UPDATE {table_name} SET selected=false"
    ):
        return jsonify({'message': f'Successful update of {table_name}'}), 200
    else:
        return jsonify({"message": "unsuccessful attempt to reset pond selections"}), 400



