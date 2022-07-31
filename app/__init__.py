from flask import Flask
from flask_cors import CORS
from .database.db_mgr import DbManager
from .cache.redis_manager import RedisManager
from urllib.parse import urlparse
import os


# instance of databases
db = DbManager()
cache = RedisManager()


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_pyfile(os.path.join('..', 'settings.py'))

    if app.config['ENV'] == "development":
        # environment specifies each connection param separately
        sql_ipaddr = app.config["SQL_IPADDR"]
        sql_port = app.config["SQL_PORT"]
        sql_user = app.config["SQL_UNAME"]
        sql_password = app.config["SQL_PASSWORD"]
        sql_db_name = app.config["SQL_DB_NAME"]

        redis_ipaddr = app.config["REDIS_IPADDR"]
        redis_port = app.config["REDIS_PORT"]
    else:
        url = urlparse(app.config["CLEARDB_DATABASE_URL"])
        sql_ipaddr = url.hostname
        sql_port = url.port
        sql_user = url.username
        sql_password = url.password
        sql_db_name = url.path.lstrip('/')

        url = urlparse(app.config["REDIS_URL"])
        redis_ipaddr = url.hostname
        redis_port = url.port
        redis_user = url.username
        redis_password = url.password

    cache.init_app(
        redis_ipaddr,
        redis_port,
        "tbd",
        "tbd"
    )

    db.init_app(
        sql_ipaddr,
        sql_port,
        sql_user,
        sql_password,
        app.config["SQL_ADMIN_EMAIL"],
        db_name=sql_db_name,
        cache=cache
    )

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
