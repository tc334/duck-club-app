from flask import Blueprint, request, jsonify
from .. import db
from .auth_wraps import token_required, admin_only, owner_and_above, all_members

properties_bp = Blueprint('properties', __name__)
table_name = 'properties'


@properties_bp.route('/properties', methods=['POST'])
@token_required(owner_and_above)
def add_row(user):
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"error": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    if "name" not in data_in:
        return jsonify({"error": "Input json missing key 'name' in " + base_identifier}), 400
    # check for duplicates
    existing = db.read_custom(f"SELECT * FROM {table_name} WHERE name = '{data_in['name']}'")
    if existing is None:
        return jsonify({"error": "Internal error"}), 400
    if existing:
        return jsonify({"error": "Entry " + data_in["name"] + " already exists in " + table_name})

    # database interaction #2 - write
    db.add_row(table_name, data_in)

    return jsonify({"message": data_in["name"] + " successfully added to " + table_name}), 201


@properties_bp.route('/properties', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    results = db.read_all(table_name)
    return jsonify({"properties": results}), 200


@properties_bp.route('/properties/<property_id>', methods=['GET'])
@token_required(all_members)
def get_one_row(users, property_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE id={property_id}")

    if result and len(result) == 1:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = [a_dict["name"] for a_dict in db.tables[table_name].table_cols]
        results_dict = {name: result[0][col] for col, name in enumerate(names_all)}
        return jsonify({"property": results_dict}), 200
    else:
        return jsonify({"error": f"Could not find id {property_id} in table {table_name}"}), 400


@properties_bp.route('/properties/<property_id>', methods=['PUT'])
@token_required(owner_and_above)
def update_row(user, property_id):
    data_in = request.get_json()
    if db.update_row(table_name, property_id, data_in):
        return jsonify({'message': f'Successful update of id {property_id} in {table_name}'}), 200
    else:
        return jsonify({"error": f"Unable to update id {property_id} of table {table_name}"}), 400


@properties_bp.route('/properties/<property_id>', methods=['DELETE'])
@token_required(owner_and_above)
def del_row(user, property_id):
    if db.del_row(table_name, property_id):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {property_id} from table {table_name}"}), 400
