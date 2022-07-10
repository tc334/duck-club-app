from flask import Blueprint, request, jsonify, current_app, make_response
from urllib.parse import urlparse

nodb_bp = Blueprint('nodb', __name__)


@nodb_bp.route('/login')
def login():
    return jsonify({'message': 'This is a response from the login route'}), 201


@nodb_bp.route('/signup', methods=['POST'])
def signup():
    data_in = request.get_json()  # expecting keys: email, password, first_name, last_name, combo

    print(f"data_in={data_in}")

    url = urlparse(current_app.config["CLEARDB_DATABASE_URL"])

    return jsonify({
        'message': f'This is a response from the signup route',
        'full': current_app.config["CLEARDB_DATABASE_URL"],
        'scheme': url.scheme,
        'hostname': url.hostname,
        'username': url.username,
        'password': url.password,
        'port': url.port,
        'database_name': url.path.lstrip('/')
    }), 201
