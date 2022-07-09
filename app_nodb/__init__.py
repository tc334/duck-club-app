from flask import Flask


def create_app():
    app = Flask(__name__)

    #  app.config.from_pyfile('..\\settings.py')

    from .views import main
    app.register_blueprint(main)

    return app
