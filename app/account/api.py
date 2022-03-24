from datetime import datetime

from flask import Blueprint
from flask_apispec import use_kwargs, marshal_with
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import Account, Sensor, Report, SensorStatusJob, SensorStatusSituation
from app.schemas import AccountSchema, ReportSchema


blueprint_account_api = Blueprint('account_api', __name__, template_folder='templates', url_prefix='/api/account')


@blueprint_account_api.route("/registration", methods=['POST'])
@marshal_with(AccountSchema)
@use_kwargs(AccountSchema())
def api_registration(**kwargs):
    login = kwargs.get("login")
    password = kwargs.get("password")
    fullname = kwargs.get("fullname")
    phone = kwargs.get("phone")

    # Validation
    if Account.get_or_none(Account.login == login):
        return {"message": "Login already exists"}, 422
    if len(login) < 8 or len(password) < 8:
        return {"message": "Login and password length from 8 to 24 characters"}, 422
    if len(str(phone)) != 9:
        return {"message": "Phone number must be 9 characters"}, 422

    # Create account
    account = Account(login=login, password=password, fullname=fullname, phone=phone, reg_datetime=datetime.now())
    account.save()
    access_token = account.create_access_token()
    return {"access_token": access_token}


@blueprint_account_api.route("/login", methods=['POST'])
@marshal_with(AccountSchema)
@use_kwargs(AccountSchema(only=("login", "password")))
def api_login(**kwargs):
    login = kwargs.get("login")
    password = kwargs.get("password")
    account = Account.get_or_none((Account.login == login) & (Account.password == password))
    if account:
        access_token = account.create_access_token()
        return {"access_token": access_token}
    return {"message": "Wrong login or password"}, 422


@blueprint_account_api.route("/object/report", methods=['POST'])
@marshal_with(AccountSchema)
@use_kwargs(ReportSchema())
@jwt_required()
def api_object_report(**kwargs):
    account_id = get_jwt_identity()
    account = Account.get_or_none(Account.id == account_id)

    reports = kwargs.get('reports')

    for report in reports:
        try:
            sensor = Sensor.get_or_none(Sensor.id == report['sensor_id'])
            battery = int(report['battery'])
            is_smoke = bool(report['is_smoke'])
            is_fire = bool(report['is_fire'])
            broken = bool(report['broken'])
        except KeyError:
            continue

        if not sensor:
            continue
        if sensor.object.account != account:
            continue
        if not 0 <= battery <= 100:
            continue

        report = Report(sensor=sensor, battery=battery, is_smoke=is_smoke, is_fire=is_fire, broken=broken,
                        datetime=datetime.now())
        report_processing(sensor=report.sensor, report=report)
        report.save()

    return {"message": "ok"}, 422


def reports_not_fire(sensor, count):
    last_reports_is_not_fire = [not (report.is_fire or report.is_smoke) for report in
                                Report.select().where(Report.sensor == sensor)
                                .limit(count).order_by(Report.datetime.desc())]
    return all(last_reports_is_not_fire)


def report_processing(sensor: Sensor, report: Report):
    is_fire = report.is_fire or report.is_smoke
    is_broken = report.broken

    # Прекращение статуса датчика "выключен, разряжен или сломан"
    if sensor.status_job in [SensorStatusJob.off, SensorStatusJob.discharged, SensorStatusJob.broken]:
        sensor.status_job = SensorStatusJob.on

    # Контроль заряда батареи
    sensor.battery = report.battery
    if sensor.battery <= 15 and sensor.status_job == SensorStatusJob.on:
        sensor.status_job = SensorStatusJob.charge_low
    elif sensor.battery > 15 and sensor.status_job == SensorStatusJob.charge_low:
        sensor.status_job = SensorStatusJob.on

    # Отчет информирует о пожаре
    if is_fire:
        # Если ранее датчик НЕ находился в статусе "Пожар" => "Пожар"
        if sensor.status_situation != SensorStatusSituation.fire:
            sensor.status_situation = SensorStatusSituation.fire

    # Отчет информирует о поломке
    elif is_broken:
        sensor.status_job = SensorStatusJob.broken
        if sensor.status_situation not in [SensorStatusSituation.fire, SensorStatusSituation.warning]:
            sensor.status_situation = SensorStatusSituation.null

    # Отчет положительный
    else:
        # Прекращение статуса ситуации "Пожар" => "Предупреждение", если последние 5 отчеты положительные
        if sensor.status_situation == SensorStatusSituation.fire and reports_not_fire(sensor=sensor, count=5):
            sensor.status_situation = SensorStatusSituation.warning
        # Прекращение статуса "Предупреждение" => "Стабильно", если последние 30 отчетов положительные
        elif sensor.status_situation == SensorStatusSituation.warning and reports_not_fire(sensor=sensor, count=30):
            sensor.status_situation = SensorStatusSituation.stable
        elif sensor.status_situation == SensorStatusSituation.null:
            sensor.status_situation = SensorStatusSituation.stable

    sensor.report_last = datetime.now()
    sensor.save()
