from flask_wtf import FlaskForm
from wtforms import SelectField


class Form(FlaskForm):
    dispatcher = SelectField('dispatcher', choices=[])
    object = SelectField('object', choices=[])
