import datetime

from flask import Blueprint, request, jsonify, current_app, make_response, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt

from .. import db, cache
from .auth_wraps import token_required, admin_only, owner_and_above, all_members, manager_and_above
from app.user_aux.token import generate_confirmation_token
from app.user_aux.email import send_email

users_bp = Blueprint('users', __name__)
table_name = 'users'


@users_bp.route('/login')
def login():
    auth = request.authorization
    if auth and auth.username and auth.password:
        results = db.read_custom(
            f"SELECT public_id, password_hash, level, confirmed, status "
            f"FROM {table_name} "
            f"WHERE email = '{auth.username.lower()}' "
            f"LIMIT 1")
        if results and len(results) == 1:
            user = db.sql_to_dict(results, names=["public_id", "password_hash", "level", "confirmed", "status"])
            if check_password_hash(user["password_hash"], auth.password):
                if user["confirmed"]:
                    if user["status"] == "active":

                        # login successful, send back a JWT
                        token = jwt.encode({
                            "user": user["public_id"],
                            "level": user["level"],
                            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
                            "token_id": str(uuid.uuid4())
                        }, current_app.config["SECRET_KEY"])

                        return jsonify({'token': token})

                    else:
                        return make_response("Your account has been deactivated", 401,
                                             {"WWW-Authenticate": "Basic realm='Login Required'"})
                else:
                    return make_response("Email address not verified. If you just signed up, check your inbox", 401,
                                         {"WWW-Authenticate": "Basic realm='Login Required'"})
            else:
                return make_response("Could not verify password", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})
        else:
            return make_response("Could not find user with that email", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})
    else:
        return make_response("Login information missing", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})


@users_bp.route('/signup', methods=['POST'])
def signup():
    data_in = request.get_json()  # expecting keys: email, password, first_name, last_name, combo

    # Error checking
    if data_in is None:
        return jsonify({'message': 'No data received'}), 400
    if 'first_name' not in data_in or len(data_in['first_name']) < 2:
        return jsonify({'message': 'First name missing'}), 400
    if 'last_name' not in data_in or len(data_in['last_name']) < 2:
        return jsonify({'message': 'Last name missing'}), 400
    if 'email' not in data_in or len(data_in['email']) < 2:
        return jsonify({'message': 'Email missing'}), 400
    if 'password' not in data_in or len(data_in['password']) < 8:
        return jsonify({'message': 'Password too short'}), 400
    if 'combo' not in data_in or data_in['combo'] != current_app.config["SIGNUP_CODE"]:
        return jsonify({'message': 'Wrong access code'}), 400

    # check for duplicates
    existing = db.read_custom(f"SELECT id FROM {table_name} WHERE email = '{data_in['email'].lower()}'")
    if existing is None:
        return jsonify({"message": "Internal error"}), 500
    if existing:
        return jsonify({"message": "Entry " + data_in["email"] + " already exists in " + table_name}), 400

    # append this information to what the user put in
    data_in['public_id'] = str(uuid.uuid4())
    data_in['password_hash'] = generate_password_hash(data_in['password'], method='sha256')
    data_in['registered_on'] = datetime.datetime.now()

    # make email all lower case since they aren't case sensitive
    data_in['email'] = data_in['email'].lower()

    id = db.add_row(table_name, data_in)
    cache.delete("charlie")

    # send email to user for them to verify their email address
    send_confirmation(data_in["email"])

    return jsonify({'message': data_in['first_name'] + ' successfully added. Your email needs to be verified before '
                                                       'you can log in. Check your inbox for a '
                                                       'verification link'}), 201


def send_confirmation(email):
    # send email to user for them to verify their email address
    token = generate_confirmation_token(email)
    confirm_url = url_for('main.confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email to the Duck Club App"
    send_email(email, subject, html)
    print(f"Just sent confirmation email to {email}")


@users_bp.route('/password_reset_request', methods=['POST'])
def password_reset_request():
    data_in = request.get_json()  # expecting keys: email
    # Error checking
    if data_in is None:
        return jsonify({'message': 'No data received'}), 400
    if 'email' not in data_in:
        return jsonify({'message': 'Email missing'}), 400
    email = data_in["email"].lower()

    # first check to see if this email address exists
    results = db.read_custom(
        f"SELECT id "
        f"FROM users "
        f"WHERE email = '{email}'")
    if not results or len(results) != 1:
        # email not found in users table. perhaps fraud? take no further action
        print(f"Password reset request failed. Didn't find {email} in DB")
    else:
        # send email to user for them to reset their password
        token = generate_confirmation_token(email)
        reset_url = url_for('main.reset_password', token=token, _external=True)
        html = render_template('password_reset_email.html', reset_url=reset_url)
        subject = "Password reset to the Duck Club App"
        send_email(email, subject, html)
        print(f"Just sent password reset email to {email}")

    # don't want to indicate to malicious user if email is in our list or not, so same reply for all
    return jsonify({"message": "Request received"}), 200


@users_bp.route('/password_reset', methods=['POST'])
def password_reset():
    public_id = request.form['public_id']
    password = request.form['password']

    if public_id is None or password is None:
        return jsonify({'message': 'No data received'}), 400

    new_dict = {
        'password_hash': generate_password_hash(password, method='sha256')
    }

    if db.update_row(table_name, public_id, new_dict, "public_id"):
        return render_template('password_reset_success.html'), 200
    else:
        return "Password update failed", 400


@users_bp.route('/users', methods=['POST'])
@token_required(owner_and_above)
def manual_add(user):
    data_in = request.get_json()  # expecting keys: email, first_name, last_name

    # Error checking
    if data_in is None:
        return jsonify({'message': 'No data received'}), 400
    if 'first_name' not in data_in or len(data_in['first_name']) < 2:
        return jsonify({'message': 'First name missing'}), 400
    if 'last_name' not in data_in or len(data_in['last_name']) < 2:
        return jsonify({'message': 'Last name missing'}), 400
    if 'email' not in data_in or len(data_in['email']) < 2:
        return jsonify({'message': 'Email missing'}), 400

    # check for duplicates
    existing = db.read_custom(f"SELECT id FROM {table_name} WHERE email = '{data_in['email'].lower()}'")
    if existing is None:
        return jsonify({"error": "Internal error"}), 400
    if existing:
        return jsonify({"error": "Entry " + data_in["email"] + " already exists in " + table_name})

    # append this information to what the user put in
    data_in['public_id'] = str(uuid.uuid4())
    # here a user has been created manually, so no password is provided. Just make one up
    data_in['password_hash'] = generate_password_hash('password', method='sha256')
    data_in['registered_on'] = datetime.datetime.now()

    # email not case sensitive
    data_in['email'] = data_in['email'].lower()

    id = db.add_row(table_name, data_in)
    cache.delete("charlie")

    return jsonify({'message': data_in['first_name'] + ' successfully added as a user'}), 201


@users_bp.route('/users', methods=['GET'])
@token_required(owner_and_above)
def get_all_rows(user):

    # this SQL postfix will sort the results by member level
    pf = "ORDER BY CASE " \
         "WHEN level = 'administrator' then 1 " \
         "WHEN level = 'owner' then 2 " \
         "WHEN level = 'manager' then 3 " \
         "WHEN level = 'member' then 4 " \
         "END ASC"
    results = db.read_all(table_name, post_fix=pf)

    return jsonify({"users": results}), 200


@users_bp.route('/users/active', methods=['GET'])
@token_required(manager_and_above)
def get_all_active(user):
    results = db.read_custom(
        f"SELECT public_id, first_name, last_name "
        f"FROM {table_name} "
        f"WHERE status = 'active' "
        f"ORDER BY last_name")

    if results:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["public_id", "first_name", "last_name"]
        results_dict = db.format_dict(names_all, results)
        return jsonify({"users": results_dict}), 200
    else:
        return jsonify({"error": f"unknown error trying to read harvest"}), 400


@users_bp.route('/users/all_allowable', methods=['GET'])
@token_required(all_members)
def get_all_allowable(user):
    # If manager or above, gets all members
    # If member, only gets yourself

    if user['level'] == "member":
        results = db.read_custom(
            f"SELECT public_id, first_name, last_name "
            f"FROM {table_name} "
            f"WHERE id={user['id']}"
            f"ORDER BY last_name")
    else:
        results = db.read_custom(
            f"SELECT public_id, first_name, last_name "
            f"FROM {table_name} "
            f"ORDER BY last_name")

    if results:
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        names_all = ["public_id", "first_name", "last_name"]
        results_dict = db.format_dict(names_all, results)
        return jsonify({"users": results_dict}), 200
    else:
        return jsonify({"message": f"unknown error trying to read users"}), 400


@users_bp.route('/users/<public_id>', methods=['GET'])
@token_required(all_members)
def get_one_row(user, public_id):
    # members can only read their own info. owners can read anything
    if not (user["level"] == "owner" or
            user["level"] == "administrator" or
            user["public_id"] == public_id):
        return jsonify({"error": f"You are not allowed to make this change to {table_name}"}), 400

    result = db.read_custom(f"SELECT * FROM {table_name} WHERE public_id='{public_id}'")

    if result and len(result) == 1:
        return jsonify({"user": db.sql_to_dict(result, table_name=table_name)}), 200
    else:
        return jsonify({"error": f"Could not find id {public_id} in table {table_name}"}), 400


@users_bp.route('/users/<public_id>', methods=['PUT'])
@token_required(all_members)
def update_row(user, public_id):
    data_in = request.get_json()

    # members can only change their own first_name, last_name, email. owners can change anything
    white_keys = ["first_name", "last_name", "email"]
    b_non_white_keys = True if len(set(data_in.keys()) - set(white_keys)) == 0 else False
    if not (user["level"] == "owner" or
            user["level"] == "administrator" or
            user["public_id"] == public_id and b_non_white_keys):
        return jsonify({"error": f"You are not allowed to make this change to {table_name}"}), 403

    # check for duplicate email if attempting to change email
    if 'email' in data_in:
        # email not case sensitive
        data_in['email'] = data_in['email'].lower()
        existing = db.read_custom(f"SELECT id FROM {table_name} WHERE email = '{data_in['email']}' AND public_id != '{public_id}'")
        if existing is None:
            return jsonify({"error": f"Internal error in {__name__}:update_row()"}), 500
        if existing:
            return jsonify({"error": "Entry " + data_in["email"].lower() + " already exists in " + table_name})

    if db.update_row(table_name, public_id, data_in, "public_id"):
        cache.delete("charlie")
        cache.delete(f"qubec:{public_id}")
        return jsonify({'message': f'Successful update of {table_name}'}), 200
    else:
        return jsonify({"error": f"Unable to update table {table_name}"}), 400


@users_bp.route('/users/<public_id>', methods=['DELETE'])
@token_required(admin_only)
def del_row(user, public_id):
    if db.del_row(table_name, public_id, "public_id"):
        cache.delete("charlie")
        cache.delete(f"qubec:{public_id}")
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {public_id} from table {table_name}"}), 400


def get_id_from_public_id(public_id):
    results = db.read_custom(
        f"SELECT id FROM users WHERE public_id='{public_id}'"
    )
    if results is None or len(results) != 1:
        return None
    else:
        return results[0][0]


@users_bp.route('/users/reconfirm/<public_id>', methods=['PUT'])
@token_required(owner_and_above)
def reconfirm_user(user, public_id):
    # first, get email based on public id
    results = db.read_custom(
        f"SELECT email FROM users WHERE public_id='{public_id}'"
    )
    if results is None or results is False or len(results) != 1:
        print(results)
        print(public_id)
        return jsonify({"message": "internal error in reconfirm user"})
    email = results[0][0]

    send_confirmation(email)

    return jsonify({"message": f"New confirmation email sent to {email}"}), 200
