from flask import Blueprint, current_app

main = Blueprint('main', __name__)


@main.route('/')
def main_index():
    return "Blueprint Hello World!" + current_app.config["SECRET_KEY"]
