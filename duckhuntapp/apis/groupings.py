from flask import Blueprint, request, jsonify
from .. import db
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above

groupings_bp = Blueprint('groupings', __name__)
table_name = 'groupings'


@groupings_bp.route('/groupings', methods=['POST'])
@token_required(all_members)
def add_row(user):
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"error": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    mandatory_keys = ('hunt_id', 'slot1_id', 'slot1_type')
    for key in mandatory_keys:
        if key not in data_in:
            return jsonify({"error": f"Input json missing key '{key}' in " + base_identifier}), 400
    # groups can only be added to active hunts
    active = db.read_custom(f"SELECT id FROM hunts WHERE status != 'hunt_closed'")
    if active is None:
        return jsonify({"error": "Internal error"}), 400
    if active and data_in["hunt_id"] != active[0][0]:
        return jsonify({"error": f"Group cannot be added because hunt {data_in['hunt_id']} is not active"})
    # hunters must exist in users table and have active status to join a hunt
    for slot in range(1, 5):
        key = 'slot' + str(slot) + '_id'
        if key in data_in:
            temp = db.read_custom(f"SELECT status FROM users WHERE id = '{data_in[key]}'")
            if len(temp) == 0 or "inactive" in temp[0]:
                return jsonify({"error": f"Hunter {data_in[key]} does not have active status in the club"})
    # members can only create groupings for themselves
    if user['level'] == "member":
        user_id = db.read_custom(f"SELECT id FROM users WHERE public_id = '{user['public_id']}'")
        if data_in['slot1_id'] != user_id[0][0]:
            return jsonify({"error": f"Members can only start groups by themselves"})
    # check all group members to make sure they aren't already signed up in another group
    temp = db.read_custom(f"SELECT id, slot1_id, slot2_id, slot3_id, slot4_id FROM groupings WHERE hunt_id = '{data_in['hunt_id']}'")
    existing_group_id = [item[0] for item in temp]
    existing_slot_ids = [item[1:] for item in temp]
    for slot in range(1, 5):
        key = 'slot' + str(slot) + '_id'
        if key in data_in:
            duplicate = [idx for idx, item in enumerate(existing_slot_ids) if data_in[key] in item]
            if len(duplicate) > 0:
                return jsonify({"error": f"Hunter {data_in[key]} you are trying to add to slot {slot} is already in group {[existing_group_id[i] for i in duplicate]}"})

    # Input passes criteria - write to database
    db.add_row(table_name, data_in)

    return jsonify({"message": "New group successfully added to hunt " + str(data_in['hunt_id'])}), 201


@groupings_bp.route('/groupings', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    results = db.read_all(table_name)
    return jsonify({"groupings": results}), 200


@groupings_bp.route('/groupings/<grouping_id>', methods=['GET'])
@token_required(all_members)
def get_one_row(users, grouping_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE id={grouping_id}")

    if result and len(result) == 1:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = [a_dict["name"] for a_dict in db.tables[table_name].table_cols]
        results_dict = {name: result[0][col] for col, name in enumerate(names_all)}
        return jsonify({"grouping": results_dict}), 200
    else:
        return jsonify({"error": f"Could not find id {grouping_id} in table {table_name}"}), 400


@groupings_bp.route('/groupings/<grouping_id>', methods=['PUT'])
@token_required(manager_and_above)
def update_row(user, grouping_id):
    data_in = request.get_json()
    if db.update_row(table_name, grouping_id, data_in):
        return jsonify({'message': f'Successful update of id {grouping_id} in {table_name}'}), 200
    else:
        return jsonify({"error": f"Unable to update id {grouping_id} of table {table_name}"}), 400


@groupings_bp.route('/groupings/<grouping_id>', methods=['DELETE'])
@token_required(manager_and_above)
def del_row(user, grouping_id):
    if db.del_row(table_name, grouping_id):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {grouping_id} from table {table_name}"}), 400


@groupings_bp.route('/groupings/merge/<group1_id>/<group2_id>', methods=['PUT'])
@token_required(manager_and_above)
def merge_groups(user, group1_id, group2_id):

    # hunters from group 2 will be placed into group 1

    # Error checking
    # Both groups must be part of same hunt
    result = db.read_custom(f"SELECT hunt_id FROM groupings WHERE id = {group1_id} or id = {group2_id}")
    if len(result) != 2 or result[0][0] != result[1][0]:
        return jsonify({"error": "The groups you are trying to merge aren't part of the same hunt"})
    # Groups can only be merged in certain hunt statuses
    hunt_status = db.read_custom(f"SELECT status FROM hunts WHERE id = {result[0][0]}")[0][0]
    if hunt_status not in ('signup_open', 'signup_closed'):
        return jsonify({"error": f"Cannot merge groups in hunt {result[0][0]} because hunt status is {hunt_status}"})
    # Total number of hunters between groups must be <= 4
    slot_ids = []
    slot_types = []
    active_slots = []
    for idx, group_id in enumerate((group1_id, group2_id)):
        hunters = db.read_custom(f"SELECT slot1_id, slot2_id, slot3_id, slot4_id, slot1_type, slot2_type, slot3_type, slot4_type FROM groupings WHERE id = {group_id}")
        slot_ids.append(hunters[0][:4])
        slot_types.append(hunters[0][4:])
        active_slots.append([idx2 for idx2, value in enumerate(slot_types[idx]) if value != "open"])
    total_hunters = sum([len(slot) for slot in active_slots])
    if total_hunters > 4:
        return jsonify({"error": f"The groups you are trying to merge have too many hunters ({sum(total_hunters)})"})

    def diff(li1, li2):
        return list(set(li1) - set(li2)) + list(set(li2) - set(li1))

    # Now start the merge of higher group id into lower group id
    open_slots_1 = diff(range(4), active_slots[0])
    update_dict = {}
    slot_1_idx = 0
    for slot_2_idx in active_slots[1]:
        update_dict['slot' + str(open_slots_1[slot_1_idx]+1) + '_id'] = slot_ids[1][slot_2_idx]
        update_dict['slot' + str(open_slots_1[slot_1_idx]+1) + '_type'] = slot_types[1][slot_2_idx]
        slot_1_idx += 1

    db.update_row("groupings", group1_id, update_dict)

    # delete the second group
    db.del_row("groupings", group2_id)

    return jsonify({"message": f"Successfully merged groups {group1_id} and {group2_id} into group {group1_id}"})


@groupings_bp.route('/groupings/breakup/<group_id>', methods=['PUT'])
@token_required(manager_and_above)
def breakup_group(user, group_id):

    # Error checking
    # Groups can only be broken up in certain hunt statuses
    result = db.read_custom(f"SELECT h.status, h.id FROM hunts h INNER JOIN groupings g ON (g.hunt_id = h.id AND g.id = {group_id})")
    if len(result) > 0:
        hunt_status = result[0][0]
        hunt_id = result[0][1]
    else:
        return jsonify({"error": f"Could not find a hunt associated with group {group_id}"})
    if hunt_status not in ('signup_open', 'signup_closed'):
        return jsonify({"error": f"Cannot breakup group {group_id} in hunt {hunt_id} because hunt status is {hunt_status}"})

    # Extract group info
    result = db.read_custom(f"SELECT slot1_id, slot2_id, slot3_id, slot4_id, slot1_type, slot2_type, slot3_type, slot4_type FROM groupings WHERE id = {group_id}")[0]
    slot_ids = result[:4]
    slot_types = result[4:]
    active_slots = [idx for idx, value in enumerate(slot_types) if value != "open"]
    total_hunters = len(active_slots)

    if total_hunters <= 1:
        return jsonify({"message": "Nothing to break up"})

    # create a new group for each member, starting with the second
    update_dict = {}
    for i in active_slots[1:]:
        new_dict = {
            'hunt_id': hunt_id,
            'slot1_id': slot_ids[i],
            'slot1_type': slot_types[i]
        }
        db.add_row("groupings", new_dict)
        update_dict['slot' + str(i + 1) + '_id'] = None
        update_dict['slot' + str(i + 1) + '_type'] = "open"

    # clear out the slots where you just moved users to new group
    db.update_row("groupings", group_id, update_dict)

    return jsonify({"message": f"Successfully broke up group {group_id}"})


@groupings_bp.route('/groupings/remove/<group_id>/<slot>', methods=['PUT'])
@token_required(manager_and_above)
def remove_specific_slot(user, group_id, slot):

    slot_idx = int(slot) - 1

    # Error checking
    # Groups can only be modified in certain hunt statuses
    result = db.read_custom(f"SELECT h.status, h.id FROM hunts h INNER JOIN groupings g ON (g.hunt_id = h.id AND g.id = {group_id})")
    if len(result) > 0:
        hunt_status = result[0][0]
        hunt_id = result[0][1]
    else:
        return jsonify({"error": f"Could not find a hunt associated with group {group_id}"})
    if hunt_status not in ('signup_open', 'signup_closed'):
        return jsonify({"error": f"Cannot modify group {group_id} in hunt {hunt_id} because hunt status is {hunt_status}"})

    # Extract group info
    result = db.read_custom(f"SELECT slot1_id, slot2_id, slot3_id, slot4_id, slot1_type, slot2_type, slot3_type, slot4_type FROM groupings WHERE id = {group_id}")[0]
    slot_ids = result[:4]
    slot_types = result[4:]

    # Check to make sure there is a member in the slot that is to be vacated
    if slot_types[slot_idx] == "open":
        return jsonify({"error": f"Slot {slot} in group {group_id} is open, so there is no one to remove"})

    # create a new group for this user
    new_dict = {
        'hunt_id': hunt_id,
        'slot1_id': slot_ids[slot_idx],
        'slot1_type': slot_types[slot_idx]
    }
    db.add_row("groupings", new_dict)

    # clear out the slots where you just moved user to new group
    update_dict = {
        'slot' + slot + '_id': None,
        'slot' + slot + '_type': "open"
    }
    db.update_row("groupings", group_id, update_dict)

    return jsonify({"message": f"Successfully removed slot {slot} from group {group_id}"})


@groupings_bp.route('/groupings/leave/<group_id>', methods=['PUT'])
@token_required(all_members)
def leave_group(user, group_id):

    # Error checking
    # Groups can only be modified in certain hunt statuses
    result = db.read_custom(f"SELECT h.status, h.id FROM hunts h INNER JOIN groupings g ON (g.hunt_id = h.id AND g.id = {group_id})")
    if len(result) > 0:
        hunt_status = result[0][0]
        hunt_id = result[0][1]
    else:
        return jsonify({"error": f"Could not find a hunt associated with group {group_id}"})
    if hunt_status not in ('signup_open', 'signup_closed'):
        return jsonify({"error": f"Cannot leave group {group_id} in hunt {hunt_id} because hunt status is {hunt_status}"})
    # User must be in the group
    result = db.read_custom(f"SELECT slot1_id, slot2_id, slot3_id, slot4_id, slot1_type, slot2_type, slot3_type, slot4_type FROM groupings WHERE id = {group_id}")[0]
    slot_ids = result[:4]
    slot_types = result[4:]
    try:
        idx_match = slot_ids.index(user['id'])
    except ValueError as e:
        return jsonify({"error": f"User {user['id']} can't leave group {group_id} because they aren't part of that group"})

    # create a new group for this user
    new_dict = {
        'hunt_id': hunt_id,
        'slot1_id': user['id'],
        'slot1_type': "member"
    }
    db.add_row("groupings", new_dict)

    # clear out the slots where you just moved user to new group
    update_dict = {
        'slot' + str(idx_match + 1) + '_id': None,
        'slot' + str(idx_match + 1) + '_type': "open"
    }
    db.update_row("groupings", group_id, update_dict)

    return jsonify({"message": f"User {user['id']} successfully left group {group_id}"})
