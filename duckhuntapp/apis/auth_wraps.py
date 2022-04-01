from functools import wraps
from flask import request, jsonify, current_app
import jwt
from .. import db


def token_required(member_level_test):
    def actual_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'x-access-token' in request.headers:
                token = request.headers['x-access-token']
                if token:
                    try:
                        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                        results = db.read_custom(f"SELECT level FROM users WHERE public_id='{data['user']}' LIMIT 1")
                        if results and len(results) == 1:
                            current_user = db.sql_to_dict(results, names=["level"])
                            print(f"Alpha:{current_user}")
                            if member_level_test(current_user["level"]):
                                return f(current_user, *args, **kwargs)
                            else:
                                return jsonify({'error': 'User not authorized'}), 403
                    except jwt.exceptions.InvalidTokenError as e:
                        return jsonify({'error': 'Token is invalid! ' + repr(e)}), 401
            return jsonify({'error': 'Token is missing'}), 401
        return wrapper
    return actual_decorator


def admin_only(level):
    if level == "administrator":
        return True
    else:
        return False


def owner_and_above(level):
    if level == "owner" or level == "administrator":
        return True
    else:
        return False


def manager_and_above(level):
    if level == "manager" or level == "owner" or level == "administrator":
        return True
    else:
        return False


def all_members(level):
    return True
