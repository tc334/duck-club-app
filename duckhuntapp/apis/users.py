from flask import Blueprint, request, jsonify, current_app, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
import uuid
import jwt
import datetime
from .auth_wraps import token_required, admin_only, owner_and_above, all_members

users_bp = Blueprint('users', __name__)
table_name = 'users'


@users_bp.route('/login')
def login():
    auth = request.authorization
    if auth and auth.username and auth.password:
        results = db.read_custom(f"SELECT public_id, password_hash, level FROM {table_name} WHERE email = '{auth.username}' LIMIT 1")
        if results and len(results) == 1:
            user = db.sql_to_dict(results, names=["public_id", "password_hash", "level"])
            if check_password_hash(user["password_hash"], auth.password):

                # login successful, send back a JWT
                token = jwt.encode({
                    "user": user["public_id"],
                    "level": user["level"],
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3),
                    "token_id": str(uuid.uuid4())
                }, current_app.config["SECRET_KEY"])

                return jsonify({'token': token})

    return make_response("Could not verify password", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})


@users_bp.route('/signup', methods=['POST'])
def signup():
    data_in = request.get_json()  # expecting keys: email, password, first_name, last_name, combo

    # Error checking
    if data_in is None:
        return jsonify({'error': 'No data received'}), 400
    if 'first_name' not in data_in or len(data_in['first_name']) < 2:
        return jsonify({'error': 'First name missing'}), 400
    if 'last_name' not in data_in or len(data_in['last_name']) < 2:
        return jsonify({'error': 'Last name missing'}), 400
    if 'email' not in data_in or len(data_in['email']) < 2:
        return jsonify({'error': 'Email missing'}), 400
    if 'password' not in data_in or len(data_in['password']) < 8:
        return jsonify({'error': 'Password too short'}), 400
    if 'combo' not in data_in or data_in['combo'] != current_app.config["SIGNUP_CODE"]:
        return jsonify({'error': 'Wrong access code'}), 400
    # check for duplicates
    existing = db.read_custom(f"SELECT id FROM {table_name} WHERE email = '{data_in['email']}'")
    if existing is None:
        return jsonify({"error": "Internal error"}), 400
    if existing:
        return jsonify({"error": "Entry " + data_in["email"] + " already exists in " + table_name})

    # append this information to what the user put in
    data_in['public_id'] = str(uuid.uuid4())
    data_in['password_hash'] = generate_password_hash(data_in['password'], method='sha256')

    db.add_row(table_name, data_in)

    return jsonify({'message': data_in['first_name'] + ' successfully added as a user'}), 201


@users_bp.route('/users', methods=['GET'])
@token_required(owner_and_above)
def get_all_rows(user):
    print(f"user={user}")
    results = db.read_all(table_name)
    return jsonify({"users": results}), 200


@users_bp.route('/users/<public_id>', methods=['GET'])
@token_required(owner_and_above)
def get_one_row(user, public_id):
    result = db.read_custom(f"SELECT * FROM {table_name} WHERE public_id='{public_id}'")

    if result and len(result) == 1:
        return jsonify({"user": db.sql_to_dict(result, table_name=table_name)}), 200
    else:
        return jsonify({"error": f"Could not find id {public_id} in table {table_name}"}), 400


@users_bp.route('/users/<public_id>', methods=['PUT'])
@token_required(owner_and_above)
def update_row(user, public_id):
    data_in = request.get_json()

    # check for duplicates
    existing = db.read_custom(f"SELECT id FROM {table_name} WHERE email = '{data_in['email']}' AND id != {public_id}")
    if existing is None:
        return jsonify({"error": "Internal error"}), 400
    if existing:
        return jsonify({"error": "Entry " + data_in["email"] + " already exists in " + table_name})

    if db.update_row(table_name, public_id, data_in, "public_id"):
        return jsonify({'message': f'Successful update of {table_name}'}), 200
    else:
        return jsonify({"error": f"Unable to update table {table_name}"}), 400


@users_bp.route('/users/<public_id>', methods=['DELETE'])
@token_required(owner_and_above)
def del_row(user, public_id):
    if db.del_row(table_name, public_id, "public_id"):
        return jsonify({'message': 'Successful removal'}), 200
    else:
        return jsonify({"error": f"Unable to remove id {public_id} from table {table_name}"}), 400
