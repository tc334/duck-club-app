from flask import Blueprint, current_app
from . import db
from .apis.auth_wraps import token_required, admin_only

main = Blueprint('main', __name__)


@main.route('/')
def main_index():
    return "Hello World, from the real app!"
