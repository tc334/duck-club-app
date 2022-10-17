from flask import Blueprint, request, jsonify
from datetime import datetime, date
from .. import db, cache
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above

stats_bp = Blueprint('stats', __name__)
SET_NAME = "groups_needing_update"
RESET_KEY = "reset_forced"


@stats_bp.route('/stats/hunters', methods=['GET'])
@token_required(all_members)
def get_stats_hunters(users):

    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    update_group_harvest()

    # date range for query
    date_start, date_end = date_helper(data_in)
    if not date_start:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-date"}), 400

    results = []
    if data_in["filter-member"] == "whole-club":
        results = db.read_custom(f"SELECT users.id, CONCAT(users.first_name, ' ', users.last_name) AS name, "
                                 f"SUM(groupings.num_ducks/groupings.num_hunters), COUNT(groupings.num_ducks), "
                                 f"SUM(groupings.num_non/groupings.num_hunters) "
                                 f"FROM groupings "
                                 f"JOIN participants ON participants.grouping_id=groupings.id "
                                 f"JOIN users ON participants.user_id=users.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"WHERE hunts.hunt_date>='{date_start}' "
                                 f"AND hunts.hunt_date<='{date_end}' "
                                 f"GROUP BY users.id, name "
                                 f"ORDER BY users.id")
    elif data_in["filter-member"] == "just-me":
        results = db.read_custom(f"SELECT users.id, CONCAT(users.first_name, ' ', users.last_name) AS name, "
                                 f"SUM(groupings.num_ducks/groupings.num_hunters), COUNT(groupings.num_ducks), "
                                 f"SUM(groupings.num_non/groupings.num_hunters) "
                                 f"FROM groupings "
                                 f"JOIN participants ON participants.grouping_id=groupings.id "
                                 f"JOIN users ON participants.user_id=users.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"WHERE users.id={users['id']} "
                                 f"AND hunts.hunt_date>='{date_start}' "
                                 f"AND hunts.hunt_date<='{date_end}' "
                                 f"GROUP BY users.id, name "
                                 f"ORDER BY users.id")
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-member"}), 400
    if results is None:
        return jsonify({"message": "internal error in get_stats_hunters"}), 500

    # if no results found, stop here
    if len(results) == 0:
        return jsonify({"message": "no results found within filter bounds"}), 404

    list_of_dicts = []
    for user in results:
        list_of_dicts.append({
            'name': user[1],
            'hunts': user[3],
            'ducks': float(user[2]),
            'non_ducks': float(user[4])
        })

    return jsonify({"stats": list_of_dicts}), 200


def update_group_harvest():
    # compute the total number of ducks and non-ducks per hunter for each grouping

    # only force a recount once after a server reset
    if not cache.get_plain(RESET_KEY):
        # add this key so that no other wsgi workers waste time going through the forced recount
        cache.add_plain(RESET_KEY, "True")

        # have to do this once because there could be a server reboot after the cache key (indicating a recount for a
        # group is required) is added but before a stats query came along to trigger action on it
        force_recount()

        return

    # now only update the groups in the set needing update
    cache_result = cache.set_pop(SET_NAME)
    while cache_result:
        group_id = cache_result.decode()

        result_ducks = db.read_custom(f"SELECT SUM(harvest.count) "
                                      f"FROM harvest "
                                      f"JOIN groupings ON harvest.group_id=groupings.id "
                                      f"JOIN birds ON harvest.bird_id=birds.id "
                                      f"WHERE birds.type='duck' "
                                      f"AND groupings.id={group_id}")

        if result_ducks and len(result_ducks) == 1:
            num_ducks = result_ducks[0][0]
        else:
            num_ducks = 0

        result_non =   db.read_custom(f"SELECT SUM(harvest.count) "
                                      f"FROM harvest "
                                      f"JOIN groupings ON harvest.group_id=groupings.id "
                                      f"JOIN birds ON harvest.bird_id=birds.id "
                                      f"WHERE birds.type<>'duck' "
                                      f"AND groupings.id={group_id}")

        if result_non and len(result_non) == 1:
            num_non = result_non[0][0]
        else:
            num_non = 0

        if num_non is None:
            num_non = 0
            print(f"Echo:Just caught num_non as None. result_non:{result_non}")
            print(f"group_id:{group_id}")

        update_dict = {
            'num_ducks': num_ducks,
            'num_non': num_non
        }

        if num_ducks != 0 or num_non != 0:
            db.update_row("groupings", group_id, update_dict)

        # clear cache result that just got invalidated
        hunt_id = db.read_custom(f"SELECT hunt_id FROM groupings WHERE id='{group_id}'")[0][0]
        cache.delete(f"bravo:{hunt_id}")

        cache_result = cache.set_pop(SET_NAME)


@stats_bp.route('/stats/flush_cache')
@token_required(admin_only)
def external_flush_cache(users):
    print("Cache flush forced externally")
    cache.wipe_cache()
    return jsonify({"message": "Cache flush complete"}), 200


@stats_bp.route('/stats/force_recount')
@token_required(admin_only)
def external_force_recount(users):
    print("Recount forced externally")
    force_recount()
    return jsonify({"message": "Forced recount complete"}), 200


def force_recount():
    # compute the total number of ducks and non-ducks per hunter for each grouping
    print("Running force_recount()")

    result_ducks = db.read_custom(f"SELECT groupings.id, SUM(harvest.count) "
                                  f"FROM harvest "
                                  f"JOIN groupings ON harvest.group_id=groupings.id "
                                  f"JOIN birds ON harvest.bird_id=birds.id "
                                  f"WHERE birds.type='duck' "
                                  f"GROUP BY groupings.id")

    group_ids_ducks = [elem[0] for elem in result_ducks]

    result_non   = db.read_custom(f"SELECT groupings.id, SUM(harvest.count) "
                                  f"FROM harvest "
                                  f"JOIN groupings ON harvest.group_id=groupings.id "
                                  f"JOIN birds ON harvest.bird_id=birds.id "
                                  f"WHERE birds.type<>'duck' "
                                  f"GROUP BY groupings.id")

    if result_non:
        group_ids_non = [elem[0] for elem in result_non]
    else:
        group_ids_non = []

    # loop through all of the duck results
    for item in result_ducks:
        num_non = 0  # default
        try:
            idx_non = group_ids_non.index(item[0])
            num_non = result_non[idx_non][1]
        except ValueError:
            pass

        update_dict = {
            'num_ducks': item[1],
            'num_non': num_non
        }

        db.update_row("groupings", item[0], update_dict)

    # find all of the non-duck results that didn't have a corresponding duck result
    idx_non_only = []
    for index, element in enumerate(group_ids_non):
        if element not in group_ids_ducks:
            idx_non_only.append(index)

    # loop through all of the non-duck results that don't have ducks
    for idx in idx_non_only:
        update_dict = {
            'num_ducks': 0,
            'num_non': result_non[idx][1]
        }

        db.update_row("groupings", result_non[idx][0], update_dict)

    cache.delete("golf")


@stats_bp.route('/stats/club', methods=['GET'])
@token_required(all_members)
def get_stats_club(users):

    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    update_group_harvest()

    # date range for query
    date_start, date_end = date_helper(data_in)
    if not date_start:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-date"}), 400

    results = db.read_custom(f"SELECT hunts.hunt_date, "
                             f"COUNT(groupings.id), "
                             f"SUM(groupings.num_hunters), "
                             f"SUM(groupings.num_ducks), "
                             f"SUM(groupings.num_non), "
                             f"SUM(IF(groupings.num_ducks>=6*groupings.num_hunters, 1, 0)) "
                             f"FROM hunts "
                             f"JOIN groupings ON groupings.hunt_id=hunts.id "
                             f"WHERE hunts.hunt_date>='{date_start}' "
                             f"AND hunts.hunt_date<='{date_end}' "
                             f"GROUP BY hunts.id "
                             f"ORDER BY hunts.id")

    # if no results found, stop here
    if not results or len(results) == 0:
        return jsonify({"message": "no results found within filter bounds"}), 404

    # now stitch the static and the counts together
    list_of_dicts = []
    for hunt in results:
        list_of_dicts.append({
            'date': hunt[0],
            'num_groups': hunt[1],
            'num_hunters': float(hunt[2]),
            'num_ducks': float(hunt[3]),
            'non_ducks': float(hunt[4]),
            'limits': float(hunt[5])
        })

    return jsonify({"stats": list_of_dicts}), 200


@stats_bp.route('/stats/birds', methods=['GET'])
@token_required(all_members)
def get_stats_birds(users):
    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    update_group_harvest()

    # date range for query
    date_start, date_end = date_helper(data_in)
    if not date_start:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-date"}), 400

    if data_in["filter-member"] == "whole-club":
        results = db.read_custom(f"SELECT birds.name, SUM(harvest.count) "
                                 f"FROM birds "
                                 f"JOIN harvest ON harvest.bird_id=birds.id "
                                 f"JOIN groupings ON harvest.group_id=groupings.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"WHERE hunts.hunt_date>='{date_start}' "
                                 f"AND hunts.hunt_date<='{date_end}' "
                                 f"GROUP BY birds.name "
                                 f"ORDER BY birds.name")
    elif data_in["filter-member"] == "just-me":
        results = db.read_custom(f"SELECT birds.name, "
                                 f"SUM(harvest.count/groupings.num_hunters) "
                                 f"FROM birds "
                                 f"JOIN harvest ON harvest.bird_id=birds.id "
                                 f"JOIN groupings ON harvest.group_id=groupings.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"JOIN participants ON participants.grouping_id=groupings.id "
                                 f"JOIN users ON participants.user_id=users.id "
                                 f"WHERE users.id={users['id']} "
                                 f"AND hunts.hunt_date>='{date_start}' "
                                 f"AND hunts.hunt_date<='{date_end}' "
                                 f"GROUP BY birds.name "
                                 f"ORDER BY birds.name")
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-member"}), 400

    # if no results found, stop here
    if len(results) == 0:
        return jsonify({"message": "no results found within filter bounds"}), 404

    # now compute the total count
    total_count = 0
    for bird in results:
        total_count += float(bird[1])

    # now stitch the names and the counts together
    list_of_dicts = []
    for bird in results:
        list_of_dicts.append({
            'name': bird[0],
            'count': float(bird[1]),
            'pct': float(bird[1]) / total_count,
        })

    return jsonify({"stats": list_of_dicts}), 200


@stats_bp.route('/stats/ponds', methods=['GET'])
@token_required(all_members)
def get_stats_ponds(users):
    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    update_group_harvest()

    # date range for query
    date_start, date_end = date_helper(data_in)
    if not date_start:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-date"}), 400

    if data_in["filter-member"] == "whole-club":
        results = db.read_custom(f"SELECT ponds.name, "
                                 f"COUNT(DISTINCT groupings.id), "
                                 f"SUM(groupings.num_ducks), SUM(groupings.num_non), SUM(groupings.num_hunters) "
                                 f"FROM ponds "
                                 f"JOIN groupings ON groupings.pond_id=ponds.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"WHERE hunts.hunt_date>='{date_start}' "
                                 f"AND hunts.hunt_date<='{date_end}' "
                                 f"GROUP BY ponds.name "
                                 f"ORDER BY ponds.name")
    elif data_in["filter-member"] == "just-me":
        results = db.read_custom(f"SELECT ponds.name, "
                                 f"COUNT(DISTINCT groupings.id), "
                                 f"SUM(groupings.num_ducks/groupings.num_hunters), "
                                 f"SUM(groupings.num_non/groupings.num_hunters), COUNT(DISTINCT groupings.id) "
                                 f"FROM ponds "
                                 f"JOIN groupings ON groupings.pond_id=ponds.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"JOIN participants ON participants.grouping_id=groupings.id "
                                 f"JOIN users ON participants.user_id=users.id "
                                 f"WHERE hunts.hunt_date>='{date_start}' "
                                 f"AND hunts.hunt_date<='{date_end}' "
                                 f"AND users.id={users['id']} "
                                 f"GROUP BY ponds.name "
                                 f"ORDER BY ponds.name")
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-member"}), 400

    # None or False means there was a read error
    if not results:
        return jsonify({"message": "internal error"}), 500

    # if no results found, stop here
    if len(results) == 0:
        return jsonify({"message": "no results found within filter bounds"}), 404

    # now stitch the names and the counts together
    list_of_dicts = []
    for pond in results:
        # *****************************
        # temporary hack to stop crashing
        if pond[3] is None:
            pond[3] = 0
        # end hack
        # *****************************
        list_of_dicts.append({
            'pond_name': pond[0],
            'num_hunts': float(pond[1]),
            'num_ducks': float(pond[2]),
            'non_ducks': float(pond[3]),
            'ave_ducks': float(pond[2])/float(pond[4])
        })

    # if a pond-id is included in the query, get hunt history on that pond
    if "pond_id" in data_in and int(data_in["pond_id"]) > -1:
        if data_in["filter-member"] == "whole-club":
            results = db.read_custom(f"SELECT hunts.hunt_date, groupings.num_ducks, groupings.num_hunters "
                                     f"FROM hunts "
                                     f"JOIN groupings ON groupings.hunt_id=hunts.id "
                                     f"JOIN ponds ON groupings.pond_id=ponds.id "
                                     f"WHERE hunts.hunt_date>='{date_start}' "
                                     f"AND hunts.hunt_date<='{date_end}' "
                                     f"AND ponds.id={data_in['pond_id']} "
                                     f"ORDER BY hunts.hunt_date")
        elif data_in["filter-member"] == "just-me":
            results = db.read_custom(f"SELECT hunts.hunt_date, groupings.num_ducks/groupings.num_hunters, 1 "
                                     f"FROM hunts "
                                     f"JOIN groupings ON groupings.hunt_id=hunts.id "
                                     f"JOIN harvest ON harvest.group_id=groupings.id "
                                     f"JOIN ponds ON groupings.pond_id=ponds.id "
                                     f"JOIN participants ON participants.grouping_id=groupings.id "
                                     f"JOIN users ON participants.user_id=users.id "
                                     f"WHERE users.id={users['id']} "
                                     f"AND hunts.hunt_date>='{date_start}' "
                                     f"AND hunts.hunt_date<='{date_end}' "
                                     f"AND ponds.id={data_in['pond_id']} "
                                     f"GROUP BY hunts.hunt_date "
                                     f"ORDER BY hunts.hunt_date")
        else:
            return jsonify({"message": f"Unable to get pond stats because of unrecognized filter-member"}), 400

        # if no results found, stop here
        if results and len(results) > 0:
            # now stitch the names and the counts together
            list_of_dicts_2 = []
            for hunt in results:
                list_of_dicts_2.append({
                    'date': hunt[0],
                    'num_ducks': hunt[1],
                    'ave_ducks': float(hunt[1]) / float(hunt[2])
                })
        else:
            return jsonify({"stats": list_of_dicts}), 200

        return jsonify({"stats": list_of_dicts, "hunt_history": list_of_dicts_2}), 200
    else:
        return jsonify({"stats": list_of_dicts}), 200


def date_helper(data_in):
    if data_in["filter-date"] == "all-records":
        date_start = date(1900, 1, 1)
        date_end = date(3000, 1, 1)
    elif data_in["filter-date"] == "custom-range":
        temp = data_in["date-start"].split("-")
        date_start = date(int(temp[0]), int(temp[1]), int(temp[2]))
        temp = data_in["date-end"].split("-")
        date_end = date(int(temp[0]), int(temp[1]), int(temp[2]))
    elif data_in["filter-date"] == "current-season":
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month >= 9:
            date_start = date(current_year, 9, 1)
            date_end = date(current_year + 1, 9, 1)
        else:
            date_start = date(current_year - 1, 9, 1)
            date_end = date(current_year, 9, 1)
    else:
        return False, False

    return date_start, date_end


@stats_bp.route('/stats/history/<public_id>', methods=['GET'])
@token_required(all_members)
def get_hunt_history(users, public_id):

    # make sure that members can only query their own hunts
    if users['level'] == 'member' and users['public_id'] != public_id:
        return jsonify({"message": "You are not allowed to access other hunters history"}), 401

    results = db.read_custom(
        f"SELECT CONCAT(users.first_name, ' ', users.last_name), hunts.hunt_date, ponds.name, groupings.id, "
        f"groupings.num_ducks/groupings.num_hunters, groupings.num_non/groupings.num_hunters "
        f"FROM users "
        f"JOIN participants ON participants.user_id=users.id "
        f"JOIN groupings ON participants.grouping_id=groupings.id "
        f"JOIN hunts ON groupings.hunt_id=hunts.id "
        f"JOIN ponds ON groupings.pond_id=ponds.id "
        f"WHERE users.public_id='{public_id}' "
        f"ORDER BY hunts.hunt_date"
    )
    if results is None or results is False:
        return jsonify({"message": "Internal error in get_hunt_history"}), 500
    names = ["name", "date", "pond", "group_id", "ducks", "non_ducks"]
    hunts_dict = db.format_dict(names, results)

    return jsonify({"hunts": hunts_dict}), 200
