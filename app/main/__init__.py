from flask import Blueprint, render_template
from flask_login import current_user

blueprint_main = Blueprint('main', __name__, template_folder='templates')


@blueprint_main.route("/")
def home():
    return render_template('main.html')


@blueprint_main.route("/terms")
def terms():
    logged = False
    if current_user.is_authenticated:
        logged = True

    return render_template('terms.html', logged=logged)
