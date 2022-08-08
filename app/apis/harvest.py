from flask import Blueprint, request, jsonify
from datetime import datetime
import pytz
from .. import db, cache
from .groupings import get_hunt_dict
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above

harvests_bp = Blueprint('harvests', __name__)
table_name = 'harvest'


def central_time_now():
    IST = pytz.timezone('US/Central')
    datetime_ist = datetime.now(IST)
    result = datetime_ist.strftime('%H:%M')
    return result


@harvests_bp.route('/harvests', methods=['POST', 'PUT'])
@token_required(all_members)
def update_harvest(user):
    # data_in["count"] and ["bird_id"] can be arrays. They have to be the same length
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + update_harvest.__name__
    if data_in is None:
        return jsonify({"message": "Input json is empty in " + base_identifier}), 400

    # mandatory keys
    mandatory_keys = ('group_id', 'count', 'bird_id')
    for key in mandatory_keys:
        if key not in data_in:
            return jsonify({"error": f"Input json missing key '{key}' in " + base_identifier}), 400

    # get the hunt_id associated with this group
    hunts_dict = get_hunt_dict(data_in["group_id"])
    if not hunts_dict:
        return jsonify({"message": "Internal error in update_harvest(), invalid read of hunt dictionary"}), 500

    # member attempting to post/put harvest must be in this group and hunt must be active
    # manager and above can modify any harvest at any time
    if user["level"] == "member":
        # 1. check to make sure user is in group
        pid_dict = cache.get(f"romeo:{data_in['group_id']}")
        if not pid_dict:
            # cache miss, go to db
            results = db.read_custom(
                f"SELECT u.public_id "
                f"FROM users u "
                f"JOIN groupings g ON u.id = g.slot1_id OR u.id = g.slot2_id OR u.id = slot3_id OR u.id = slot4_id "
                f"WHERE g.id = {data_in['group_id']}")
            names = ["public_id", ]
            pid_dict = db.format_dict(names, results)
            # update cache
            cache.add(f"romeo:{data_in['group_id']}", pid_dict, 60*60)
        slot_ids = [elem["public_id"] for elem in pid_dict]
        if not user["public_id"] in slot_ids:
            return jsonify({"error": "Members can only post harvest results to their own hunts"}), 400
        # 2. check to make sure hunt is active
        if hunts_dict['status'] != 'hunt_open':
            return jsonify({"message": f"Member cannot modify harvest for hunt {hunts_dict['id']} because hunt status is {hunts_dict['status']}"}), 400

    # make constants into length 1 arrays
    if type(data_in["count"]) is int or type(data_in["count"]) is str:
        data_in["count"] = (data_in["count"],)
        data_in["bird_id"] = (data_in["bird_id"],)

    # check to see if a record already exists
    harvest_id = None
    for idxBird in range(len(data_in['count'])):
        existing = db.read_custom(
            f"SELECT id "
            f"FROM {table_name} "
            f"WHERE group_id = {data_in['group_id']} "
            f"AND bird_id = {data_in['bird_id'][idxBird]}")
        if existing is None:
            return jsonify({"message": "Internal error"}), 500
        if existing:
            harvest_id = existing[0][0]
            print(f"harvest_id={harvest_id}")
            update_dict = {
                "count": data_in["count"][idxBird],
                "bird_id": data_in["bird_id"][idxBird]
            }
            if not db.update_row(table_name, harvest_id, update_dict):
                return jsonify({"message": f"Unable to update id {harvest_id} of table {table_name}"}), 500
        else:
            add_dict = {
                "group_id": data_in["group_id"],
                "count": data_in["count"][idxBird],
                "bird_id": data_in["bird_id"][idxBird]
            }
            db.add_row(table_name, add_dict)
            harvest_id = "new"  # this is to indicate that we just did a POST not a PUT. I don't want to waste a call back to the DB just to get the new row that was just added

    # the successful update in this function invalidates the value in cache
    cache.delete(f"india:{data_in['group_id']}")
    cache.delete(f"juliett:{data_in['group_id']}")
    cache.delete(f"mike:{data_in['group_id']}")

    # set the group's last update time to now
    if db.update_row("groupings", data_in["group_id"], {"harvest_update_time": central_time_now()}):
        cache.delete(f"golf:{hunts_dict['id']}")
        cache.delete("stats_clean")
        return jsonify({'message': f"Successful update of id {harvest_id} in {table_name}"}), 200
    else:
        return jsonify({"message": f"Unable to update harvest for group {data_in['group_id']} of table {table_name}"}), 500


@harvests_bp.route('/harvests', methods=['GET'])
@token_required(manager_and_above)
def get_all_rows(user):
    # results = db.read_all(table_name)  # original
    results = db.read_custom(f"SELECT harvest.id, harvest.group_id, harvest.count, birds.name, hunts.hunt_date, ponds.name FROM {table_name} "
                             f"JOIN birds ON harvest.bird_id=birds.id "
                             f"JOIN groupings ON harvest.group_id=groupings.id "
                             f"JOIN hunts ON hunts.id=groupings.hunt_id "
                             f"JOIN ponds ON groupings.pond_id=ponds.id")

    if results is not None:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["id", "group_id", "count", "bird", "hunt_date", "pond_name"]
        results_dict = db.format_dict(names_all, results)
        return jsonify({"harvests": results_dict}), 200
    else:
        return jsonify({"error": f"unknown error trying to read harvest"}), 400


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
@token_required(admin_only)
def del_row(user, harvest_id):
    if db.del_row(table_name, harvest_id):
        cache.delete("india")
        cache.delete("mike")
        cache.delete("juliett")
        cache.delete("stats_clean")
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {harvest_id} from table {table_name}"}), 400


@harvests_bp.route('/harvests/filtered', methods=['GET'])
@token_required(all_members)
def get_stats_birds(users):
    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()
    if 'hunt_id' in data_in and int(data_in['hunt_id']) > -1:
        b_filter_hunt = True
    else:
        b_filter_hunt = False

    if 'pond_id' in data_in and int(data_in['pond_id']) > -1:
        b_filter_pond = True
    else:
        b_filter_pond = False

    sql_qry_str = f"SELECT harvest.id, ponds.name, hunts.hunt_date, groupings.id, birds.name, harvest.count "\
                  f"FROM {table_name} "\
                  f"JOIN groupings ON harvest.group_id=groupings.id "\
                  f"JOIN birds ON harvest.bird_id=birds.id "\
                  f"JOIN hunts ON groupings.hunt_id=hunts.id "\
                  f"JOIN ponds ON groupings.pond_id=ponds.id "

    if b_filter_pond:
        sql_qry_str += f"WHERE ponds.id={data_in['pond_id']} "

    if b_filter_pond and b_filter_hunt:
        sql_qry_str += f"AND hunts.id={data_in['hunt_id']} "
    elif b_filter_hunt:
        sql_qry_str += f"WHERE hunts.id={data_in['hunt_id']} "

    sql_qry_str += f"ORDER BY hunts.hunt_date, ponds.name, birds.type"

    results = db.read_custom(sql_qry_str)

    if results is not None:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["harvest_id", "pond_name", "hunt_date", "group_id", "bird_name", "count"]
        print(f"Bravo:results:{results}")
        results_dict = db.format_dict(names_all, results)
        return jsonify({"harvests": results_dict}), 200
    else:
        return jsonify({"message": f"unknown error trying to read harvest"}), 400
