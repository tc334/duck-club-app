from flask import Blueprint, request, jsonify
from datetime import datetime
import math
import time
from .. import db
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/stats/hunters', methods=['GET'])
@token_required(all_members)
def get_one_row(users):

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
            'harvest_ave_non': 0.0
        }
        b_write = False  # default is to skip writes that aren't necessary

        # test to see if there is a duck count for this group id
        count = [tup[1] for tup in id_ducks if tup[0] == group[0]]
        if len(count) == 1:
            update_dict["harvest_ave_ducks"] = round(float(count[0]) / group[1], 2)
            # only update if there is a significant change in the average
            if math.fabs(update_dict["harvest_ave_ducks"] - group[2]) > 0.01:
                b_write = True

        # repeat for non-ducks
        count = [tup[1] for tup in id_non if tup[0] == group[0]]
        if len(count) == 1:
            update_dict["harvest_ave_non"] = round(float(count[0]) / group[1], 2)
            # only update if there is a significant change in the average
            if math.fabs(update_dict["harvest_ave_non"] - group[3]) > 0.01:
                b_write = True

        if b_write:
            db.update_row("groupings", group[0], update_dict)
