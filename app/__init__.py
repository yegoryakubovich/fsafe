from flask import Flask
from flask_jwt_extended import JWTManager
from flask_login import LoginManager

from app.errors import blueprint_errors
from app.login import AccountLogin
from app.main import blueprint_main
from app.account import blueprint_account_ui, blueprint_account_api
from app.models import models_create
from app.notifications import bot_run
from app.objects_processing import create_processing
from config import SECRET_KEY, DEBUG


blueprints = [blueprint_main, blueprint_errors, blueprint_account_ui, blueprint_account_api]


def create_app():
    models_create()
    create_processing()
    bot_run()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['DEBUG'] = DEBUG

    JWTManager(app)
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def account_load(account_id):
        return AccountLogin().from_db(account_id)

    [app.register_blueprint(blueprint) for blueprint in blueprints]
    return app
