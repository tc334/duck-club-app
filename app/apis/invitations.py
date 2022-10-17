from flask import Blueprint, request, jsonify
from .. import db, cache
from .auth_wraps import token_required, manager_and_above, owner_and_above, all_members, admin_only
from .users import get_id_from_public_id
from .groupings import get_users_in_hunt_aux, print_group

table_name = 'invitations'
invitations_bp = Blueprint(table_name, __name__)


@invitations_bp.route('/invitations', methods=['POST'])
@token_required(all_members)
def add_row(user):
    base_identifier = "file: " + __name__ + "func: " + add_row.__name__

    data_in = request.get_json()

    # Error checking
    if data_in is None:
        return jsonify({"error": "Input json is empty in " + base_identifier}), 400
    # mandatory keys
    mandatory_keys = ('public_id',)
    for key in mandatory_keys:
        if key not in data_in:
            return jsonify({"error": f"Input json missing key '{key}' in " + base_identifier}), 400
    # groups can only be added to active hunt
    results = db.read_custom(f"SELECT id FROM hunts WHERE status = 'signup_open'")
    if results is None or results is False or len(results) > 1:
        return jsonify({"message": "Could not find hunt in proper status to add a group"}), 500
    hunt_id = results[0][0]
    # both inviter and invitee must be signed up for current hunt
    invitee_id = get_id_from_public_id(data_in['public_id'])
    results = db.read_custom(
        f"SELECT participants.id FROM participants "
        f"JOIN users ON participants.user_id=users.id "
        f"JOIN groupings ON participants.grouping_id=groupings.id "
        f"WHERE groupings.hunt_id={hunt_id} "
        f"AND participants.user_id IN ({user['id']},{invitee_id})"
    )
    if results is None or results is False or len(results) != 2:
        print(f"Error in adding invitation. results={results}")
        return jsonify({"message": "Could not verify that both inviter and invitee are in current hunt"}), 400
    # can't invite yourself
    if invitee_id == user['id']:
        return jsonify({"message": "You can't invite yourself"}), 400
    # check for duplicate invitation
    existing = db.read_custom(
        f"SELECT id FROM {table_name} "
        f"WHERE inviter_id='{user['id']}' "
        f"AND invitee_id='{invitee_id}' "
        f"AND hunt_id={hunt_id} "
        f"AND active=true"
    )
    if existing is None or existing is False:
        print(f"DB read error in {base_identifier}")
        return jsonify({"message": "Internal error"}), 500
    if existing:
        return jsonify({"message": "Invitation you requested already exists in " + table_name})
    # check to see if this invitation would put inviter's group over 4 hunters
    inviters_group_size = count_group(user['id'], hunt_id)
    invitees_subgroup_size = count_subgroup(invitee_id, hunt_id)
    if inviters_group_size is None or invitees_subgroup_size is None:
        print(f"Internal error in {base_identifier}. Couldn't count groups")
        return jsonify({"message": "Internal error"}), 500
    if inviters_group_size + invitees_subgroup_size > 4:
        return jsonify({"message": f"Can't send invitation because combined group would be too large"}), 400

    # all checks pass; add invitation to DB
    db_row = {
        "inviter_id": user['id'],
        "invitee_id": invitee_id,
        "hunt_id": hunt_id,
    }
    db.add_row(table_name, db_row)

    # send invitation email
    # TODO

    return jsonify({"message": "Invitation successfully created"}), 200


def count_group(user_id, hunt_id):
    # count all participants in user_1's group
    results = db.read_custom(
        f"SELECT COUNT(*) FROM participants p "
        f"WHERE grouping_id IN "
        f"("
        f"SELECT grouping_id FROM participants "
        f"JOIN groupings ON participants.grouping_id=groupings.id "
        f"WHERE participants.user_id={user_id} "
        f"AND groupings.hunt_id={hunt_id}"
        f")"
    )
    if results is None or results is False:
        return None
    return results[0][0]


def count_subgroup(user_id, hunt_id):
    # counts member & all of their guests
    results = db.read_custom(
        f"SELECT COUNT(*) FROM participants p "
        f"JOIN groupings ON p.grouping_id=groupings.id "
        f"LEFT JOIN guests ON p.guest_id=guests.id "
        f"WHERE groupings.hunt_id={hunt_id} "
        f"AND (p.user_id={user_id} "
        f"OR guests.user_id={user_id})"
    )
    if results is None or results is False:
        return None
    return results[0][0]


@invitations_bp.route('/invitations', methods=['GET'])
@token_required(all_members)
def get_my_invitations(user):
    base_identifier = "file: " + __name__ + "func: " + get_my_invitations.__name__

    # invitations can only be sent/received while status is signup_open
    results = db.read_custom(f"SELECT id FROM hunts WHERE status IN ('signup_open', 'signup_closed', 'draw_complete')")
    if results is None or results is False or len(results) != 1:
        return jsonify({"message": "No hunts are currently in a pre-hunt state"}), 400
    hunt_id = results[0][0]

    # invitations from me
    results = db.read_custom(
        f"SELECT i.id, CONCAT(u.first_name, ' ', u.last_name), i.active, i.cancellation_notes FROM invitations i "
        f"JOIN users u ON i.invitee_id=u.id "
        f"WHERE i.inviter_id={user['id']} "
        f"AND i.hunt_id={hunt_id}"
    )
    if results is None or results is False:
        print(f"Internal error in {base_identifier}")
        return jsonify({"message": "Internal error"}), 500
    names = ["id", "name", "active", "notes"]
    invitations_from = db.format_dict(names, results)

    # invitations to me
    results = db.read_custom(
        f"SELECT i.id, CONCAT(u.first_name, ' ', u.last_name) FROM invitations i "
        f"JOIN users u ON i.inviter_id=u.id "
        f"WHERE i.invitee_id={user['id']} "
        f"AND i.hunt_id={hunt_id} "
        f"AND i.active=true"
    )
    if results is None or results is False:
        print(f"Internal error in {base_identifier}")
        return jsonify({"message": "Internal error"}), 500
    names = ["id", "name"]
    invitations_to = db.format_dict(names, results)

    # now pull all users in this hunt
    users_dict = get_users_in_hunt_aux(hunt_id)
    if users_dict is None:
        return jsonify({"message": "Internal error"}), 500

    out_dict = {
        "invitations_from": invitations_from,
        "invitations_to": invitations_to,
        "users": users_dict
    }

    return jsonify({"data": out_dict}), 200


@invitations_bp.route('/invitations/rescind/<invitation_id>', methods=['PUT'])
@token_required(all_members)
def rescind_invite(user, invitation_id):
    base_identifier = "file: " + __name__ + "func: " + rescind_invite.__name__
    # error check

    # invitations can only be rescinded when hunt status is signup_open
    results = db.read_custom(f"SELECT id FROM hunts WHERE status = 'signup_open'")
    if results is None or results is False or len(results) != 1:
        return jsonify({"message": "Invitations can only be managed when hunt status is signup_open"}), 400
    hunt_id = results[0][0]

    # members can only rescind an invite they sent
    results = db.read_custom(
        f"SELECT inviter_id FROM invitations WHERE id='{invitation_id}'"
    )
    if results is None or results is False:
        print(f"internal error in {base_identifier}")
        return jsonify({"message": "Internal error"}), 500
    if len(results) != 1:
        return jsonify({"message": "Invitation you are trying to rescind was not found"}), 400
    inviter_id = results[0][0]
    if user['level'] == 'member' and user['id'] != inviter_id:
        return jsonify({"message": "You can only rescind an invite you sent"}), 400

    update_dict = {
        "active": False,
        "cancellation_notes": "Rescinded by inviter"
    }
    db.update_row(table_name, invitation_id, update_dict)

    return jsonify({"message": "Invitation successfully rescinded"}), 200


@invitations_bp.route('/invitations/reject/<invitation_id>', methods=['PUT'])
@token_required(all_members)
def reject_invite(user, invitation_id):
    base_identifier = "file: " + __name__ + "func: " + reject_invite.__name__
    # error check

    # invitations can only be rejected when hunt status is signup_open
    results = db.read_custom(f"SELECT id FROM hunts WHERE status = 'signup_open'")
    if results is None or results is False or len(results) != 1:
        return jsonify({"message": "Invitations can only be managed when hunt status is signup_open"}), 400
    hunt_id = results[0][0]

    # members can only rescind an active invite sent to them
    results = db.read_custom(
        f"SELECT invitee_id, active FROM invitations WHERE id='{invitation_id}'"
    )
    if results is None or results is False:
        print(f"internal error in {base_identifier}")
        return jsonify({"message": "Internal error"}), 500
    if len(results) != 1:
        return jsonify({"message": "Invitation you are trying to reject was not found"}), 400
    invitee_id = results[0][0]
    active = results[0][1]
    if not active:
        return jsonify({"message": "This invitation is not currently active"}), 400
    if user['level'] == 'member' and user['id'] != invitee_id:
        return jsonify({"message": "You can only reject an invite you sent"}), 400

    update_dict = {
        "active": False,
        "cancellation_notes": "Rejected by invitee"
    }
    db.update_row(table_name, invitation_id, update_dict)

    return jsonify({"message": "Invitation successfully rejected"}), 200


@invitations_bp.route('/invitations/accept/<invitation_id>', methods=['PUT'])
@token_required(all_members)
def accept_invite(user, invitation_id):
    return accept_invite_aux(user['id'], invitation_id)


def accept_invite_aux(user_id, invitation_id):
    # invitations can only be accepted when hunt status is signup_open
    results = db.read_custom(f"SELECT id FROM hunts WHERE status = 'signup_open'")
    if results is None or results is False or len(results) != 1:
        return jsonify({"message": "Invitations can only be accepted when hunt status is signup_open"}), 400
    hunt_id = results[0][0]

    # members can only accept an active invite sent to them
    results = db.read_custom(
        f"SELECT invitee_id, active, inviter_id FROM invitations WHERE id='{invitation_id}'"
    )
    if results is None or results is False:
        print(f"internal error in accept_invite_aux")
        return jsonify({"message": "Internal error"}), 500
    if len(results) != 1:
        return jsonify({"message": "Invitation you are trying to accept was not found"}), 400
    invitee_id = results[0][0]
    active = results[0][1]
    inviter_id = results[0][2]
    if not active:
        return jsonify({"message": "This invitation is no longer active"}), 400
    if user_id != invitee_id:
        print(f"Error in accept_invite_aux: user_id {user_id} does not match invitee_id {invitee_id}")
        return jsonify({"message": f"User ID does not match Invitee ID"}), 400

    # recheck that both invitee and inviter are both STILL part of this hunt
    results = db.read_custom(
        f"SELECT participants.id FROM participants "
        f"JOIN users ON participants.user_id=users.id "
        f"JOIN groupings ON participants.grouping_id=groupings.id "
        f"WHERE groupings.hunt_id={hunt_id} "
        f"AND participants.user_id IN ({inviter_id},{invitee_id})"
    )
    if results is None or results is False or len(results) != 2:
        print(f"Error in accepting invitation. results={results}")
        return jsonify({"message": "Could not verify that both inviter and invitee are still in current hunt"}), 400

    # recheck group capacity
    inviters_group_size = count_group(inviter_id, hunt_id)
    invitees_subgroup_size = count_subgroup(invitee_id, hunt_id)
    if inviters_group_size is None or invitees_subgroup_size is None:
        print(f"Internal error in accept_invite_aux. Couldn't count groups")
        return jsonify({"message": "Internal error"}), 500
    if inviters_group_size + invitees_subgroup_size > 4:
        print(f"Error. Invitation cannot be accepted b/c combined group too large. inviter={inviters_group_size}, invitee{invitees_subgroup_size}")
        return jsonify({"message": f"Can't send invitation because combined group would be too large"}), 400

    # move the invitee & their guests to the inviter's group
    group_id_inviter = get_group_id(hunt_id, inviter_id)
    group_id_invitee = get_group_id(hunt_id, invitee_id)
    print(f"BEFORE GROUP ACTION 'accept_invite'. group1_id={group_id_inviter}. group2_id={group_id_invitee}")
    print_group(group_id_inviter)
    print_group(group_id_invitee)

    # move member
    db.update_custom(
        f"UPDATE participants "
        f"SET grouping_id={group_id_inviter} "
        f"WHERE grouping_id={group_id_invitee} "
        f"AND user_id={invitee_id}")

    # move member's guests
    db.update_custom(
        f"UPDATE participants "
        f"SET grouping_id={group_id_inviter} "
        f"WHERE grouping_id={group_id_invitee} "
        f"AND guest_id IN "
        f"(SELECT id FROM guests WHERE user_id={invitee_id})")

    # delete the second group if and only if it was emptied by the previous operation
    count_after = db.read_custom(f"SELECT COUNT(*) FROM participants WHERE grouping_id={group_id_invitee}")[0][0]
    if count_after < 1:
        db.del_row("groupings", group_id_invitee)

    cache.delete("bravo")
    cache.delete(f"golf:{hunt_id}")
    cache.delete(f"golf:{hunt_id}")
    cache.delete(f"hotel:{group_id_inviter}")
    cache.delete(f"hotel:{group_id_invitee}")
    cache.delete(f"kilo:{group_id_inviter}")
    cache.delete(f"kilo:{group_id_invitee}")
    cache.delete(f"romeo:{group_id_inviter}")
    cache.delete(f"romeo:{group_id_invitee}")

    print(f"AFTER GROUP ACTION 'accept_invitation'. group1_id={group_id_inviter}. group2_id={group_id_invitee}")
    print_group(group_id_inviter)
    print_group(group_id_invitee)

    # close out the invitation
    update_dict = {
        "active": False,
        "cancellation_notes": "Accepted by invitee"
    }
    db.update_row(table_name, invitation_id, update_dict)

    return jsonify({"message": "Invitation successfully accepted"}), 200


def get_group_id(hunt_id, user_id):
    results = db.read_custom(
        f"SELECT g.id FROM groupings g "
        f"JOIN participants ON participants.grouping_id=g.id "
        f"WHERE g.hunt_id={hunt_id} "
        f"AND participants.user_id={user_id}"
    )
    if results is None or results is False or len(results) != 1:
        print(f"Error in get_group_id. results={results}")
        return None
    return results[0][0]
