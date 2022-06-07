from flask import Flask
from flask_cors import CORS
from .database.db_mgr import DbManager

# instance of database
db = DbManager()


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_pyfile('settings.py')

    db.init_app(
        app.config["SQL_IPADDR"],
        app.config["SQL_PORT"],
        app.config["SQL_UNAME"],
        app.config["SQL_PASSWORD"]
    )
    db.connect_to_existing(app.config["SQL_DB_NAME"])

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

    return app
