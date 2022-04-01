from flask import Blueprint, request, jsonify
from .. import db

birds_bp = Blueprint('birds', __name__)
table_name = 'birds'


@birds_bp.route('/birds', methods=['POST'])
def add_row():
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"error": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    if "name" not in data_in:
        return jsonify({"error": "Input json missing key 'name' in " + base_identifier}), 400
    if "type" not in data_in:
        return jsonify({"error": "Input json missing key 'type' in " + base_identifier}), 400
    # check for duplicates
    existing = db.read_custom(f"SELECT * FROM {table_name} WHERE name = '{data_in['name']}'")
    if existing is None:
        return jsonify({"error": "Internal error"}), 400
    if existing:
        return jsonify({"error": "Entry " + data_in["name"] + " already exists in " + table_name})

    # database interaction #2 - write
    db.add_row(table_name, data_in)

    return jsonify({"message": data_in["name"] + " successfully added to " + table_name}), 201


@birds_bp.route('/birds', methods=['GET'])
def get_all_rows():
    results = db.read_all(table_name)
    return jsonify({"birds": results}), 200


@birds_bp.route('/birds/<bird_id>', methods=['GET'])
def get_one_row(bird_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE id={bird_id}")

    if result and len(result) == 1:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = [a_dict["name"] for a_dict in db.tables[table_name].table_cols]
        results_dict = {name: result[0][col] for col, name in enumerate(names_all)}
        return jsonify({"bird": results_dict}), 200
    else:
        return jsonify({"error": f"Could not find id {bird_id} in table {table_name}"}), 400


@birds_bp.route('/birds/<bird_id>', methods=['PUT'])
def update_row(bird_id):
    data_in = request.get_json()
    if db.update_row(table_name, bird_id, data_in):
        return jsonify({'message': f'Successful update of id {bird_id} in {table_name}'}), 200
    else:
        return jsonify({"error": f"Unable to update id {bird_id} of table {table_name}"}), 400


@birds_bp.route('/birds/<bird_id>', methods=['DELETE'])
def del_row(bird_id):
    if db.del_row(table_name, bird_id):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {bird_id} from table {table_name}"}), 400
