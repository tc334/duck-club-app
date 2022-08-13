import datetime

from flask import Blueprint, render_template, url_for

from app.user_aux.token import confirm_token
from . import db

main = Blueprint('main', __name__)


@main.route('/')
def main_index():
    return "Hello World, from the real app!"


@main.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        # flash('The confirmation link is invalid or has expired.', 'danger')
        return 'The confirmation link is invalid or has expired.'

    results = db.read_custom(
        f"SELECT id, confirmed "
        f"FROM users "
        f"WHERE email = '{email}'")
    if results and len(results) == 1:
        user = db.sql_to_dict(results, names=["id", "confirmed"])
    else:
        # flash('Internal error', 'error')
        return "Lookup of the user's email failed"

    if user["confirmed"]:
        return "Account already confirmed. Please login"
    else:
        user_new = {
            "confirmed": True,
            "confirmed_on": datetime.datetime.now(),
            "status": "active"
        }
        db.update_row("users", user["id"], user_new)

    return render_template('activation_success.html')


@main.route('/reset_password/<token>')
def reset_password(token):
    try:
        email = confirm_token(token)
    except:
        return 'The password reset link is invalid or has expired.'

    results = db.read_custom(
        f"SELECT public_id "
        f"FROM users "
        f"WHERE email = '{email}'")
    if results and len(results) == 1:
        pid = results[0][0]
    else:
        return "Lookup of the user's email failed"

    return render_template('password_reset_page.html', public_id=pid)
