from flask import Blueprint, request, jsonify
from .. import db
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above
import math

groupings_bp = Blueprint('groupings', __name__)
table_name = 'groupings'


def convert_time(time_of_day_sec):
    sec_in_min = 60
    sec_in_hr = sec_in_min * 60
    hours = math.floor(time_of_day_sec / sec_in_hr)
    minutes = math.floor((time_of_day_sec - hours*sec_in_hr) / sec_in_min)
    return f"{hours:02d}:{minutes:02d}"


@groupings_bp.route('/groupings', methods=['POST'])
@token_required(all_members)
def add_row(user):
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"message": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    mandatory_keys = ('hunt_id', 'slot1_id', 'slot1_type')
    for key in mandatory_keys:
        if key not in data_in:
            return jsonify({"message": f"Input json missing key '{key}' in " + base_identifier}), 400
    # groups can only be added to active hunts
    active = db.read_custom(f"SELECT id FROM hunts WHERE status = 'signup_open' OR status = 'signup_closed'")
    if active is None:
        return jsonify({"message": "Internal error"}), 400
    if active and data_in["hunt_id"] != active[0][0]:
        return jsonify({"message": f"Group cannot be added because hunt {data_in['hunt_id']} is not active"})
    # hunters must exist in users table and have active status to join a hunt
    num_hunters = 0
    for slot in range(1, 5):
        key = 'slot' + str(slot) + '_id'
        if key in data_in:
            num_hunters += 1
            temp = db.read_custom(f"SELECT status FROM users WHERE id = '{data_in[key]}'")
            if len(temp) == 0 or "inactive" in temp[0]:
                return jsonify({"message": f"Hunter {data_in[key]} does not have active status in the club"})
    # members can only create groupings for themselves
    if user['level'] == "member":
        user_id = db.read_custom(f"SELECT id FROM users WHERE public_id = '{user['public_id']}'")
        if data_in['slot1_id'] != user_id[0][0]:
            return jsonify({"message": f"Members can only start groups by themselves"})
    # check all group members to make sure they aren't already signed up in another group
    temp = db.read_custom(f"SELECT id, slot1_id, slot2_id, slot3_id, slot4_id FROM groupings WHERE hunt_id = '{data_in['hunt_id']}'")
    existing_group_id = [item[0] for item in temp]
    existing_slot_ids = [item[1:] for item in temp]
    for slot in range(1, 5):
        key = 'slot' + str(slot) + '_id'
        if key in data_in:
            duplicate = [idx for idx, item in enumerate(existing_slot_ids) if data_in[key] in item]
            if len(duplicate) > 0:
                return jsonify({"message": f"Hunter {data_in[key]} you are trying to add to slot {slot} is already in group {[existing_group_id[i] for i in duplicate]}"})

    # Input passes criteria - write to database
    data_in["num_hunters"] = num_hunters
    db.add_row(table_name, data_in)

    return jsonify({"message": "New group successfully added to hunt " + str(data_in['hunt_id'])}), 201


@groupings_bp.route('/groupings', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    results = db.read_all(table_name)
    # time has to be cleaned up before it can be jsonified
    for item in results:
        if item["harvest_update_time"] is not None:
            item["harvest_update_time"] = convert_time(item["harvest_update_time"].seconds)
        else:
            item["harvest_update_time"] = "00:00"
    return jsonify({"groupings": results}), 200


@groupings_bp.route('/groupings/harvest_summary', methods=['GET'])
@token_required(all_members)
def get_harvest_summary(user):

    # First figure out the id of the open hunt
    hunts = db.read_custom(f"SELECT id, hunt_date FROM hunts WHERE status = 'hunt_open'")
    if hunts is None:
        return jsonify({"message": "internal error"}), 500
    if len(hunts) == 0:
        return jsonify({"message": "Couldn't find an open hunt"}), 400
    hunt_id = hunts[0][0]
    hunt_date = hunts[0][1]

    data, group_id_of_current_user = harvest_summary_helper(hunt_id, user["id"])
    data["hunt_date"] = hunt_date

    # if calling user is part of current hunt, fetch their group's harvests
    if group_id_of_current_user is not None:
        data["this_user"] = get_harvest_detail_core(group_id_of_current_user)
        # add the list of all birds so they can add a new species to their harvest
        birds = db.read_custom(f"SELECT id, name FROM birds ORDER BY name")
        names = ["id", "name"]
        birds_dict = db.format_dict(names, birds)
        data["this_user"]["birds"] = birds_dict

    return jsonify({"data": data}), 200


@groupings_bp.route('/groupings/harvest_summary/<hunt_id>', methods=['GET'])
@token_required(all_members)
def get_harvest_summary_by_hunt_id(user, hunt_id):

    data, dummy = harvest_summary_helper(hunt_id, user["id"])

    return jsonify({"data": data}), 200


# this helper function could be called by multiple routes
def harvest_summary_helper(hunt_id, user_id):
    # harvest summary
    # regardless of whether they have any harvests yet, we always need to know the group, pond, & #hunters

    # now pull all groupings that match this hunt_id
    foo = db.read_custom(f"SELECT "
                         f"groupings.id, groupings.harvest_update_time, ponds.name FROM groupings "
                         f"JOIN ponds ON groupings.pond_id=ponds.id "
                         f"WHERE groupings.hunt_id={hunt_id} "
                         f"ORDER BY groupings.id")

    # now convert to list of dictionaries
    names = ["group_id", "harvest_update_time", "pond_name"]
    groups_dict = db.format_dict(names, foo)
    # time has to be cleaned up before it can be jsonified
    for item in groups_dict:
        if item["harvest_update_time"] is not None:
            item["harvest_update_time"] = convert_time(item["harvest_update_time"].seconds)
        else:
            item["harvest_update_time"] = "00:00"

    group_id_of_current_user = None
    for group in groups_dict:
        # count the number of hunters in this group
        results = db.read_custom(
            f"SELECT slot1_type, slot2_type, slot3_type, slot4_type, slot1_id, slot2_id, slot3_id, slot4_id "
            f"FROM groupings "
            f"WHERE id = {group['group_id']}")[0]
        slot_types = results[:4]
        slot_ids = results[4:]
        active_slots = []
        for idx, value in enumerate(slot_types):
            if value != "open":
                active_slots.append(idx)
            if value == "member" and slot_ids[idx] == user_id:
                group_id_of_current_user = group['group_id']
        group['num_hunters'] = len(active_slots)

        # count the number of ducks harvested
        harvest_ducks = db.read_custom(
            f"SELECT harvest.count FROM harvest JOIN birds ON harvest.bird_id=birds.id WHERE birds.type='duck' AND harvest.group_id={group['group_id']}")
        if harvest_ducks is None:
            return jsonify({"message": "unkown internal error"}), 500
        group["num_ducks"] = sum([elem[0] for elem in harvest_ducks])

        # count the number of non-ducks harvested
        harvest_nonducks = db.read_custom(
            f"SELECT harvest.count FROM harvest JOIN birds ON harvest.bird_id=birds.id WHERE birds.type!='duck' AND harvest.group_id={group['group_id']}")
        if harvest_nonducks is None:
            return jsonify({"message": "unkown internal error"}), 500
        group["num_nonducks"] = sum([elem[0] for elem in harvest_nonducks])

    data = {
        "groups": groups_dict
    }

    return data, group_id_of_current_user


@groupings_bp.route('/groupings/harvest_detail/<grouping_id>', methods=['GET'])
@token_required(all_members)
def get_harvest_detail(user, grouping_id):

    # the guts of this function are broken out so that it can be called from multiple routes
    data = get_harvest_detail_core(grouping_id)

    return jsonify({"data": data}), 200


def get_harvest_detail_core(grouping_id):
    # we need to know the names of the hunters in this group. start with the slot types
    foo = db.read_custom(f"SELECT "
                         f"slot1_type, slot2_type, slot3_type, slot4_type, "
                         f"slot1_id, slot2_id, slot3_id, slot4_id FROM groupings "
                         f"WHERE groupings.id={grouping_id}")[0]

    # for each slot type that is "member", pull the name
    foo_idx = [idx + 4 for idx, val in enumerate(foo[:4]) if val == "member"]
    if len(foo_idx) > 0:
        s = ""
        for idx in foo_idx:
            s += f" OR users.id={foo[idx]}"
        users = db.read_custom(f"SELECT first_name, last_name FROM users WHERE {s[4:]}")
        names = ["first_name", "last_name"]
        users_dict = db.format_dict(names, users)

    # get the pond name
    pond = db.read_custom(
        f"SELECT ponds.name FROM ponds JOIN groupings ON groupings.pond_id=ponds.id WHERE groupings.id={grouping_id}")
    if not pond or len(pond) == 0:
        return jsonify({"message": "Unknown internal error"}), 500

    # pull all harvests associated with this group
    foo = db.read_custom(f"SELECT birds.id, birds.name, harvest.count FROM birds "
                         f"JOIN harvest ON harvest.bird_id=birds.id "
                         f"WHERE harvest.group_id={grouping_id} "
                         f"ORDER BY birds.name")
    names = ["bird_id", "bird_name", "count"]
    harvest_dict = db.format_dict(names, foo)

    return {
        "hunters": users_dict,
        "pond": pond[0][0],
        "harvests": harvest_dict,
        "group_id": grouping_id
    }


@groupings_bp.route('/groupings/current', methods=['GET'])
@token_required(all_members)
def get_groups_in_current_hunt(user):

    # First figure out the id of the current hunt
    hunts = db.read_custom(f"SELECT id, hunt_date, status FROM hunts WHERE status = 'signup_open' OR status = 'signup_closed' OR status='draw_complete'")
    if hunts is None:
        return jsonify({"message": "internal error"}), 500
    if len(hunts) == 0:
        return jsonify({"message": "Couldn't find a hunt in a pre-hunt state"}), 400
    names = ["id", "hunt_date", "status"]
    hunts_dict = db.format_dict(names, hunts)[0]

    # now pull all groupings that match this hunt_id
    groupings = db.read_custom(f"SELECT * FROM groupings WHERE hunt_id = {hunts_dict['id']} ORDER BY id")
    groupings_dict = db.format_dict(None, groupings, table_name)
    # time has to be cleaned up before it can be jsonified
    for item in groupings_dict:
        if item["harvest_update_time"] is not None:
            item["harvest_update_time"] = convert_time(item["harvest_update_time"].seconds)
        else:
            item["harvest_update_time"] = "00:00"

    # now pull all hunter names & id
    users = db.read_custom(f"SELECT id, first_name, last_name, public_id FROM users")
    names = ["id", "first_name", "last_name", "public_id"]
    users_dict = db.format_dict(names, users)

    # now pull all open ponds
    ponds = db.read_custom(f"SELECT id, name FROM ponds WHERE status='open' ORDER BY name")
    names = ["id", "name"]
    ponds_dict = db.format_dict(names, ponds)

    # now see if the calling user is signed up for this hunt
    result = db.read_custom(f"SELECT id "
                            f"FROM groupings "
                            f"WHERE hunt_id={hunts_dict['id']} AND( "
                            f"groupings.slot1_type='member' AND groupings.slot1_id={user['id']} "
                            f"OR groupings.slot2_type='member' AND groupings.slot2_id={user['id']} "
                            f"OR groupings.slot3_type='member' AND groupings.slot3_id={user['id']} "
                            f"OR groupings.slot4_type='member' AND groupings.slot4_id={user['id']}) ")
    if result and len(result) > 0:
        callers_group_id = result[0][0]
    else:
        callers_group_id = -99

    # now put it all together
    results_dict = {
        "my_group_id": callers_group_id,
        "hunts": hunts_dict,
        "groupings": groupings_dict,
        "users": users_dict,
        "ponds": ponds_dict
    }

    return jsonify({"data": results_dict}), 200


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

    if 'pond_id' in data_in and data_in['pond_id'] is not None:

        # ponds can only be changed when the hunt state is signup_closed
        result = db.read_custom(f"SELECT hunts.status FROM hunts INNER JOIN groupings ON groupings.hunt_id=hunts.id WHERE groupings.id={grouping_id}")
        if not result[0][0] == 'signup_closed':
            return jsonify({'message': f"Cannot assign new pond {data_in['pond_id']} because hunt is not in the signup_closed state"}), 400

        # if a pond is being assigned to a group, check to see if it is already selected. If not, mark the pond as selected
        result = db.read_custom(f"SELECT status, selected FROM ponds WHERE id={data_in['pond_id']}")
        if result[0][0] == 'open' and result[0][1] == 0:
            # pond is open and available. now mark pond as selected
            db.update_custom(f"UPDATE ponds SET selected=1 WHERE id={data_in['pond_id']}")
        else:
            return jsonify({'message': f"Cannot assign pond {data_in['pond_id']} because it is not available"}), 400

        # if a pond is being changed, free up the previous pond for others
        result = db.read_custom(f"SELECT pond_id FROM groupings WHERE id={grouping_id}")
        pond_id_last = result[0][0]
        if pond_id_last is not None and pond_id_last != data_in['pond_id']:
            db.update_custom(f"UPDATE ponds SET selected=0 WHERE id={pond_id_last}")

    if db.update_row(table_name, grouping_id, data_in):

        # count the number of hunters
        results = db.read_custom(f"SELECT slot1_type, slot2_type, slot3_type, slot4_type FROM {table_name} WHERE id={grouping_id}")
        if results is not None and len(results) == 1:
            num_hunters = 0
            for slot in range(1, 5):
                key_id = 'slot' + str(slot) + '_id'
                # this slot is filled if there is input data for it or there is already someone in it
                if key_id in data_in or results[0][slot-1] != 'open':
                    num_hunters += 1
            data_in["num_hunters"] = num_hunters

            return jsonify({'message': f'Successful update of id {grouping_id} in {table_name}'}), 200
        else:
            return jsonify({"message": f"Unable to update id {grouping_id} of table {table_name}"}), 400
    else:
        return jsonify({"message": f"Unable to update id {grouping_id} of table {table_name}"}), 400


@groupings_bp.route('/groupings/<grouping_id>', methods=['DELETE'])
@token_required(admin_only)
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
        return jsonify({"message": "The groups you are trying to merge aren't part of the same hunt"})
    # Groups can only be merged in certain hunt statuses
    hunt_status = db.read_custom(f"SELECT status FROM hunts WHERE id = {result[0][0]}")[0][0]
    if hunt_status not in ('signup_open', 'signup_closed'):
        return jsonify({"message": f"Cannot merge groups in hunt {result[0][0]} because hunt status is {hunt_status}"})
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
        return jsonify({"message": f"The groups you are trying to merge have too many hunters ({total_hunters})"})

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

    # perform the update
    update_dict["num_hunters"] = total_hunters
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
    update_dict = {'num_hunters': total_hunters}
    for i in active_slots[1:]:
        new_dict = {
            'hunt_id': hunt_id,
            'slot1_id': slot_ids[i],
            'slot1_type': slot_types[i],
            'num_hunters': 1
        }
        db.add_row("groupings", new_dict)
        update_dict['slot' + str(i + 1) + '_id'] = None
        update_dict['slot' + str(i + 1) + '_type'] = "open"
        update_dict['num_hunters'] -= 1

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
    result = db.read_custom(
        f"SELECT h.status, h.id FROM hunts h INNER JOIN groupings g ON (g.hunt_id = h.id AND g.id = {group_id})")
    if len(result) > 0:
        hunt_status = result[0][0]
        hunt_id = result[0][1]
    else:
        return jsonify({"error": f"Could not find a hunt associated with group {group_id}"})
    if not hunt_status == 'signup_open':
        return jsonify(
            {"error": f"Cannot leave group {group_id} in hunt {hunt_id} because hunt status is {hunt_status}"})
    # User must be in the group
    result = db.read_custom(
        f"SELECT slot1_id, slot2_id, slot3_id, slot4_id, slot1_type, slot2_type, slot3_type, slot4_type FROM groupings WHERE id = {group_id}")[
        0]
    slot_ids = result[:4]
    slot_types = result[4:]
    total_hunters = sum(map(lambda x: x != "open", slot_types))
    if total_hunters == 1:
        return jsonify({"message": f"User {user['id']} can't leave group {group_id} because they are the only person in the group"}), 400

    try:
        idx_match = slot_ids.index(user['id'])
    except ValueError as e:
        return jsonify(
            {"error": f"User {user['id']} can't leave group {group_id} because they aren't part of that group"})

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


@groupings_bp.route('/groupings/withdraw/<group_id>', methods=['PUT'])
@token_required(all_members)
def withdraw(user, group_id):

    # this is nearly identical to leave_group except the user isn't put into their own new group

    # Error checking
    # Groups can only be modified in certain hunt statuses
    result = db.read_custom(f"SELECT h.status, h.id FROM hunts h INNER JOIN groupings g ON (g.hunt_id = h.id AND g.id = {group_id})")
    if len(result) > 0:
        hunt_status = result[0][0]
        hunt_id = result[0][1]
    else:
        return jsonify({"error": f"Could not find a hunt associated with group {group_id}"})
    if not hunt_status == 'signup_open':
        return jsonify({"error": f"Cannot leave group {group_id} in hunt {hunt_id} because hunt status is {hunt_status}"})
    # User must be in the group
    result = db.read_custom(f"SELECT slot1_id, slot2_id, slot3_id, slot4_id, slot1_type, slot2_type, slot3_type, slot4_type FROM groupings WHERE id = {group_id}")[0]
    slot_ids = result[:4]
    slot_types = result[4:]
    total_hunters = sum(map(lambda x: x != "open", slot_types))

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
    # db.add_row("groupings", new_dict)
    # commenting out this line is the only difference between this and leave_group

    if total_hunters > 1:
        # clear out the slots where you just moved user to new group
        update_dict = {
            'slot' + str(idx_match + 1) + '_id': None,
            'slot' + str(idx_match + 1) + '_type': "open"
        }
        db.update_row("groupings", group_id, update_dict)
    else:
        # this was the only user in the group, so delete the whole group
        db.del_row(table_name, group_id)

    return jsonify({"message": f"User {user['id']} successfully left group {group_id}"})
