from functools import wraps
from flask import request, jsonify, current_app
import jwt
from .. import db, cache


def token_required(member_level_test):
    def actual_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'x-access-token' in request.headers:
                token = request.headers['x-access-token']
                if token:
                    try:
                        # print("Alpha")
                        db.get_conn()
                        jwt_data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                        current_user = cache.get(f"qubec:{jwt_data['user']}")
                        if not current_user:
                            # cache miss, go to db
                            results = db.read_custom(f"SELECT id, level, public_id FROM users WHERE public_id='{jwt_data['user']}' LIMIT 1")
                            # print(f"results={results}")
                            if results and len(results) == 1:
                                names = ["id", "level", "public_id"]
                                current_user = db.format_dict(names, results)[0]
                                # cache update
                                cache.add(f"qubec:{jwt_data['user']}", current_user, 24*60*60)
                            else:
                                # print("Foxtrot")
                                db.release_conn()
                                return jsonify({'error': 'User not found'}), 403
                        # print("Bravo")
                        if member_level_test(current_user["level"]):
                            print(f"wrapped function: {f}")
                            ret_val = f(current_user, *args, **kwargs)
                            # print(f"Charlie 2")
                            db.release_conn()
                            # print("Delta")
                            return ret_val
                        else:
                            # print("Echo")
                            db.release_conn()
                            return jsonify({'error': 'User not authorized'}), 403
                    except jwt.exceptions.InvalidTokenError as e:
                        # print("Golf")
                        db.release_conn()
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
