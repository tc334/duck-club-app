from flask import Blueprint, request, jsonify
import datetime
from copy import deepcopy
from .. import db, cache
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above
from .users import get_id_from_public_id
from .hunts import get_current_prehunt
from .stats import update_group_harvest

groupings_bp = Blueprint('groupings', __name__)
table_name = 'groupings'


@groupings_bp.route('/groupings', methods=['POST'])
@token_required(all_members)
def add_row(user):
    # this function will add one group and one participant to the current hunt
    print(f"BEFORE GROUP ACTION 'add_row'")

    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"message": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    mandatory_keys = ('public_id', )
    for key in mandatory_keys:
        if key not in data_in:
            return jsonify({"message": f"Input json missing key '{key}' in " + base_identifier}), 400
    user_id = get_id_from_public_id(data_in['public_id'])
    # groups can only be added to active hunt
    results = db.read_custom(f"SELECT id FROM hunts WHERE status = 'signup_open' OR status = 'signup_closed'")
    if results is None or results is False or len(results) > 1:
        return jsonify({"message": "Could not find hunt in proper status to add a group"}), 500
    hunt_id = results[0][0]
    # hunters must exist in users table and have active status to join a hunt
    results = db.read_custom(f"SELECT status FROM users WHERE public_id = '{data_in['public_id']}'")
    if results is None or results is False or len(results) != 1 or results[0][0] != "active":
        return jsonify({"message": f"Hunter {data_in['user_id']} does not have active status in the club"})
    # members can only create groupings for themselves
    if user['level'] == "member":
        if data_in['public_id'] != user['public_id']:
            return jsonify({"message": f"Members can only start groups for themselves"})
    # check to make sure new hunter isn't already signed up in another group
    results = db.read_custom(
        f"SELECT groupings.id FROM groupings "
        f"JOIN participants ON participants.grouping_id=groupings.id "
        f"WHERE participants.user_id={user_id} "
        f"AND groupings.hunt_id='{hunt_id}'"
    )
    if results is None:
        return jsonify({"message": "internal error"}), 500
    if len(results) > 0:
        # this means we found the user already signed up for this hunt
        return jsonify({"message": f"User {user_id} is already signed up for hunt {hunt_id} in group {results[0][0]}"}), 400

    # Input passes criteria - write to database
    # 1) create new grouping
    db_row = {
        "hunt_id": hunt_id,
    }
    group_id = db.add_row(table_name, db_row)
    # 2) create new participant associated with above group
    db_row = {
        "type": "member",
        "grouping_id": group_id,
        "user_id": user_id
    }
    if 'b_dog' in data_in:
        db_row['b_dog'] = True if data_in['b_dog'] == 'on' else False
    if 'num_atv_seats' in data_in:
        db_row['num_atv_seats'] = int(data_in['num_atv_seats'])
    if 'pond_preference' in data_in and len(data_in['pond_preference']) > 0:
        db_row['pond_preference'] = data_in['pond_preference']
    if 'notes' in data_in and len(data_in['notes']) > 0:
        db_row['notes'] = data_in['notes']
    participant_id = db.add_row("participants", db_row)
    cache.delete("bravo")
    cache.delete(f"golf:{'hunt_id'}")

    print(f"AFTER GROUP ACTION 'add_row'")
    print_group(group_id)

    return jsonify({"message": "New group successfully added to hunt " + str(hunt_id)}), 201


@groupings_bp.route('/groupings', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    results = db.read_all(table_name)
    # time has to be cleaned up before it can be jsonified
    for item in results:
        if item["harvest_update_time"] is not None:
            item["harvest_update_time"] = item["harvest_update_time"].isoformat(timespec='minutes')
        else:
            item["harvest_update_time"] = "00:00"
    return jsonify({"groupings": results}), 200


@groupings_bp.route('/groupings/harvest_summary', methods=['GET'])
@token_required(all_members)
def get_harvest_summary(user):

    # First figure out the id of the current hunt
    hunts_dict = cache.get("echo")
    if len(hunts_dict) < 1:
        # no stored value in cache, must go to db
        hunts = db.read_custom(f"SELECT id, hunt_date FROM hunts WHERE status = 'hunt_open'")
        if hunts is None or not hunts:
            return jsonify({"message": "internal error"}), 500
        if len(hunts) == 0:
            return jsonify({"message": "Couldn't find a hunt in a hunt-open state"}), 400
        names = ["id", "hunt_date"]
        hunts_dict = db.format_dict(names, hunts)[0]
        # datetime requires special handling
        hunts_dict["hunt_date"] = hunts_dict["hunt_date"].isoformat()
        # push response to cache
        cache.add("echo", hunts_dict, 60 * 60)

    data, group_id_of_current_user = harvest_summary_helper(hunts_dict["id"], user["id"])
    data["hunt_date"] = hunts_dict["hunt_date"]

    # if calling user is part of current hunt, fetch their group's harvests
    if group_id_of_current_user is not None:
        data["this_user"] = get_harvest_detail_core(group_id_of_current_user)
        # add the list of all birds so they can add a new species to their harvest
        birds_dict = cache.get("foxtrot")
        if len(birds_dict) < 1:
            # no stored value in cache, must go to db
            birds = db.read_custom(f"SELECT id, name FROM birds ORDER BY name")
            names = ["id", "name"]
            birds_dict = db.format_dict(names, birds)
            # push response to cache
            cache.add("foxtrot", birds_dict, 24*60*60)
        data["this_user"]["birds"] = birds_dict

    return jsonify({"data": data}), 200


@groupings_bp.route('/groupings/harvest_summary/<hunt_id>', methods=['GET'])
@token_required(all_members)
def get_harvest_summary_by_hunt_id(user, hunt_id):

    data, dummy = harvest_summary_helper(hunt_id, user["id"])

    return jsonify({"data": data}), 200


def harvest_summary_helper(hunt_id, user_id):

    # this call updates any groups that have changed data since last update
    update_group_harvest()

    # pull all groupings that match this hunt_id
    groups_dict = cache.get(f"golf:{hunt_id}")
    if len(groups_dict) < 1:
        # no cache hit, go to db
        foo = db.read_custom(f"SELECT "
                             f"groupings.id, "
                             f"groupings.harvest_update_time, "
                             f"groupings.num_ducks, "
                             f"groupings.num_non, "
                             f"COUNT(participants), "
                             f"ponds.name "
                             f"FROM groupings "
                             f"JOIN participants ON participants.grouping_id=groupings.id "
                             f"JOIN ponds ON groupings.pond_id=ponds.id "
                             f"WHERE groupings.hunt_id={hunt_id} "
                             f"GROUP BY groupings.id, ponds.name "
                             f"ORDER BY groupings.harvest_update_time")
        # now convert to list of dictionaries
        names = ["group_id", "harvest_update_time", "num_ducks", "num_nonducks", "num_hunters", "pond_name"]
        groups_dict = db.format_dict(names, foo)
        # time has to be cleaned up before it can be jsonified
        for item in groups_dict:
            if item["harvest_update_time"] is not None:
                item["harvest_update_time"] = item["harvest_update_time"].isoformat(timespec='minutes')
            else:
                item["harvest_update_time"] = "00:00"
        # update cache
        cache.add(f"golf:{hunt_id}", groups_dict, 24*60*60)

    group_id_of_current_user = get_group_id_from_user_id(user_id, hunt_id)

    data = {
        "groups": groups_dict
    }

    return data, group_id_of_current_user


@groupings_bp.route('/groupings/harvest_detail/<grouping_id>', methods=['GET'])
@token_required(all_members)
def get_harvest_detail(user, grouping_id):

    # the guts of this function are broken out so that it can be called from multiple routes
    data = get_harvest_detail_core(grouping_id)
    if not data:
        return jsonify({"message": "error in get_harvest_detail_core"}), 500

    return jsonify({"data": data}), 200


def get_harvest_detail_core(grouping_id):

    users_dict = cache.get(f"kilo:{grouping_id}")
    if len(users_dict) < 1:
        # cache miss, go to db
        members = db.read_custom(
            f"SELECT CONCAT(users.first_name, ' ', users.last_name) FROM users "
            f"JOIN participants ON participants.user_id=users.id "
            f"WHERE participants.grouping_id={grouping_id}"
        )
        if members is not None:
            users_dict = {"members": [row[0] for row in members]}
        else:
            users_dict = {"members": None}

        guests = db.read_custom(
            f"SELECT guests.full_name FROM guests "
            f"JOIN participants ON participants.guest_id=guests.id "
            f"WHERE participants.grouping_id={grouping_id}"
        )
        if guests is not None:
            users_dict["guests"] = [row[0] for row in guests]
        else:
            users_dict["guests"] = None

        # update cache
        cache.add(f"kilo:{grouping_id}", users_dict, 60*60)

    # get the pond name
    pond_name = cache.get(f"lima:{grouping_id}")
    if len(pond_name) < 1:
        # cache miss, go to db
        results = db.read_custom(
            f"SELECT ponds.name "
            f"FROM ponds "
            f"JOIN groupings ON groupings.pond_id=ponds.id "
            f"WHERE groupings.id={grouping_id}")
        if not results or len(results) == 0:
            return False
        else:
            pond_name = results[0][0]
        # update cache
        cache.add(f"lima:{grouping_id}", [pond_name], 60*60)
    else:
        pond_name = pond_name[0]  # strip off the list; length should always be 1

    # pull all harvests associated with this group
    harvest_dict = cache.get(f"mike:{grouping_id}")
    if len(harvest_dict) < 1:
        # cache miss, go to db
        foo = db.read_custom(f"SELECT birds.id, birds.name, harvest.count FROM birds "
                             f"JOIN harvest ON harvest.bird_id=birds.id "
                             f"WHERE harvest.group_id={grouping_id} "
                             f"ORDER BY birds.name")
        names = ["bird_id", "bird_name", "count"]
        harvest_dict = db.format_dict(names, foo)
        # update cache
        cache.add(f"mike:{grouping_id}", harvest_dict, 60*60)

    return {
        "hunters": users_dict,
        "pond": pond_name,
        "harvests": harvest_dict,
        "group_id": grouping_id
    }


@groupings_bp.route('/groupings/current', methods=['GET'])
@token_required(all_members)
def get_groups_in_current_hunt(user):

    # First figure out the id of the current hunt
    hunt_dict = get_current_prehunt()
    if hunt_dict is None:
        return jsonify({"message": "No hunt in prehunt state"}), 400

    # now pull all groupings that match this hunt_id
    groupings_dict = get_all_groupings_from_hunt(hunt_dict['id'])

    # now pull all open ponds
    ponds_dict = cache.get("delta")
    if len(ponds_dict) < 1:
        # no stored value in cache, must go to db
        ponds = db.read_custom(f"SELECT id, name FROM ponds WHERE status='open' ORDER BY name")
        names = ["id", "name"]
        ponds_dict = db.format_dict(names, ponds)
        # push response to cache
        cache.add("delta", ponds_dict, 30*60)

    # now see if the calling user is signed up for this hunt
    callers_group_id = get_group_id_from_user_id(user['id'], hunt_dict['id'])
    if callers_group_id is None:
        callers_group_id = -99

    # now put it all together
    results_dict = {
        "my_group_id": callers_group_id,
        "hunt": hunt_dict,
        "groupings": groupings_dict,
        "ponds": ponds_dict
    }

    return jsonify({"data": results_dict}), 200


@groupings_bp.route('/groupings/current_users', methods=['GET'])
@token_required(all_members)
def get_users_in_current_hunt(user):

    # First figure out the id of the current hunt
    hunt_dict = get_current_prehunt()
    if hunt_dict is None:
        return jsonify({"message": "No hunt in prehunt state"}), 400

    # now pull all users in this hunt
    users_dict = get_users_in_hunt_aux(hunt_dict['id'])
    if users_dict is None:
        return jsonify({"message": "internal error in get_users_in_current_hunt"}), 500

    results_dict = {
        "hunt_id": hunt_dict['id'],
        "users": users_dict
    }

    return jsonify({"data": results_dict}), 200


def get_users_in_hunt_aux(hunt_id):
    results = db.read_custom(
        f"SELECT u.public_id, CONCAT(u.first_name, ' ', u.last_name) as name FROM users u "
        f"JOIN participants p ON p.user_id=u.id "
        f"JOIN groupings g ON p.grouping_id=g.id "
        f"WHERE g.hunt_id={hunt_id} "
        f"ORDER BY name"
    )
    if results is None or results is False:
        print(f"Internal error in get_users_in_hunt_aux")
        return None
    names = ["id", "name"]
    return db.format_dict(names, results)


@groupings_bp.route('/groupings/<grouping_id>', methods=['GET'])
@token_required(all_members)
def get_one_row(users, grouping_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE id={grouping_id}")

    if result and len(result) == 1:
        results_dict = db.format_dict(None, result, table_name=table_name)
        return jsonify({"grouping": results_dict}), 200
    else:
        return jsonify({"error": f"Could not find id {grouping_id} in table {table_name}"}), 400


@groupings_bp.route('/groupings/<grouping_id>', methods=['PUT'])
@token_required(manager_and_above)
def update_row(user, grouping_id):
    print(f"BEFORE GROUP ACTION 'update_row'. grouping_id={grouping_id}")
    print_group(grouping_id)

    data_in = request.get_json()

    hunt_dict = get_hunt_dict(grouping_id)
    if not hunt_dict:
        return jsonify({"message": "Internal error, invalid read of hunt dictionary"}), 500

    if 'pond_id' in data_in and data_in['pond_id'] is not None:

        # ponds can only be changed when the hunt state is signup_closed (unless you are an admin)
        if hunt_dict["status"] != 'signup_closed' and user["level"] != "administrator":
            return jsonify({'message': f"Cannot assign new pond {data_in['pond_id']} because hunt is not in the signup_closed state"}), 400

        # if a pond is being assigned to a group, check to see if it is already selected. If not, mark the pond as
        # selected
        result = db.read_custom(
            f"SELECT status, selected "
            f"FROM ponds "
            f"WHERE id={data_in['pond_id']}")
        names = ["status", "selected"]
        ponds_dict = db.format_dict(names, result)[0]
        if ponds_dict["status"] == 'open' and ponds_dict["selected"] == 0:
            # pond is open and available. now mark pond as selected
            db.update_custom(f"UPDATE ponds SET selected=TRUE WHERE id={data_in['pond_id']}")
            # invalidate cache
            cache.delete(f"lima:{grouping_id}")  # cached value is now stale
        else:
            return jsonify({'message': f"Cannot assign pond {data_in['pond_id']} because it is not available"}), 400

        # if a pond is being changed, free up the previous pond for others
        result = db.read_custom(f"SELECT pond_id FROM groupings WHERE id={grouping_id}")
        pond_id_last = result[0][0]
        if pond_id_last is not None and pond_id_last != data_in['pond_id']:
            db.update_custom(f"UPDATE ponds SET selected=FALSE WHERE id={pond_id_last}")

    if db.update_row(table_name, grouping_id, data_in):
        cache.delete("bravo")
        cache.delete(f"golf:{hunt_dict['id']}")
        cache.delete(f"hotel:{grouping_id}")
        cache.delete(f"kilo:{grouping_id}")
        cache.delete(f"romeo:{grouping_id}")

        print(f"AFTER GROUP ACTION 'update_row'. grouping_id={grouping_id}")
        print_group(grouping_id)

        return jsonify({'message': f'Successful update of id {grouping_id} in {table_name}'}), 200
    else:
        return jsonify({"message": f"Unable to update id {grouping_id} of table {table_name}"}), 400


@groupings_bp.route('/groupings/<grouping_id>', methods=['DELETE'])
@token_required(admin_only)
def del_row(user, grouping_id):
    result = db.read_custom(f"DELETE FROM {table_name} WHERE id={grouping_id} RETURNING hunt_id")
    if result and len(result) == 1:
        hunt_id = result[0][0]
        cache.delete("bravo")
        cache.delete(f"golf:{hunt_id}")
        cache.delete(f"hotel:{grouping_id}")
        cache.delete(f"kilo:{grouping_id}")
        cache.delete(f"lima:{grouping_id}")
        cache.delete(f"romeo:{grouping_id}")
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {grouping_id} from table {table_name}"}), 400


@groupings_bp.route('/groupings/merge/<group1_id>/<group2_id>', methods=['PUT'])
@token_required(manager_and_above)
def merge_groups(user, group1_id, group2_id):
    print(f"BEFORE GROUP ACTION 'merge_groups'. group1_id={group1_id}. group2_id={group2_id}")
    print_group(group1_id)
    print_group(group2_id)

    # hunters from group 2 will be placed into group 1

    # Error checking
    # Both groups must be part of same hunt
    hunt_dict1 = get_hunt_dict(group1_id)
    if not hunt_dict1:
        return jsonify({"message": "Internal error, invalid read of hunt dictionary"}), 500
    hunt_dict2 = get_hunt_dict(group2_id)
    if not hunt_dict2:
        return jsonify({"message": "Internal error, invalid read of hunt dictionary"}), 500
    if hunt_dict1["id"] != hunt_dict2["id"]:
        return jsonify({"message": "The groups you are trying to merge aren't part of the same hunt"})
    # Groups can only be merged in certain hunt statuses
    if hunt_dict1["status"] not in ('signup_open', 'signup_closed'):
        return jsonify({"message": f"Cannot merge groups in hunt {hunt_dict1['id']} because hunt status is {hunt_dict1['status']}"})
    # Total number of hunters between groups must be <= 4
    num_hunters_1 = db.read_custom(f"SELECT COUNT(*) FROM participants p WHERE p.grouping_id={group1_id}")[0][0]
    num_hunters_2 = db.read_custom(f"SELECT COUNT(*) FROM participants p WHERE p.grouping_id={group2_id}")[0][0]
    num_hunters_tot = num_hunters_1 + num_hunters_2
    if num_hunters_tot > 4:
        return jsonify({"message": f"Merging groups {group1_id} and {group2_id} would result in "
                                   f"{num_hunters_tot} hunters, which is more than the max of 4"}), 400

    # perform the update
    db.update_custom(f"UPDATE participants SET grouping_id={group1_id} WHERE grouping_id={group2_id}")

    # delete the second group
    db.del_row("groupings", group2_id)

    cache.delete("bravo")
    cache.delete(f"golf:{hunt_dict1['id']}")
    cache.delete(f"golf:{hunt_dict2['id']}")
    cache.delete(f"hotel:{group1_id}")
    cache.delete(f"hotel:{group2_id}")
    cache.delete(f"kilo:{group1_id}")
    cache.delete(f"kilo:{group2_id}")
    cache.delete(f"romeo:{group1_id}")
    cache.delete(f"romeo:{group2_id}")

    print(f"AFTER GROUP ACTION 'merge_groups'. group1_id={group1_id}. group2_id={group2_id}")
    print_group(group1_id)
    print_group(group2_id)

    return jsonify({"message": f"Successfully merged groups {group1_id} and {group2_id} into group {group1_id}"})


@groupings_bp.route('/groupings/breakup/<group_id>', methods=['PUT'])
@token_required(manager_and_above)
def breakup_group(user, group_id):
    print(f"BEFORE GROUP ACTION 'breakup_group'. group_id={group_id}")
    print_group(group_id)

    # Error checking
    # Groups can only be broken up in certain hunt statuses
    hunt_dict = get_hunt_dict(group_id)
    if not hunt_dict:
        return jsonify({"message": "Internal error in breakup_group(), invalid read of hunt dictionary"}), 500
    if hunt_dict["status"] not in ('signup_open', 'signup_closed'):
        return jsonify({"error": f"Cannot breakup group {group_id} in hunt {hunt_dict['id']} because hunt status is {hunt_dict['status']}"})

    # get all participants in this group
    results = db.read_custom(
        f"SELECT participants.id, participants.type, participants.user_id, users.id "
        f"FROM participants "
        f"LEFT JOIN guests ON participants.guest_id=guests.id "
        f"LEFT JOIN users ON guests.user_id=users.id "
        f"WHERE participants.grouping_id={group_id} "
        f"ORDER BY participants.type ASC"
    )
    if results is None:
        return jsonify({"message": "Internal error"}), 500
    if len(results) == 0:
        return jsonify({"message": f"Group {group_id} appears to have no participants"}), 400
    names = ["id", "type", "user_id", "host_id"]
    participants_dict = db.format_dict(names, results)

    left = False  # have we left the first member and their guests in this group?
    new_ids = []
    while len(participants_dict) > 0:
        # double-check that we get members first
        if participants_dict[0]["type"] != "member":
            raise Exception("didn't find member in grouping")
        # indices of guests associated with this member
        idx_guests = [idx for idx, participant in enumerate(participants_dict) if participant["host_id"]==participants_dict[0]["user_id"]]
        p_idxs_to_move = [0] + idx_guests
        if not left:
            left = True
        else:
            # member, and all guests move to new grouping
            # 1) create new grouping
            db_row = {
                "hunt_id": hunt_dict['id'],
            }
            group_id_new = db.add_row(table_name, db_row)
            new_ids.append(group_id_new)
            # 2) update participant foreign keys
            for i_p in p_idxs_to_move:
                db.update_row("participants", participants_dict[i_p]["id"], {"grouping_id": group_id_new})
        p_idxs_to_move.sort(reverse=True)
        [participants_dict.pop(i) for i in p_idxs_to_move]

    cache.delete("bravo")
    cache.delete(f"golf:{hunt_dict['id']}")
    cache.delete(f"hotel:{group_id}")
    cache.delete(f"kilo:{group_id}")
    cache.delete(f"romeo:{group_id}")

    print(f"AFTER GROUP ACTION 'breakup_group'. group_id={group_id}")
    print_group(group_id)
    for id in new_ids:
        print_group(id)

    return jsonify({"message": f"Successfully broke up group {group_id}"})


def remove_hunter(user_id, hunt_id):
    # this will remove a member and all of their guests regardless of hunt status. Any restrictions on who can do this
    # when should have been applied prior to calling this function

    # 0) get group id
    results = db.read_custom(
        f"SELECT groupings.id FROM groupings "
        f"JOIN participants ON participants.grouping_id=groupings.id "
        f"WHERE participants.user_id={user_id} "
        f"AND groupings.hunt_id={hunt_id}"
    )
    if results is None:
        print("internal error in remove_hunter")
        return None
    if len(results) != 1:
        print("Error: could not remove hunter because they were found in more or less than 1 group")
        return None
    group_id = results[0][0]

    print_group(group_id)  # debug print

    # 1) remove this member from the hunt by deleting participant entry
    db.update_custom(
        f"DELETE FROM participants "
        f"WHERE grouping_id={group_id} "
        f"AND user_id={user_id}"
    )

    # 2) remove all guests of this member
    db.update_custom(
        f"DELETE FROM participants "
        f"WHERE grouping_id={group_id} "
        f"AND guest_id IN (SELECT id from guests WHERE user_id={user_id})"
    )

    # 3) if that group no longer has any hunters, delete it too
    num_hunters = db.read_custom(f"SELECT COUNT(*) FROM participants WHERE grouping_id={group_id}")[0][0]
    if num_hunters == 0:
        db.update_custom(f"DELETE FROM groupings WHERE id={group_id}")

    # 4) Clear out cache that might have been invalidated
    cache.delete(f"golf:{hunt_id}")
    cache.delete("bravo")
    cache.delete(f"hotel:{group_id}")
    cache.delete(f"kilo:{group_id}")
    cache.delete(f"romeo:{group_id}")

    print(f"AFTER GROUP ACTION 'remove hunter'. group_id={group_id}")
    print_group(group_id)  # debug print

    return True


@groupings_bp.route('/groupings/withdraw', methods=['PUT'])
@token_required(all_members)
def withdraw(user):
    print(f"BEFORE GROUP ACTION 'withdraw'")

    # members can withdraw themselves when hunt status is signup_open
    hunt_dict = get_current_prehunt()
    if hunt_dict and hunt_dict['status'] == "signup_open":
        if remove_hunter(user['id'], hunt_dict['id']) is not None:
            return jsonify({"message": f"User {user['id']} successfully left withdrew from hunt"})
        else:
            return jsonify({"message": "internal error in withdraw"}), 500
    else:
        return jsonify({"message": f"Cannot withdraw from hunt because hunt status is not signup_open"})


@groupings_bp.route('/groupings/drop/<public_id>/<hunt_id>', methods=['PUT'])
@token_required(manager_and_above)
def drop(user, public_id, hunt_id):
    print(f"BEFORE GROUP ACTION 'drop'")

    # get hunt status
    results = db.read_custom(
        f"SELECT status FROM hunts WHERE id={hunt_id}"
    )
    if results is None or len(results) != 1:
        return jsonify({"message": "bad hunt_id"}), 400
    hunt_status = results[0][0]

    # managers can drop hunters unless hunt status is closed
    if user['level'] != "administrator" and hunt_status == "hunt_closed":
        return jsonify({"message": "Only administrators can drop users after a hunt is closed."})

    user_id = get_id_from_public_id(public_id)

    if remove_hunter(user_id, hunt_id) is not None:
        return jsonify({"message": f"User {user_id} successfully removed from hunt"})
    else:
        return jsonify({"message": "internal error in remove hunter via drop"}), 500


def get_hunt_dict(grouping_id):
    hunt_dict = cache.get(f"nov:{grouping_id}")
    if not hunt_dict:
        # cache miss, go to db
        result = db.read_custom(
            f"SELECT h.id, h.status, h.hunt_date "
            f"FROM hunts h "
            f"INNER JOIN groupings g ON g.hunt_id=h.id "
            f"WHERE g.id={grouping_id}")
        if result is None or len(result) != 1:
            return False
        names = ["id", "status", "hunt_date"]
        hunt_dict = db.format_dict(names, result)[0]
        # cache update
        cache.add(f"nov:{grouping_id}", hunt_dict, 10 * 60)
    else:
        # cache hit, need to fix datetime fields
        hunt_dict["hunt_date"] = datetime.datetime.strptime(hunt_dict["hunt_date"], '%Y-%m-%d').date()

    return hunt_dict


@groupings_bp.route('/groupings/editable', methods=['GET'])
@token_required(all_members)
def get_editable_hunts(user):
    # return the dates and group ids for hunts that the user can still edit harvests for
    results = db.read_custom(
        f"SELECT groupings.id, hunts.hunt_date FROM groupings "
        f"JOIN hunts ON groupings.hunt_id=hunts.id "
        f"JOIN participants ON participants.grouping_id=groupings.id "
        f"WHERE hunts.status='hunt_closed' "
        f"AND current_date()-hunts.hunt_date <= 1 "
        f"AND participants.user_id={user['id']} "
        f"ORDER BY hunts.hunt_date"
    )
    if results:
        names = ["group_id", "hunt_date"]
        results_dict = db.format_dict(names, results)
        return jsonify({"message": results_dict}), 200
    else:
        return jsonify({"message": "You don't have any hunts that can be edited right now"}), 500


@groupings_bp.route('/groupings/filtered', methods=['GET'])
@token_required(manager_and_above)
def get_groups_filtered(user):
    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    # check for mandatory filter
    if "hunt_id" not in data_in:
        return jsonify({"message": "Missing hunt ID in filtered groupings query"}), 400

    groupings_dict = get_all_groupings_from_hunt(data_in['hunt_id'])

    return jsonify({"groupings": groupings_dict}), 200


def print_group(id_group):

    num_hunters = db.read_custom(
        f"SELECT COUNT(*) FROM participants WHERE grouping_id={id_group}"
    )

    members = db.read_custom(
        f"SELECT participants.type, CONCAT(users.first_name, ' ', users.last_name) "
        f"FROM users "
        f"JOIN participants ON users.id=participants.user_id "
        f"WHERE participants.grouping_id='{id_group}'"
    )

    guests = db.read_custom(
        f"SELECT participants.type, guests.full_name "
        f"FROM guests "
        f"JOIN participants ON guests.id=participants.guest_id "
        f"WHERE participants.grouping_id='{id_group}'"
    )

    print("****************************************")
    print(f"     Group {id_group}")
    print("------------------------------------")
    if num_hunters:
        print(f"| Slot |  Type  |  Participant         |")
        print("|------|--------|------------------|")
        slot = 0
        if members:
            for row in members:
                slot += 1
                print(f"|    {slot} | {row[0]:6s} | {row[1]}")
        print("------------------------------------")
        if guests:
            for row in guests:
                slot += 1
                print(f"|    {slot} | {row[0]:6s} | {row[1]}")
        print("------------------------------------")
        print(f"# hunters: {num_hunters[0][0]}")

    else:
        print(f"Group doesn't exist")
    print("****************************************")


def get_group_id_from_user_id(user_id, hunt_id):
    results = db.read_custom(
        f"SELECT groupings.id FROM groupings "
        f"JOIN participants ON participants.grouping_id=groupings.id "
        f"WHERE participants.user_id={user_id} "
        f"AND groupings.hunt_id={hunt_id}"
    )

    # Error cases
    if results is None or len(results) == 0:
        return None
    if len(results) > 1:
        raise Exception('Found multiple matching groups when there should only ever be one')

    return results[0][0]


def get_all_groupings_from_hunt(hunt_id):

    groupings_dict = cache.get(f"bravo:{hunt_id}")
    if len(groupings_dict) < 1:
        # no stored value in cache, must go to db
        results = db.read_custom(
            f"SELECT g.id, g.pond_id, g.draw_chip_raw, "
            f"ARRAY_AGG(u.first_name || ' ' || u.last_name) FILTER(WHERE u.first_name IS NOT NULL), "
            f"ARRAY_AGG(participants.b_dog) FILTER(WHERE u.first_name IS NOT NULL), "
            f"ARRAY_AGG(participants.num_atv_seats) FILTER(WHERE u.first_name IS NOT NULL), "
            f"ARRAY_AGG(participants.pond_preference) FILTER(WHERE u.first_name IS NOT NULL), "
            f"ARRAY_AGG(participants.notes) FILTER(WHERE u.first_name IS NOT NULL), "
            f"ARRAY_AGG(CONCAT('(G) ', guests.full_name))  FILTER(WHERE guests.full_name IS NOT NULL), "
            f"COUNT(*) "
            f"FROM groupings g "
            f"JOIN participants ON participants.grouping_id=g.id "
            f"LEFT JOIN users u ON participants.user_id=u.id "
            f"LEFT JOIN guests ON participants.guest_id=guests.id "
            f"WHERE g.hunt_id={hunt_id} "
            f"GROUP BY g.id"
        )
        if results is None or results is False:
            return None
        names = ["id", "pond_id", "chip", "members", "dogs", "atv", "pond_pref", "notes", "guests", "count"]
        groupings_dict = db.format_dict(names, results)
        # order results
        groupings_dict = order_groups(groupings_dict)
        # push response to cache
        cache.add(f"bravo:{hunt_id}", groupings_dict, 5*60)

    return groupings_dict


def order_groups(groupings_LOD):
    idx_out = []
    # no chip, no pond
    def condition1(x): return x["chip"] is None and x["pond_id"] is None
    idx_1 = [idx for idx, element in enumerate(groupings_LOD) if condition1(element)]
    print(f"Alpha:{idx_1}")
    if len(idx_1) > 0:
        sort_seq = [groupings_LOD[i]["count"] for i in idx_1]
        print(f"Bravo:{sort_seq}")
        sort_idx = h(sort_seq)
        print(f"Charlie:{sort_idx}")
        idx_out += [idx_1[i] for i in sort_idx]
        print(f"Delta:{idx_out}")

    # yes chip, no pond
    def condition2(x): return x["chip"] is not None and x["pond_id"] is None
    idx_2 = [idx for idx, element in enumerate(groupings_LOD) if condition2(element)]
    if len(idx_2) > 0:
        sort_seq = [groupings_LOD[i]["chip"] for i in idx_2]
        sort_idx = h(sort_seq)
        idx_out += [idx_2[i] for i in sort_idx]

    # yes pond
    def condition3(x): return x["pond_id"] is not None
    idx_3 = [idx for idx, element in enumerate(groupings_LOD) if condition3(element)]
    if len(idx_3) > 0:
        sort_seq = [groupings_LOD[i]["chip"] for i in idx_3]
        sort_idx = h(sort_seq)
        idx_out += [idx_3[i] for i in sort_idx]

    if len(idx_out) != len(groupings_LOD):
        raise Exception("these should have matched")

    return [groupings_LOD[i] for i in idx_out]


def h(seq):
    #http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    #by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)
