from flask import Blueprint, request, jsonify
from .. import db, cache
from .auth_wraps import token_required, admin_only, all_members, manager_and_above, owner_and_above
from .hunts import get_current_prehunt
from .users import get_id_from_public_id

table_name = 'guests'
guests_bp = Blueprint(table_name, __name__)


@guests_bp.route('/guests', methods=['POST'])
@token_required(all_members)
def add_row(user):
    # adding a new guest will automatically join them to the current hunt
    data_in = request.get_json()

    # Error checking
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__
    if data_in is None:
        return jsonify({"message": "Input json is empty in " + base_identifier}), 400
    # mandatory keys - either guest_id OR full_name and type
    if "guest_id" not in data_in and not ("full_name" in data_in and "type" in data_in):
        return jsonify({"message": "Input json missing keys in " + base_identifier}), 400
    # optional key - public_id
    if "public_id" in data_in:
        data_in['user_id'] = get_id_from_public_id(data_in['public_id'])
    # need to know host
    if "guest_id" in data_in:
        # pull host id out from existing guest
        user_id = get_user_from_guest(data_in['guest_id'])
        if user_id is None:
            return jsonify({"message": f"internal error 9"}), 500
        data_in['user_id'] = user_id
    elif "user_id" not in data_in:
        # default to caller if no user id in data
        data_in["user_id"] = user['id']
    # hunt status must be signup open or signup closed to add a guest
    hunt_dict = get_current_prehunt()
    if hunt_dict["status"] not in ("signup_closed", "signup_open"):
        return jsonify({"message": "Cannot add guests unless hunt status is signup open or signup closed"})
    # check to make sure host is signed up for this hunt and there is room in host's group
    results = db.read_custom(
        f"SELECT groupings.id "
        f"FROM groupings "
        f"JOIN participants ON participants.grouping_id=groupings.id "
        f"WHERE groupings.hunt_id={hunt_dict['id']} "
        f"AND participants.user_id={data_in['user_id']}"
    )
    if results is None or results is False:
        return jsonify({"message": "internal error 2"}), 500
    if len(results) != 1:
        return jsonify({"message": f"Host cannot have guests unless they are signed up to hunt already"}), 400
    group_id = results[0][0]
    num_hunters = db.read_custom(f"SELECT COUNT(*) FROM participants p WHERE p.grouping_id={group_id}")[0][0]

    if num_hunters >= 4:
        return jsonify({"message": f"Group {group_id} doesn't have room for this guest"}), 400
    # if guest already exists, don't add them again to the guest table. Just create a participant
    if 'guest_id' in data_in:
        guest_id = data_in['guest_id']
    else:
        results = db.read_custom(
            f"SELECT id FROM guests WHERE user_id={data_in['user_id']} AND full_name='{data_in['full_name']}'"
        )
        if results is None or results is False:
            return jsonify({"message": "internal error 3"}), 500
        if len(results) == 0:
            # add guest to guest table
            guest_id = db.add_row(table_name, data_in)
        else:
            guest_id = results[0][0]

    # check to make sure guest isn't already participating in this hunt
    results = db.read_custom(
        f"SELECT groupings.id "
        f"FROM groupings "
        f"JOIN participants ON participants.grouping_id=groupings.id "
        f"WHERE participants.guest_id='{guest_id}' "
        f"AND groupings.hunt_id={hunt_dict['id']}"
    )
    if results is None or results is False:
        return jsonify({"message": "internal error 4"}), 500
    if len(results) > 0:
        return jsonify({"message": f"Guest {guest_id[:3]} is already in group {results[0][0]}"}), 400

    # add participant to group that is this guest
    db_row_participant = {
        "type": "guest",
        "grouping_id": group_id,
        "guest_id": guest_id,
    }
    participant_id = db.add_row("participants", db_row_participant)
    # test for success of previous operation
    if participant_id is not None and participant_id is not False:
        # clear out invalidated cache
        cache.delete(f"kilo:{group_id}")
        cache.delete(f"bravo:{hunt_dict['id']}")

        return jsonify({"message": "Successfully added new guest"}), 201
    else:
        return jsonify({"message": "error adding participant"})


@guests_bp.route('/my_guests', methods=['GET'])
@token_required(all_members)
def get_my_rows(user):
    # returns two lists: 1) user's guests in this hunt  2) user's historical guests
    hunt_dict = get_current_prehunt()
    if not hunt_dict:
        return jsonify({"message": "Could not find an open hunt to pull scouting reports from"}), 400

    results = db.read_custom(
        f"SELECT guests.id, guests.full_name, guests.type "
        f"FROM guests "
        f"JOIN participants ON participants.guest_id=guests.id "
        f"JOIN groupings ON participants.grouping_id=groupings.id "
        f"WHERE groupings.hunt_id={hunt_dict['id']} "
        f"AND guests.user_id={user['id']}"
    )
    if results is None or results is False:
        return jsonify({"message": "Internal error"}), 500
    names = ["id", "name", "type"]
    guest_dict = {"active": db.format_dict(names, results)}

    results = db.read_custom(
        f"SELECT guests.id, guests.full_name "
        f"FROM guests "
        f"WHERE guests.user_id={user['id']}"
    )
    if results is None or results is False:
        return jsonify({"message": "Internal error"}), 500
    names = ["id", "name"]
    guest_dict["historical"] = db.format_dict(names, results)

    return jsonify({"data": guest_dict}), 200


@guests_bp.route('/guests/<public_id>', methods=['GET'])
@token_required(owner_and_above)
def get_all_guests_for_one_member(user, public_id):
    user_id = get_id_from_public_id(public_id)

    results = db.read_custom(
        f"SELECT p.id, guests.id, h.id, guests.full_name, CONCAT(u.first_name, ' ', u.last_name), h.hunt_date "
        f"FROM participants p "
        f"JOIN guests ON p.guest_id=guests.id "
        f"JOIN users u ON guests.user_id=u.id "
        f"JOIN groupings ON p.grouping_id=groupings.id "
        f"JOIN hunts h ON groupings.hunt_id=h.id "
        f"WHERE guests.user_id={user_id} "
        f"ORDER BY h.hunt_date"
    )
    if results is None or results is False:
        return jsonify({"message": "Internal error in get_all_guests_for_one_member"}), 500
    print(f"Alpha:{results}")
    names = ["participant_id", "guest_id", "hunt_id", "guest", "member", "date"]
    guest_dict = db.format_dict(names, results)

    return jsonify({"data": guest_dict}), 200


@guests_bp.route('/guests', methods=['GET'])
@token_required(manager_and_above)
def get_all_active(user):
    results = db.read_custom(
        f"SELECT g.id, g.full_name, g.type, CONCAT(users.first_name, ' ', users.last_name) "
        f"FROM guests g "
        f"JOIN participants ON participants.guest_id=g.id "
        f"JOIN groupings ON participants.grouping_id=groupings.id "
        f"JOIN hunts ON groupings.hunt_id=hunts.id "
        f"JOIN users ON g.user_id=users.id "
        f"WHERE hunts.status IN ('signup_open', 'signup_closed', 'draw_complete')"
    )
    if results is None or results is False:
        return jsonify({"message": "Internal error"}), 500
    names = ["id", "name", "type", "host"]
    guest_dict = db.format_dict(names, results)
    return jsonify({"data": guest_dict}), 200


@guests_bp.route('/guests/<guest_id>', methods=['PUT'])
@token_required(manager_and_above)
def update_row(user, guest_id):
    data_in = request.get_json()

    keys_in = set(data_in.keys())
    allowable_keys = {"full_name", "type"}
    # no extra keys
    if len(keys_in - allowable_keys) > 0:
        return jsonify({'message': 'extra, unsupported keys in scouting report update'})
    # must have at least 1 allowable key
    if len(allowable_keys - keys_in) == len(allowable_keys):
        return jsonify({'message': 'missing required key in scouting report update'})
    if db.update_row(table_name, guest_id, data_in):
        return jsonify({'message': f'Successful update of id {guest_id} in {table_name}'}), 200
    else:
        return jsonify({"message": f"Unable to update id {guest_id} of table {table_name}"}), 400


@guests_bp.route('/drop_guest/<guest_id>', methods=['PUT'])
@token_required(all_members)
def drop_guest(user, guest_id):
    data_in = request.get_json()

    # need to know if there is a current hunt
    results = db.read_custom(
        f"SELECT id, status "
        f"FROM hunts "
        f"WHERE status IN ('signup_open', 'signup_closed', 'draw_complete', 'hunt_open')")
    if results is None or results is False or len(results) > 1:
        return jsonify({"message": "drop_guest internal error 1"}), 500
    if len(results) == 0:
        # this means there is no active hunt. only administrators who provide hunt_id can do anything here
        if 'hunt_id' in data_in and user['level'] == "administrator":
            return drop_guest_aux(data_in['hunt_id'], guest_id)
        else:
            return jsonify({"message": "you aren't authorized to drop a guest right now"}), 400
    else:
        hunt_id = results[0][0]
        hunt_status = results[0][1]
        if user['level'] in ("manager", "owner", "administrator"):
            # you can drop other people's guests
            return drop_guest_aux(hunt_id, guest_id)
        elif hunt_status == "signup_open":
            # members can only drop their own guests and only if status is signup_open
            user_id = get_user_from_guest(data_in['guest_id'])
            if user_id == user['id']:
                return drop_guest_aux(hunt_id, guest_id)
            else:
                return jsonify({"message": f"internal error 10"}), 500
        else:
            return jsonify({"message": "Action cannot be taken by you at this time"}), 400


def drop_guest_aux(hunt_id, guest_id):
    # First, get the participant ID
    results = db.read_custom(
        f"SELECT participants.id, participants.grouping_id FROM participants "
        f"JOIN groupings ON participants.grouping_id=groupings.id "
        f"JOIN guests ON participants.guest_id=guests.id "
        f"WHERE groupings.hunt_id={hunt_id} "
        f"AND guests.id='{guest_id}'"
    )
    if results is None or results is False or len(results) != 1:
        return jsonify({"message": f"Failed to drop of guest {guest_id[:3]} from hunt {hunt_id}"}), 400
    participant_id = results[0][0]
    group_id = results[0][1]

    # Next, delete that row from the participant table
    if not db.update_custom(f"DELETE FROM participants WHERE id='{participant_id}'"):
        return jsonify({"message": f"Failed to drop of guest {guest_id[:3]} from hunt {hunt_id}"}), 400

    cache.delete(f"kilo:{group_id}")
    cache.delete(f"bravo:{hunt_id}")

    return jsonify({"message": f"Successful drop of guest {guest_id} from hunt {hunt_id}"}), 200


@guests_bp.route('/guests/<guest_id>', methods=['DELETE'])
@token_required(admin_only)
def del_row(user, guest_id):
    if db.del_row(table_name, guest_id):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {guest_id} from table {table_name}"}), 400


def get_user_from_guest(guest_id):
    results = db.read_custom(f"SELECT user_id FROM guests WHERE id='{guest_id}'")
    if results is None or results is False:
        print(f"Error in get_user_from_guest 1")
        return None
    if len(results) != 1:
        print(f"Error in get_user_from_guest 2")
        return None
    return results[0][0]
