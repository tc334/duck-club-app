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
    if existing:
        return jsonify({"error": "Entry " + data_in["name"] + " already exists in " + table_name})

    db.add_row(table_name, data_in)

    return jsonify({"message": data_in["name"] + " successfully added to " + table_name}), 201


@birds_bp.route('/birds', methods=['GET'])
def get_all_rows():
    return ""


@birds_bp.route('/birds/<bird_id>', methods=['GET'])
def get_one_row(bird_id):
    return ""


@birds_bp.route('/birds/<bird_id>', methods=['PUT'])
def update_row(bird_id):
    return ""


@birds_bp.route('/birds/<bird_id>', methods=['DELETE'])
def del_row(bird_id):
    return ""
