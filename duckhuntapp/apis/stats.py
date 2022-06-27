from flask import Blueprint, request, jsonify
from datetime import datetime
import math
import time
from .. import db
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/stats/hunters', methods=['GET'])
@token_required(all_members)
def get_stats_hunters(users):

    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    # TODO: make this a background function that runs every X min. For now doing it every time
    update_group_harvest()

    # date range for query
    if data_in["filter-date"] == "all-records":
        date_start = "1900-01-01"
        date_end = "3000-01-01"
    elif data_in["filter-date"] == "custom-range":
        date_start = data_in["date-start"]
        date_end = data_in["date-end"]
    elif data_in["filter-date"] == "current-season":
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month > 7:
            date_start = str(current_year) + "-07-01"
            date_end = str(current_year+1) + "-07-01"
        else:
            date_start = str(current_year-1) + "-07-01"
            date_end = str(current_year) + "-07-01"
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-date"}), 400

    results = []
    for slot_num in range(1, 5):
        if data_in["filter-member"] == "whole-club":
            this_slot = db.read_custom(f"SELECT users.id, "
                                       f"SUM(groupings.harvest_ave_ducks), COUNT(groupings.harvest_ave_ducks), "
                                       f"SUM(groupings.harvest_ave_non) "
                                       f"FROM groupings "
                                       f"JOIN users ON groupings.slot{slot_num}_id=users.id "
                                       f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                       f"WHERE groupings.slot{slot_num}_type='member' "
                                       f"AND hunts.hunt_date>'{date_start}' "
                                       f"AND hunts.hunt_date<'{date_end}' "
                                       f"GROUP BY users.id "
                                       f"ORDER BY users.id")
        elif data_in["filter-member"] == "just-me":
            this_slot = db.read_custom(f"SELECT users.id, "
                                       f"SUM(groupings.harvest_ave_ducks), COUNT(groupings.harvest_ave_ducks), "
                                       f"SUM(groupings.harvest_ave_non) "
                                       f"FROM groupings "
                                       f"JOIN users ON groupings.slot{slot_num}_id=users.id "
                                       f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                       f"WHERE groupings.slot{slot_num}_type='member' "
                                       f"AND users.id={users['id']} "
                                       f"AND hunts.hunt_date>'{date_start}' "
                                       f"AND hunts.hunt_date<'{date_end}' "
                                       f"GROUP BY users.id "
                                       f"ORDER BY users.id")
        else:
            return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-member"}), 400
        results = merge_slots(results, this_slot)

    # if no results found, stop here
    if len(results) == 0:
        return jsonify({"message": "no results found within filter bounds"}), 404

    # now get the names associated with the above results
    list_of_ids = "("
    for elem in results:
        list_of_ids += str(elem[0]) + ", "
    list_of_ids = list_of_ids[:-2] + ")"
    names = db.read_custom(f"SELECT first_name, last_name FROM users WHERE id IN {list_of_ids} ORDER BY id")

    # now stitch the names and the counts together
    list_of_dicts = []
    for i in range(len(names)):
        list_of_dicts.append({
            'first_name': names[i][0],
            'last_name': names[i][1],
            'hunts': results[i][2],
            'ducks': results[i][1],
            'non_ducks': results[i][3]
        })

    return jsonify({"stats": list_of_dicts}), 200


def merge_slots(slot_1, slot_2):
    # input is a list of tuples; if first element matches, add the rest together
    merged = slot_1 + [list(elem) for elem in slot_2]
    i = 0
    while i < len(merged)-1:
        j = i+1
        while j < len(merged):
            if merged[i][0] == merged[j][0]:
                merged[i][1:] = [merged[i][x] + merged[j][x] for x in range(1, len(merged[j]))]
                merged.pop(j)
            else:
                j += 1
        i += 1
    return merged


def update_group_harvest():
    # compute the average number of ducks and non-ducks per hunter for each grouping

    id_ducks = db.read_custom(f"SELECT groupings.id, SUM(harvest.count) "
                              f"FROM groupings "
                              f"JOIN harvest ON harvest.group_id=groupings.id "
                              f"JOIN birds ON harvest.bird_id=birds.id "
                              f"WHERE birds.type='duck' "
                              f"GROUP BY groupings.id "
                              f"ORDER BY groupings.id")

    id_non =   db.read_custom(f"SELECT groupings.id, SUM(harvest.count) "
                              f"FROM groupings "
                              f"JOIN harvest ON harvest.group_id=groupings.id "
                              f"JOIN birds ON harvest.bird_id=birds.id "
                              f"WHERE birds.type<>'duck' "
                              f"GROUP BY groupings.id "
                              f"ORDER BY groupings.id")

    id_num = db.read_custom(f"SELECT id, num_hunters, harvest_ave_ducks, harvest_ave_non "
                            f"FROM groupings "
                            f"ORDER BY groupings.id")

    for group in id_num:
        # defaults
        update_dict = {
            'harvest_ave_ducks': 0.0,
            'harvest_ave_non': 0.0,
            'limit': False
        }
        b_write = False  # default is to skip writes that aren't necessary

        # test to see if there is a duck count for this group id
        count = [tup[1] for tup in id_ducks if tup[0] == group[0]]
        if len(count) == 1:
            update_dict["harvest_ave_ducks"] = float(count[0]) / group[1]
            # only update if there is a significant change in the average
            if math.fabs(update_dict["harvest_ave_ducks"] - group[2]) > 0.01:
                b_write = True

        # repeat for non-ducks
        count = [tup[1] for tup in id_non if tup[0] == group[0]]
        if len(count) == 1:
            update_dict["harvest_ave_non"] = float(count[0]) / group[1]
            # only update if there is a significant change in the average
            if math.fabs(update_dict["harvest_ave_non"] - group[3]) > 0.01:
                b_write = True

        if b_write:
            db.update_row("groupings", group[0], update_dict)


@stats_bp.route('/stats/club', methods=['GET'])
@token_required(all_members)
def get_stats_club(users):

    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    # TODO: make this a background function that runs every X min. For now doing it every time
    update_group_harvest()

    # date range for query
    if data_in["filter-date"] == "all-records":
        date_start = "1900-01-01"
        date_end = "3000-01-01"
    elif data_in["filter-date"] == "custom-range":
        date_start = data_in["date-start"]
        date_end = data_in["date-end"]
    elif data_in["filter-date"] == "current-season":
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month > 7:
            date_start = str(current_year) + "-07-01"
            date_end = str(current_year+1) + "-07-01"
        else:
            date_start = str(current_year-1) + "-07-01"
            date_end = str(current_year) + "-07-01"
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-date"}), 400

    results = db.read_custom(f"SELECT hunts.id, "
                             f"COUNT(groupings.harvest_ave_ducks), "
                             f"SUM(groupings.num_hunters), "
                             f"SUM(groupings.harvest_ave_ducks*groupings.num_hunters), "
                             f"SUM(groupings.harvest_ave_non*groupings.num_hunters), "
                             f"SUM(IF(groupings.harvest_ave_ducks>5.9, 1, 0)) "
                             f"FROM hunts "
                             f"JOIN groupings ON groupings.hunt_id=hunts.id "
                             f"WHERE hunts.hunt_date>'{date_start}' "
                             f"AND hunts.hunt_date<'{date_end}' "
                             f"GROUP BY hunts.id "
                             f"ORDER BY hunts.id")

    # if no results found, stop here
    if len(results) == 0:
        return jsonify({"message": "no results found within filter bounds"}), 404

    # now get the static associated with the above results
    list_of_ids = "("
    for elem in results:
        list_of_ids += str(elem[0]) + ", "
    list_of_ids = list_of_ids[:-2] + ")"
    static = db.read_custom(f"SELECT hunt_date FROM hunts WHERE id IN {list_of_ids} ORDER BY id")

    # now stitch the static and the counts together
    list_of_dicts = []
    for i in range(len(static)):
        list_of_dicts.append({
            'date': static[i][0],
            'num_groups': results[i][1],
            'num_hunters': results[i][2],
            'num_ducks': results[i][3],
            'non_ducks': results[i][4],
            'limits': results[i][5]
        })

    return jsonify({"stats": list_of_dicts}), 200


@stats_bp.route('/stats/birds', methods=['GET'])
@token_required(all_members)
def get_stats_birds(users):
    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    # TODO: make this a background function that runs every X min. For now doing it every time
    update_group_harvest()

    # date range for query
    if data_in["filter-date"] == "all-records":
        date_start = "1900-01-01"
        date_end = "3000-01-01"
    elif data_in["filter-date"] == "custom-range":
        date_start = data_in["date-start"]
        date_end = data_in["date-end"]
    elif data_in["filter-date"] == "current-season":
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month > 7:
            date_start = str(current_year) + "-07-01"
            date_end = str(current_year + 1) + "-07-01"
        else:
            date_start = str(current_year - 1) + "-07-01"
            date_end = str(current_year) + "-07-01"
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-date"}), 400

    if data_in["filter-member"] == "whole-club":
        results = db.read_custom(f"SELECT birds.id, "
                                 f"SUM(harvest.count) "
                                 f"FROM birds "
                                 f"JOIN harvest ON harvest.bird_id=birds.id "
                                 f"JOIN groupings ON harvest.group_id=groupings.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"WHERE hunts.hunt_date>'{date_start}' "
                                 f"AND hunts.hunt_date<'{date_end}' "
                                 f"GROUP BY birds.id "
                                 f"ORDER BY birds.id")
    elif data_in["filter-member"] == "just-me":
        results = []
        for slot_num in range(1, 5):
            this_slot = db.read_custom(f"SELECT birds.id, "
                                       f"SUM(harvest.count) "
                                       f"FROM birds "
                                       f"JOIN harvest ON harvest.bird_id=birds.id "
                                       f"JOIN groupings ON harvest.group_id=groupings.id "
                                       f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                       f"JOIN users ON groupings.slot{slot_num}_id=users.id "
                                       f"WHERE groupings.slot{slot_num}_type='member' "
                                       f"AND users.id={users['id']} "
                                       f"AND hunts.hunt_date>'{date_start}' "
                                       f"AND hunts.hunt_date<'{date_end}' "
                                       f"GROUP BY birds.id "
                                       f"ORDER BY birds.id")
            results = merge_slots(results, this_slot)
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-member"}), 400

    # if no results found, stop here
    if len(results) == 0:
        return jsonify({"message": "no results found within filter bounds"}), 404

    # now get the names associated with the above results
    total_count = 0
    list_of_ids = "("
    for elem in results:
        list_of_ids += str(elem[0]) + ", "
        total_count += float(elem[1])
    list_of_ids = list_of_ids[:-2] + ")"
    names = db.read_custom(f"SELECT name FROM birds WHERE id IN {list_of_ids} ORDER BY id")

    # now stitch the names and the counts together
    list_of_dicts = []
    for i in range(len(names)):
        list_of_dicts.append({
            'name': names[i][0],
            'count': float(results[i][1]),
            'pct': float(results[i][1]) / total_count,
        })

    return jsonify({"stats": list_of_dicts}), 200


@stats_bp.route('/stats/ponds', methods=['GET'])
@token_required(all_members)
def get_stats_ponds(users):
    # convert query selector string in URL to dictionary
    data_in = request.args.to_dict()

    # TODO: make this a background function that runs every X min. For now doing it every time
    update_group_harvest()

    # date range for query
    if data_in["filter-date"] == "all-records":
        date_start = "1900-01-01"
        date_end = "3000-01-01"
    elif data_in["filter-date"] == "custom-range":
        date_start = data_in["date-start"]
        date_end = data_in["date-end"]
    elif data_in["filter-date"] == "current-season":
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month > 7:
            date_start = str(current_year) + "-07-01"
            date_end = str(current_year + 1) + "-07-01"
        else:
            date_start = str(current_year - 1) + "-07-01"
            date_end = str(current_year) + "-07-01"
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-date"}), 400

    if data_in["filter-member"] == "whole-club":
        results = db.read_custom(f"SELECT ponds.id, "
                                 f"SUM(harvest.count), COUNT( DISTINCT harvest.group_id ), "
                                 f"AVG(groupings.harvest_ave_ducks) "
                                 f"FROM ponds "
                                 f"JOIN groupings ON groupings.pond_id=ponds.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"JOIN harvest ON harvest.group_id=groupings.id "
                                 f"JOIN birds ON harvest.bird_id=birds.id "
                                 f"WHERE hunts.hunt_date>'{date_start}' "
                                 f"AND hunts.hunt_date<'{date_end}' "
                                 f"AND birds.type='duck' "
                                 f"GROUP BY ponds.id "
                                 f"ORDER BY ponds.id")
        nonduck = db.read_custom(f"SELECT ponds.id, "
                                 f"SUM(harvest.count) "
                                 f"FROM ponds "
                                 f"JOIN groupings ON groupings.pond_id=ponds.id "
                                 f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                 f"JOIN harvest ON harvest.group_id=groupings.id "
                                 f"JOIN birds ON harvest.bird_id=birds.id "
                                 f"WHERE hunts.hunt_date>'{date_start}' "
                                 f"AND hunts.hunt_date<'{date_end}' "
                                 f"AND birds.type<>'duck' "
                                 f"GROUP BY ponds.id "
                                 f"ORDER BY ponds.id")
    elif data_in["filter-member"] == "just-me":
        results = []
        nonduck = []
        for slot_num in range(1, 5):
            this_slot = db.read_custom(f"SELECT ponds.id, "
                                       f"SUM(harvest.count), COUNT( DISTINCT harvest.group_id ), "
                                       f"AVG(groupings.harvest_ave_ducks) "
                                       f"FROM ponds "
                                       f"JOIN groupings ON groupings.pond_id=ponds.id "
                                       f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                       f"JOIN harvest ON harvest.group_id=groupings.id "
                                       f"JOIN birds ON harvest.bird_id=birds.id "
                                       f"JOIN users ON groupings.slot{slot_num}_id=users.id "
                                       f"WHERE groupings.slot{slot_num}_type='member' "
                                       f"AND hunts.hunt_date>'{date_start}' "
                                       f"AND hunts.hunt_date<'{date_end}' "
                                       f"AND users.id={users['id']} "
                                       f"AND birds.type='duck' "
                                       f"GROUP BY ponds.id "
                                       f"ORDER BY ponds.id")
            results = merge_slots(results, this_slot)
            this_slot = db.read_custom(f"SELECT ponds.id, "
                                       f"SUM(harvest.count), COUNT( DISTINCT harvest.group_id ), "
                                       f"AVG(groupings.harvest_ave_ducks) "
                                       f"FROM ponds "
                                       f"JOIN groupings ON groupings.pond_id=ponds.id "
                                       f"JOIN hunts ON groupings.hunt_id=hunts.id "
                                       f"JOIN harvest ON harvest.group_id=groupings.id "
                                       f"JOIN birds ON harvest.bird_id=birds.id "
                                       f"JOIN users ON groupings.slot{slot_num}_id=users.id "
                                       f"WHERE groupings.slot{slot_num}_type='member' "
                                       f"AND hunts.hunt_date>'{date_start}' "
                                       f"AND hunts.hunt_date<'{date_end}' "
                                       f"AND users.id={users['id']} "
                                       f"AND birds.type<>'duck' "
                                       f"GROUP BY ponds.id "
                                       f"ORDER BY ponds.id")
            nonduck = merge_slots(nonduck, this_slot)
    else:
        return jsonify({"message": f"Unable to get hunter stats because of unrecognized filter-member"}), 400

    # if no results found, stop here
    if len(results) == 0:
        return jsonify({"message": "no results found within filter bounds"}), 404

    # now get the names associated with the above results
    total_count = 0
    list_of_ids = "("
    for elem in results:
        list_of_ids += str(elem[0]) + ", "
        total_count += float(elem[1])
    list_of_ids = list_of_ids[:-2] + ")"
    names = db.read_custom(f"SELECT name FROM ponds WHERE id IN {list_of_ids} ORDER BY id")

    # now stitch the names and the counts together
    list_of_dicts = []
    for i in range(len(names)):
        # check to see if this pond has any non-duck results
        idx_non = [count for count, value in enumerate(nonduck) if value[0] == results[i][0]]
        if len(idx_non) == 1:
            num_non_ducks = nonduck[idx_non][1]
        else:
            num_non_ducks = 0
        list_of_dicts.append({
            'pond_name': names[i][0],
            'num_hunts': float(results[i][2]),
            'num_ducks': float(results[i][1]),
            'non_ducks': num_non_ducks,
            'ave_ducks': float(results[i][3])
        })

    # if a pond-id is included in the query, get hunt history on that pond
    if "pond_id" in data_in:
        if data_in["filter-member"] == "whole-club":
            results = db.read_custom(f"SELECT hunts.id, groupings.harvest_ave_ducks, groupings.num_hunters "
                                     f"FROM hunts "
                                     f"JOIN groupings ON groupings.hunt_id=hunts.id "
                                     f"JOIN harvest ON harvest.group_id=groupings.id "
                                     f"JOIN ponds ON groupings.pond_id=ponds.id "
                                     f"WHERE hunts.hunt_date>'{date_start}' "
                                     f"AND hunts.hunt_date<'{date_end}' "
                                     f"AND ponds.id={data_in['pond_id']} "
                                     f"GROUP BY hunts.id "
                                     f"ORDER BY hunts.id")
        elif data_in["filter-member"] == "just-me":
            results = []
            for slot_num in range(1, 5):
                this_slot = db.read_custom(f"SELECT hunts.id, groupings.harvest_ave_ducks, groupings.num_hunters "
                                           f"FROM hunts "
                                           f"JOIN groupings ON groupings.hunt_id=hunts.id "
                                           f"JOIN harvest ON harvest.group_id=groupings.id "
                                           f"JOIN ponds ON groupings.pond_id=ponds.id "
                                           f"JOIN users ON groupings.slot{slot_num}_id=users.id "
                                           f"WHERE groupings.slot{slot_num}_type='member' "
                                           f"AND users.id={users['id']} "
                                           f"AND hunts.hunt_date>'{date_start}' "
                                           f"AND hunts.hunt_date<'{date_end}' "
                                           f"AND ponds.id={data_in['pond_id']} "
                                           f"GROUP BY hunts.id "
                                           f"ORDER BY hunts.id")
                results = merge_slots(results, this_slot)
        else:
            return jsonify({"message": f"Unable to get pond stats because of unrecognized filter-member"}), 400

        # if no results found, stop here
        if len(results) > 0:
            # now get the dates associated with the above results
            list_of_ids = "("
            for elem in results:
                list_of_ids += str(elem[0]) + ", "
            list_of_ids = list_of_ids[:-2] + ")"
            dates = db.read_custom(f"SELECT hunt_date FROM hunts WHERE id IN {list_of_ids} ORDER BY id")

            # now stitch the names and the counts together
            list_of_dicts_2 = []
            for i in range(len(dates)):
                list_of_dicts_2.append({
                    'date': dates[i][0],
                    'num_ducks': float(results[i][1]) * float(results[i][2]),
                    'ave_ducks': float(results[i][1])
                })
        else:
            return jsonify({"stats": list_of_dicts}), 200

        return jsonify({"stats": list_of_dicts, "hunt_history": list_of_dicts_2}), 200
    else:
        return jsonify({"stats": list_of_dicts}), 200
