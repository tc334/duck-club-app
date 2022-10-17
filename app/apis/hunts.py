from flask import Blueprint, request, jsonify
import datetime
from .. import db, cache
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above


hunts_bp = Blueprint('hunts', __name__)
table_name = 'hunts'


@hunts_bp.route('/hunts', methods=['POST'])
@token_required(manager_and_above)
def add_row(user):
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"error": "Input json is empty in " + base_identifier}), 400

    # check to make sure there isn't already another hunt on the same day
    existing = db.read_custom(f"SELECT id FROM {table_name} WHERE hunt_date = '{data_in['hunt_date']}'")
    if existing is None:
        return jsonify({"message": "Internal error"}), 500
    if existing:
        return jsonify({"message": f"Cannot modify this hunt because hunt {existing[0][0]} already exists on date {data_in['hunt_date']}"}), 400

    # check to make sure there is only one hunt at a time active
    if 'status' in data_in and data_in['status'] in ('signup_open', 'signup_closed', 'draw_complete', 'hunt_open'):
        existing = db.read_custom(f"SELECT id, status FROM {table_name} WHERE status <> 'hunt_closed'")
        if existing is None:
            return jsonify({"message": "Internal error"}), 400
        if existing:
            return jsonify({"message": f"Cannot add this hunt because hunt {existing[0][0]} already has status {existing[0][1]}"}), 400

    # database interaction #2 - write
    db.add_row(table_name, data_in)
    cache.delete("alpha")
    cache.delete("echo")
    cache.delete("sierra")
    cache.delete("tango")

    return jsonify({"message": "New hunt started"}), 201


@hunts_bp.route('/hunts', methods=['GET'])
@token_required(all_members)
def get_all_rows(user):
    results_dict = db.read_all(table_name)

    # time has to be cleaned up before it cane be jsonified
    time_keys = ["signup_closed_time", "hunt_open_time", "hunt_close_time"]
    for item in results_dict:
        for key in time_keys:
            item[key] = item[key].isoformat(timespec='minutes')

    return jsonify({"hunts": results_dict}), 200


@hunts_bp.route('/hunts/active', methods=['GET'])
@token_required(all_members)
def get_all_active(user):
    hunts_dict = cache.get("sierra")
    if len(hunts_dict) < 1:
        # cache miss, go to db
        results = db.read_custom(
            f"SELECT * "
            f"FROM {table_name} "
            f"WHERE status != 'hunt_closed' "
            f"ORDER BY hunt_date")

        if results is not None:
            # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
            hunts_dict = db.format_dict(None, results, table_name)
            time_keys = ["signup_closed_time", "hunt_open_time", "hunt_close_time"]
            for item in hunts_dict:
                for key in time_keys:
                    item[key] = item[key].isoformat(timespec='minutes')
            # update cache
            cache.add(f"sierra", hunts_dict, 24*60*60)
        else:
            return jsonify({"message": f"unknown error trying to read hunts"}), 400
    else:
        # cache hit, need to fix datetime fields
        for hunt in hunts_dict:
            hunt["hunt_date"] = datetime.datetime.strptime(hunt["hunt_date"], '%Y-%m-%d').date()

    return jsonify({"hunts": hunts_dict}), 200


@hunts_bp.route('/hunts/signup_open_or_closed', methods=['GET'])
@token_required(manager_and_above)
def get_signup_open_or_closed(user):
    results = db.read_custom(f"SELECT id, hunt_date FROM {table_name} WHERE status='signup_open' OR status='signup_closed'")

    if results is not None:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["id", "hunt_date"]
        results_dict = db.format_dict(names_all, results)
        return jsonify({"hunts": results_dict}), 200
    else:
        return jsonify({"message": f"unknown error trying to read hunts"}), 400


@hunts_bp.route('/hunts/signup_open', methods=['GET'])
@token_required(manager_and_above)
def get_signup_open(user):
    results = db.read_custom(f"SELECT id, hunt_date FROM {table_name} WHERE hunts.status = 'signup_open'")

    if results is not None:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["id", "hunt_date"]
        results_dict = db.format_dict(names_all, results)
        return jsonify({"hunts": results_dict}), 200
    else:
        return jsonify({"error": f"unknown error trying to read hunts"}), 400


@hunts_bp.route('/hunts/dates', methods=['GET'])
@token_required(all_members)
def get_hunt_dates(user):
    results = db.read_custom(f"SELECT id, hunt_date "
                             f"FROM {table_name} "
                             f"WHERE hunts.status = 'hunt_closed' "
                             f"ORDER BY hunt_date DESC")

    if results is not None and results is not False:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["id", "hunt_date"]
        results_dict = db.format_dict(names_all, results)
        return jsonify({"dates": results_dict}), 200
    else:
        return jsonify({"error": f"unknown error trying to read hunts"}), 400


@hunts_bp.route('/hunts/<hunt_id>', methods=['GET'])
@token_required(all_members)
def get_one_row(users, hunt_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE id={hunt_id}")

    if result and len(result) == 1:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = [a_dict["name"] for a_dict in db.tables[table_name].table_cols]
        results_dict = {name: result[0][col] for col, name in enumerate(names_all)}
        return jsonify({"hunt": results_dict}), 200
    else:
        return jsonify({"error": f"Could not find id {hunt_id} in table {table_name}"}), 400


@hunts_bp.route('/hunts/<hunt_id>', methods=['PUT'])
@token_required(manager_and_above)
def update_row(user, hunt_id):
    data_in = request.get_json()

    # check to make sure there isn't already another hunt on the same day
    if 'hunt_date' in data_in:
        existing = db.read_custom(f"SELECT id FROM {table_name} WHERE id != {hunt_id} AND hunt_date = '{data_in['hunt_date']}'")
        if existing is None:
            return jsonify({"message": "Internal error"}), 400
        if existing:
            return jsonify({"message": f"Cannot modify this hunt because hunt {existing[0][0]} already exists on date {data_in['hunt_date']}"}), 400

    results = db.read_custom(f"SELECT status from {table_name} WHERE id={hunt_id}")
    if results is None:
        return jsonify({"message": "Internal error"}), 500
    else:
        last_status = results[0][0]

    if 'status' in data_in:
        # check to make sure there is only one hunt at a time active
        if data_in['status'] != 'hunt_closed':
            existing = db.read_custom(f"SELECT id FROM {table_name} WHERE id != {hunt_id} AND status <> 'hunt_closed'")
            if existing is None:
                return jsonify({"message": "Internal error"}), 500
            if existing:
                return jsonify({"message": f"Cannot modify this hunt because hunt {existing[0][0]} is already active"}), 400

        # only an administrator can change status backwards (exception: draw_complete -> signup_closed)
        if last_status == 'signup_closed' and data_in['status'] == 'signup_open' and not user["level"] == 'administrator':
            return jsonify({"message": f"Unable to update hunt {hunt_id} because hunt status went backward"})
        if last_status == 'draw_complete' and data_in['status'] == 'signup_open' and not user["level"] == 'administrator':
            return jsonify({"message": f"Unable to update hunt {hunt_id} because hunt status went backward"})
        if last_status == 'hunt_open' and data_in['status'] in ('signup_open', 'signup_closed', 'draw_complete') and not user["level"] == 'administrator':
            return jsonify({"message": f"Unable to update hunt {hunt_id} because hunt status went backward"})
        if last_status == 'hunt_closed' and not data_in['status'] == 'hunt_closed' and not user["level"] == 'administrator':
            return jsonify({"message": f"Unable to update hunt {hunt_id} because hunt status went backward"})

        # if changing status from signup_open to signup_closed, reset pond availability & cancel invitations
        if last_status == 'signup_open' and data_in['status'] == 'signup_closed':
            if not db.update_custom(
                    f"UPDATE invitations "
                    f"SET active='false', cancellation_notes='all invitations cancel when signup closes' "
                    f"WHERE active='true'"
            ):
                return jsonify({"message": f"Unable to update id {hunt_id} of table {table_name}. Invitation cancellation failed."}), 500
            # reset all pond availability
            if not db.update_custom(f"UPDATE ponds SET selected=FALSE"):
                return jsonify({"message": f"Unable to update id {hunt_id} of table {table_name}. Reset ponds selected failed."}), 500
            # reset ponds only for groups in this hunt
            if not db.update_custom(f"UPDATE groupings SET pond_id=NULL WHERE hunt_id={hunt_id}"):
                return jsonify({"message": f"Unable to update id {hunt_id} of table {table_name}. Reset group ponds failed"}), 500

        # if changing status from signup_closed to draw_complete, make sure all groups have a pond assigned
        if last_status == 'signup_closed' and data_in['status'] == 'draw_complete':
            # grab pond_id for all groups in this hunt
            results = db.read_custom(f"SELECT groupings.pond_id FROM groupings WHERE hunt_id={hunt_id}")
            if results:
                pond_id = [elem[0] for elem in results]
                if None in pond_id:
                    return jsonify({"message": f"Unable to update id {hunt_id} of table {table_name} because not all groups have a pond assigned."}), 400
            else:
                return jsonify({"message": f"Unable to update id {hunt_id} of table {table_name}. Could not verify all groups had a pond."}), 500

        # cache data now invalid for all groups in this hunt
        results = db.read_custom(f"SELECT id FROM groupings WHERE hunt_id={hunt_id}")
        if results is not None and results:
            for gid in results:
                cache.delete(f"nov:{gid[0]}")

    if db.update_row(table_name, hunt_id, data_in):
        cache.delete("alpha")
        cache.delete("echo")
        cache.delete("sierra")
        cache.delete("tango")
        return jsonify({'message': f'Successful update of id {hunt_id} in {table_name}'}), 200
    else:
        return jsonify({"message": f"Unable to update id {hunt_id} of table {table_name}"}), 400


@hunts_bp.route('/hunts/<hunt_id>', methods=['DELETE'])
@token_required(admin_only)
def del_row(user, hunt_id):
    if db.del_row(table_name, hunt_id):
        cache.delete("alpha")
        cache.delete("echo")
        cache.delete("nov")
        cache.delete("sierra")
        cache.delete("tango")
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {hunt_id} from table {table_name}"}), 400


def get_current_prehunt():
    hunt_dict = cache.get("tango")
    if not hunt_dict:
        # cache miss, go to db
        result = db.read_custom(
            f"SELECT id, hunt_date, status "
            f"FROM hunts "
            f"WHERE status IN ('signup_open', 'signup_closed', 'draw_complete')")
        if result is None or result is False:
            return None
        if len(result) != 1:
            print(f"Error in get_current_prehunt. len(result)={len(result)}. Couldn't find a hunt in a pre-hunt state")
            return None
        names = ["id", "hunt_date", "status"]
        hunt_dict = db.format_dict(names, result)[0]
        # datetime requires special handling
        hunt_dict["hunt_date"] = hunt_dict["hunt_date"].isoformat()
        # cache update
        cache.add("tango", hunt_dict, 60 * 60)

    return hunt_dict
