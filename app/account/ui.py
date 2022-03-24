from datetime import datetime

from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, login_user, current_user, logout_user

from app import AccountLogin
from app.forms import Form
from app.models import Account, Dispatcher, Object, Sensor


blueprint_account_ui = Blueprint('account_ui', __name__, template_folder='templates', url_prefix='/account')


@blueprint_account_ui.route("/", methods=['GET'])
@login_required
def ui_main():
    account = current_user.account
    access_token = account.create_access_token()
    return render_template('account.html', logged=True, auto_refresh=True, access_token=access_token)


@blueprint_account_ui.route("/state", methods=['GET'])
@login_required
def ui_state():
    account = current_user.account
    objects = [o for o in Object.select().where(Object.account == account)]
    return render_template('state.html', auto_refresh=True, logged=True, objects=objects)


@blueprint_account_ui.route("/state/<object_id>", methods=['GET'])
@login_required
def ui_state_sensor(object_id):
    account = current_user.account
    objects = [o for o in Object.select().where(Object.account == account)]
    obj = Object.get_or_none(Object.id == object_id)
    if not obj:
        flash('Error!')
        return redirect('/account/state')
    if obj.account == account:
        sensors = [s for s in Sensor.select().where(Sensor.object == obj)]
        return render_template('state.html', auto_refresh=True, logged=True, objects=objects, obj=obj, sensors=sensors,
                               datetime=datetime)
    else:
        flash('Error!')
        return redirect('/account/state')


@blueprint_account_ui.route("/objects", methods=['POST', 'GET'])
@login_required
def ui_objects():
    form = Form()
    account = current_user.account
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        dispatcher = Dispatcher.get_or_none(Dispatcher.id == form.dispatcher.data)

        # Create object
        obj = Object(name=name, address=address, dispatcher=dispatcher, account=account)
        obj.save()

        flash('Successful object creation')
        return redirect('/account/objects')

    objects = [o for o in Object.select().where(Object.account == account)]
    form.dispatcher.choices = [(dispatcher.id, dispatcher.name) for dispatcher in Dispatcher.select()]
    return render_template('objects.html', logged=True, form=form, objects=objects)


@blueprint_account_ui.route("/object/<object_id>/delete", methods=['GET'])
@login_required
def ui_objects_delete(object_id):
    account = current_user.account
    obj = Object.get_or_none((Object.id == object_id) & (Object.account == account))

    if obj:
        obj.delete_instance()
        flash('Successful object delete')
    else:
        flash('Error!')
    return redirect('/account/objects')


@blueprint_account_ui.route("/sensors", methods=['POST', 'GET'])
@login_required
def ui_sensors():
    form = Form()
    account = current_user.account
    if request.method == 'POST':
        description = request.form['description']
        obj = Object.get_or_none((Object.id == form.object.data) & (Object.account == account))

        # Create sensor
        sens = Sensor(report_last=datetime.now(), object=obj, description=description)
        sens.save()

        flash('Successful sensor creation')
        return redirect('/account/sensors')

    objects = [o for o in Object.select().where(Object.account == account)]
    sensors = []
    for o in objects:
        sensors += [s for s in Sensor.select().where(Sensor.object == o)]

    form.object.choices = [(obj.id, obj.name) for obj in objects]
    return render_template('sensors.html', logged=True, form=form, sensors=sensors)


@blueprint_account_ui.route("/sensor/<sensor_id>/delete", methods=['GET'])
@login_required
def ui_sensors_delete(sensor_id):
    account = current_user.account
    sensor = Sensor.get_or_none((Sensor.id == sensor_id))

    if sensor:
        if sensor.object.account == account:
            sensor.delete_instance()
            flash('Successful sensor delete')
    else:
        flash('Error!')
    return redirect('/account/sensors')


@blueprint_account_ui.route("/registration", methods=['POST', 'GET'])
def ui_registration():
    if request.method == 'POST':
        validation_suc = True

        login = request.form['login']
        password = request.form['password']
        fullname = request.form['fullname']
        phone = request.form['phone'].replace('+', '')

        # Validation
        if Account.get_or_none(Account.login == login):
            validation_suc = False
            flash('Login already exists!')
        if len(login) < 8 or len(password) < 8:
            validation_suc = False
            flash('Login and password length from 8 to 24 characters!')
        if not phone.isdigit():
            validation_suc = False
            flash('Phone number must be in the format "+375291234567"!')
        if len(str(phone)) != 12:
            validation_suc = False
            flash('Phone number must be 12 characters!')

        if not validation_suc:
            return render_template('registration.html',
                                   login=login, password=password, fullname=fullname, phone=phone)

        # Create account
        account = Account(login=login, password=password, fullname=fullname, phone=phone, reg_datetime=datetime.now())
        account.save()
        login_user(AccountLogin().create(account))

        flash('Successful sign up')
        return redirect('/account')

    return render_template('registration.html')


@blueprint_account_ui.route("/login", methods=['POST', 'GET'])
def ui_login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        account = Account.get_or_none((Account.login == login) & (Account.password == password))
        if account:
            login_user(AccountLogin().create(account))
            flash('Successful sign in')
            return redirect('/account')

        flash('Wrong login or password!')
        return render_template('login.html', login=login, password=password)

    return render_template('login.html')


@blueprint_account_ui.route("/logout", methods=['POST', 'GET'])
@login_required
def ui_logout():
    if request.method == 'POST':
        logout_user()
        flash('Successful log out')
        return redirect('/account/login')
    return render_template('logout.html', logged=True)
