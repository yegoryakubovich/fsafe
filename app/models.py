from datetime import timedelta

from flask_jwt_extended import create_access_token
from peewee import *
from qrcode import make

from app.status import SensorStatusSituation, ObjectStatusJob, ObjectStatusSituation, SensorStatusJob
from config import DB_PORT, DB_PASSWORD, DB_USER, DB_NAME, DB_HOST


db = MySQLDatabase(DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)


def models_create():
    Account.create_table()
    Dispatcher.create_table()
    Object.create_table()
    Sensor.create_table()
    Report.create_table()


class BaseModel(Model):
    class Meta:
        database = db


class Account(BaseModel):
    id = PrimaryKeyField()
    login = CharField(max_length=24)
    password = CharField(max_length=24)
    fullname = CharField(max_length=128)
    phone = CharField(max_length=24)
    tg_id = IntegerField(null=True)
    tg_username = CharField(max_length=128, null=True)
    reg_datetime = DateTimeField()

    def create_access_token(self, expire_time=1):
        expires_delta = timedelta(expire_time)
        access_token = create_access_token(identity=self.id, expires_delta=expires_delta)
        return access_token

    def create_qr(self):
        img = make('t.me/fsafe_bot?start={}'.format(self.id))
        img.save('app/static/images/tg/{}.png'.format(self.id))

    class Meta:
        db_table = "accounts"


class Dispatcher(BaseModel):
    id = PrimaryKeyField()
    name = CharField(max_length=128)
    login = CharField(max_length=24)
    password = CharField(max_length=24)

    class Meta:
        db_table = "dispatchers"


class Object(BaseModel):
    id = PrimaryKeyField()
    name = CharField(max_length=128)
    account = ForeignKeyField(Account, to_field='id', on_delete='cascade')
    dispatcher = ForeignKeyField(Dispatcher, to_field='id', on_delete='cascade')
    address = CharField(max_length=256)
    status_job = CharField(max_length=16, default=ObjectStatusJob.off)
    status_situation = CharField(max_length=16, default=ObjectStatusSituation.null)

    class Meta:
        db_table = "objects"


class Sensor(BaseModel):
    id = PrimaryKeyField()
    object = ForeignKeyField(Object, to_field='id', on_delete='cascade')
    description = CharField(max_length=256)
    report_last = DateTimeField()
    battery = IntegerField(default=0)
    status_job = CharField(max_length=16, default=SensorStatusJob.off)
    status_situation = CharField(max_length=16, default=SensorStatusSituation.null)

    class Meta:
        db_table = "sensors"


class Report(BaseModel):
    id = PrimaryKeyField()
    sensor = ForeignKeyField(Sensor, to_field='id', on_delete='cascade')
    battery = IntegerField()
    is_fire = BooleanField()
    is_smoke = BooleanField()
    broken = BooleanField()
    datetime = DateTimeField()

    class Meta:
        db_table = "reports"
