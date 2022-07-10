from flask import Blueprint, request, jsonify, current_app, make_response

nodb_bp = Blueprint('nodb', __name__)


@nodb_bp.route('/login')
def login():
    return make_response("Could not verify password", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})


@nodb_bp.route('/signup', methods=['POST'])
def signup():
    data_in = request.get_json()  # expecting keys: email, password, first_name, last_name, combo

    print(f"data_in={data_in}")

    return jsonify({'message': 'This is a response from the signup route'}), 201
