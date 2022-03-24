from flask import Blueprint, render_template
from flask_login import current_user


blueprint_errors = Blueprint('errors', __name__, template_folder='templates')


titles = {
    401: 'times you can ask,\nbut this page only for authorized users :(',
    404: 'hearts 💜 for you,\nbut this page does not exist ;(',
}


@blueprint_errors.app_errorhandler(Exception)
def ui_error(error):
    try:
        code = int(str(error)[:3])
        logged = False
        if current_user.is_authenticated:
            logged = True

        return render_template('error.html', logged=logged, error_code=code, error_title=titles[code])
    except Exception as e:
        print(e)
        return error
