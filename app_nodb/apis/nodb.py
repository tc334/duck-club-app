from flask import Blueprint, request, jsonify, current_app, make_response

nodb_bp = Blueprint('nodb', __name__)


@nodb_bp.route('/login')
def login():
    return jsonify({'message': 'This is a response from the login route'}), 201


@nodb_bp.route('/signup', methods=['POST'])
def signup():
    data_in = request.get_json()  # expecting keys: email, password, first_name, last_name, combo

    print(f"data_in={data_in}")

    return jsonify({'message': f'This is a response from the signup route**{current_app.config["CLEARDB_DATABASE_URL"]}'}), 201
