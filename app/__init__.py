from flask import Flask
from flask_cors import CORS
from .database.db_mgr_cockroach import DbManagerCockroach
from .cache.redis_manager import RedisManager
from urllib.parse import urlparse
import os


# instance of databases
db = DbManagerCockroach()
cache = RedisManager()


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_pyfile(os.path.join('..', 'settings.py'))

    if app.config['ENV'] == "development":
        redis_ipaddr = app.config["REDIS_IPADDR"]
        redis_port = app.config["REDIS_PORT"]
        redis_user = None
        redis_password = None
    else:
        url = urlparse(app.config["REDIS_URL"])
        redis_ipaddr = url.hostname
        redis_port = url.port
        redis_user = url.username
        redis_password = url.password

    cache.init_app(
        redis_ipaddr,
        redis_port,
        redis_user,
        redis_password
    )

    db.init_app(
        app.config["COCKROACH_URL"],
        app.config["ADMIN_EMAIL"],
        cache=cache
    )

    db.select_db(db_name=app.config["DB_NAME"])

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
