from datetime import datetime, timedelta
from threading import Thread
from time import sleep

from app.models import Object, ObjectStatusJob, Sensor, SensorStatusJob, SensorStatusSituation, ObjectStatusSituation, \
    Report
from app.notifications import send_notification, send_notification_emergency


texts = {
    'off': 'The FSafe system for the object \"{}\" has been disabled.\n\n'
           'Go to <a href=\"https://fsafe.yegoryakubovich.com/account/state/{}\">State page</a> for details',
    'defect': 'Sensors of object \"{}\" has defect.\n\n'
              'Go to <a href=\"https://fsafe.yegoryakubovich.com/account/state/{}\">State page</a> for details',
    'fire': 'Информация в данном сообщении является недостоверной. Сенсорами на объекте "{}" в комнате "{}"'
            'был обнаружен пожар!\n\nМы уведомили экстренные службы',
    'warning': 'Ситуация переведена в статус предупреждения. Будьте аккуратны!',
    'stable': 'Ситуация переведена в статус стабильно.',
    'fire_emergency': 'Информация в данном сообщении является недостоверной. Автоматический звонок системой Fire Safe!'
                      '\n\nИзвещателями был замечен пожар по адресу "{}". Комната: {}.',
}


def objects_processing():
    for obj in Object.select():
        status_job_init = obj.status_job
        status_situation_init = obj.status_situation

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

        if status_job_init != obj.status_job:
            # any => off
            if obj.status_job == ObjectStatusJob.off:
                send_notification(account=obj.account,
                                  notification=texts['off'].format(obj.name, obj.id))

            # any => defect
            elif obj.status_job == ObjectStatusJob.defect:
                send_notification(account=obj.account,
                                  notification=texts['defect'].format(obj.name, obj.id))
        if status_situation_init != obj.status_situation:
            # fire, call+emergency
            if obj.status_situation == ObjectStatusSituation.fire:
                sensor_fire = Sensor.get_or_none((Sensor.object == obj)
                                                 & (Sensor.status_situation == SensorStatusSituation.fire))

                send_notification(account=obj.account,
                                  notification=texts['fire'].format(obj.name, sensor_fire.description), call=True)
                send_notification_emergency(notification=texts['fire_emergency']
                                            .format(obj.address, sensor_fire.description))

            # warning
            elif obj.status_situation == ObjectStatusSituation.warning:
                send_notification(account=obj.account, notification=texts['warning'])

            # warning => stable
            elif obj.status_situation == ObjectStatusSituation.stable \
                    and status_situation_init == SensorStatusSituation.warning:
                send_notification(account=obj.account, notification=texts['stable'])


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
