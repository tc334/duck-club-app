from flask import Blueprint, request, jsonify
from .. import db
from .auth_wraps import token_required, admin_only, all_members, manager_and_above
from .hunts import get_current_prehunt

table_name = 'scouting_reports'
scouts_bp = Blueprint(table_name, __name__)


@scouts_bp.route('/scouts', methods=['POST'])
@token_required(manager_and_above)
def add_row(user):
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"message": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    if "pond_id" not in data_in:
        return jsonify({"message": "Input json missing key 'pond_id' in " + base_identifier}), 400
    # check for duplicates - can't have 2 entries with same pond & hunt
    hunt_dict = get_current_prehunt()
    if not hunt_dict:
        return jsonify({"message": "Could not find an open hunt to associate with this new scouting report"}), 400
    existing = db.read_custom(
        f"SELECT id FROM {table_name} "
        f"WHERE pond_id = '{data_in['pond_id']}' "
        f"AND hunt_id = '{hunt_dict['id']}'")
    if existing is None:
        return jsonify({"message": "Internal error"}), 400
    if existing:
        return jsonify({"message": "Entry already exists in " + table_name + " that matches this hunt and pond"}), 400

    # database interaction #2 - write
    data_in['hunt_id'] = hunt_dict['id']
    data_in['created_by'] = user['id']
    db.add_row(table_name, data_in)

    return jsonify({"message": "Successfully added new scouting report"}), 201


@scouts_bp.route('/scouts', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    # returns all scouting reports from the current hunt
    hunt_dict = get_current_prehunt()
    if not hunt_dict:
        return jsonify({"message": "Could not find an open hunt to pull scouting reports from"}), 400

    print(f"Alpha:{hunt_dict}")
    results = db.read_custom(
        f"SELECT scouting_reports.id, properties.name, ponds.name, count, notes, first_name "
        f"FROM scouting_reports "
        f"JOIN users ON users.id=scouting_reports.created_by "
        f"JOIN ponds ON ponds.id=scouting_reports.pond_id "
        f"JOIN properties ON ponds.property_id=properties.id "
        f"WHERE hunt_id={hunt_dict['id']}"
    )
    if results is None or results is False:
        return jsonify({"message": "Internal error"}), 500
    names = ["id", "property", "pond", "count", "notes", "scout"]
    scout_dict = db.format_dict(names, results)
    return jsonify({"data": scout_dict}), 200


@scouts_bp.route('/scouts/<report_id>', methods=['PUT'])
@token_required(manager_and_above)
def update_row(user, report_id):
    data_in = request.get_json()

    keys_in = set(data_in.keys())
    allowable_keys = {"count", "notes", "pond_id"}
    # no extra keys
    if len(keys_in - allowable_keys) > 0:
        return jsonify({'message': 'extra, unsupported keys in scouting report update'})
    # must have at least 1 allowable key
    if len(allowable_keys - keys_in) == len(allowable_keys):
        return jsonify({'message': 'missing required key in scouting report update'})
    if db.update_row(table_name, report_id, data_in):
        return jsonify({'message': f'Successful update of id {report_id} in {table_name}'}), 200
    else:
        return jsonify({"message": f"Unable to update id {report_id} of table {table_name}"}), 400


@scouts_bp.route('/scouts/<report_id>', methods=['DELETE'])
@token_required(admin_only)
def del_row(user, report_id):
    if db.del_row(table_name, report_id):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {report_id} from table {table_name}"}), 400
