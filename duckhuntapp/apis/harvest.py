from flask import Blueprint, request, jsonify
from .. import db
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above

harvests_bp = Blueprint('harvests', __name__)
table_name = 'harvest'


@harvests_bp.route('/harvests', methods=['POST', 'PUT'])
@token_required(all_members)
def update_harvest(user):
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + update_harvest.__name__
    if data_in is None:
        return jsonify({"error": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    mandatory_keys = ('group_id', 'count', 'bird_id')
    for key in mandatory_keys:
        if key not in data_in:
            return jsonify({"error": f"Input json missing key '{key}' in " + base_identifier}), 400
    # member attempting to post/put harvest must be in this group and hunt must be active
    # manager and above can modify any harvest at any time
    if user["level"] == "member":
        # 1. check to make sure user is in group
        slot_ids = db.read_custom(
            f"SELECT u.public_id FROM users u INNER JOIN groupings g ON u.id = g.slot1_id OR u.id = g.slot2_id OR u.id = slot3_id OR u.id = slot4_id WHERE g.id = {data_in['group_id']}")
        slot_ids = [slot_ids[idx][0] for idx in range(len(slot_ids))]
        if not user["public_id"] in slot_ids:
            return jsonify({"error": "Members can only post harvest results to their own hunts"}), 400
        # 2. check to make sure hunt is active
        result = db.read_custom(f"SELECT h.status, h.id FROM hunts h INNER JOIN groupings g ON (g.hunt_id = h.id AND g.id = {data_in['group_id']})")
        if len(result) > 0:
            hunt_status = result[0][0]
            hunt_id = result[0][1]
        else:
            return jsonify({"error": f"Could not find a hunt associated with group {data_in['group_id']}"})
        if hunt_status != 'hunt_open':
            return jsonify({"error": f"Member cannot modify harvest for hunt {hunt_id} because hunt status is {hunt_status}"})

    # check to see if a record already exists
    existing = db.read_custom(f"SELECT id FROM {table_name} WHERE group_id = {data_in['group_id']} AND bird_id = {data_in['bird_id']}")
    if existing is None:
        return jsonify({"error": "Internal error"}), 400
    if existing:
        harvest_id = existing[0][0]
        print(f"harvest_id={harvest_id}")
        if db.update_row(table_name, harvest_id, data_in):
            return jsonify({'message': f"Successful update of id {harvest_id} in {table_name}"}), 200
        else:
            return jsonify({"error": f"Unable to update id {harvest_id} of table {table_name}"}), 400
    else:
        db.add_row(table_name, data_in)
        return jsonify({"message": "New entry successfully added to " + table_name}), 201


@harvests_bp.route('/harvests', methods=['GET'])
@token_required(admin_only)
def get_all_rows(user):
    results = db.read_all(table_name)
    return jsonify({"harvests": results}), 200


@harvests_bp.route('/harvests/<harvest_id>', methods=['GET'])
@token_required(all_members)
def get_one_row(users, harvest_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE id={harvest_id}")

    if result and len(result) == 1:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = [a_dict["name"] for a_dict in db.tables[table_name].table_cols]
        results_dict = {name: result[0][col] for col, name in enumerate(names_all)}
        return jsonify({"harvest": results_dict}), 200
    else:
        return jsonify({"error": f"Could not find id {harvest_id} in table {table_name}"}), 400


@harvests_bp.route('/harvests/<harvest_id>', methods=['DELETE'])
@token_required(manager_and_above)
def del_row(user, harvest_id):
    if db.del_row(table_name, harvest_id):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {harvest_id} from table {table_name}"}), 400
