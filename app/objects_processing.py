from datetime import datetime, timedelta
from threading import Thread
from time import sleep

from app.models import Object, ObjectStatusJob, Sensor, SensorStatusJob, SensorStatusSituation, ObjectStatusSituation, \
    Report


def objects_processing():
    for obj in Object.select():
        obj_sensors = [s for s in Sensor.select().where(Sensor.object == obj)]

        if not obj_sensors:
            continue

        obj_sensors_j = [s.status_job for s in obj_sensors]
        obj_sensors_s = [s.status_situation for s in obj_sensors]

        count_on = obj_sensors_j.count(SensorStatusJob.on)
        count_off = obj_sensors_j.count(SensorStatusJob.off)
        count_broken = obj_sensors_j.count(SensorStatusJob.broken)
        count_discharged = obj_sensors_j.count(SensorStatusJob.discharged)

        if count_on == len(obj_sensors):
            obj.status_job = ObjectStatusJob.on
        elif len(obj_sensors) == count_off + count_broken + count_discharged:
            obj.status_job = ObjectStatusJob.off
        else:
            obj.status_job = ObjectStatusJob.defect

        count_null = obj_sensors_s.count(SensorStatusSituation.null)
        count_fire = obj_sensors_s.count(SensorStatusSituation.fire)
        count_warning = obj_sensors_s.count(SensorStatusSituation.warning)

        if count_null == len(obj_sensors):
            obj.status_situation = ObjectStatusSituation.null
        elif count_fire:
            obj.status_situation = ObjectStatusSituation.fire
        elif count_warning:
            obj.status_situation = ObjectStatusSituation.warning
        else:
            obj.status_situation = ObjectStatusSituation.stable

        obj.save()


def sensors_processing():
    for sensor in Sensor.select():
        request = Report.select().where(Report.sensor == sensor).limit(1).order_by(Report.datetime.desc())
        report_last = [r for r in request]
        if report_last:
            report = report_last[0]
            time_limited = datetime.now() - timedelta(minutes=3)
            if report.datetime <= time_limited:
                if sensor.status_situation in [SensorStatusSituation.fire, SensorStatusSituation.warning]:
                    sensor.status_job = SensorStatusJob.broken
                elif sensor.battery <= 15:
                    sensor.status_job = SensorStatusJob.discharged
                    sensor.status_situation = SensorStatusSituation.null
                else:
                    sensor.status_job = SensorStatusJob.off
                    sensor.status_situation = SensorStatusSituation.null
        else:
            sensor.status_job = SensorStatusJob.off

        sensor.save()


def processing():
    while True:
        try:
            objects_processing()
            sensors_processing()
            sleep(5)
        except Exception as e:
            print(e)


def create_processing():
    Thread(target=processing, args=()).start()
