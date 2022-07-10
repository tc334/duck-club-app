from flask import Flask
from flask_cors import CORS
from .database.db_mgr import DbManager
from urllib.parse import urlparse
import os


# instance of database
db = DbManager()


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_pyfile(os.path.join('..', 'settings.py'))

    if "SQL_IPADDR" in app.config:
        # environment specifies each connection param separately
        sql_ipaddr = app.config["SQL_IPADDR"]
        sql_port = app.config["SQL_PORT"]
        sql_user = app.config["SQL_UNAME"]
        sql_password = app.config["SQL_PASSWORD"]
        sql_db_name = app.config["SQL_DB_NAME"]
    else:
        url = urlparse(app.config["CLEARDB_DATABASE_URL"])
        sql_ipaddr = url.hostname
        sql_port = url.port
        sql_user = url.username
        sql_password = url.password
        sql_db_name = url.path.lstrip('/')

    db.init_app(
        sql_ipaddr,
        sql_port,
        sql_user,
        sql_password,
        app.config["SQL_ADMIN_EMAIL"]
    )
    db.connect_to_existing(sql_db_name)

    from .views import main
    from . import apis
    app.register_blueprint(main)
    app.register_blueprint(apis.birds_bp)
    app.register_blueprint(apis.users_bp)
    app.register_blueprint(apis.properties_bp)
    app.register_blueprint(apis.ponds_bp)
    app.register_blueprint(apis.hunts_bp)
    app.register_blueprint(apis.groupings_bp)
    app.register_blueprint(apis.harvests_bp)
    app.register_blueprint(apis.stats_bp)

    return app
