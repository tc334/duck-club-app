from flask import Blueprint, current_app
from . import db
from .apis.auth_wraps import token_required, admin_only, owner_and_above, all_members

main = Blueprint('main', __name__)


@main.route('/')
def main_index():
    return "Blueprint Hello World!" + current_app.config["SIGNUP_CODE"]


@main.route('/nuke_db')
def nuke():
    db.nuke_and_rebuild(current_app.config["SQL_DB_NAME"], current_app.config["SQL_ADMIN_EMAIL"])
    return "Database nuked!"


@main.route('/unprotected')
def unprotected():
    return "Anyone can access"


@main.route('/protected')
@token_required(all_members)
def protected(user):
    return "Special users only!" + user["level"]
