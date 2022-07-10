from flask import Flask
import os


def create_app():
    app = Flask(__name__)

    filename = os.path.join('..', 'settings.py')
    print(f"***filename***{filename}")
    app.config.from_pyfile(filename)

    from .views import main
    from . import apis
    app.register_blueprint(main)
    app.register_blueprint(apis.nodb_bp)

    return app
