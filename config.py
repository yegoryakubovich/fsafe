from os import getenv

SECRET_KEY = getenv('SECRET_KEY')
DEBUG = True

DB_NAME = getenv('DB_NAME')
DB_USER = getenv('DB_USER')
DB_PASSWORD = getenv('DB_PASSWORD')
DB_HOST = getenv('DB_HOST')
DB_PORT = int(getenv('DB_PORT'))

CALL_TOKEN = getenv('CALL_TOKEN')
CALL_CAMPAIGN_ID = getenv('CALL_CAMPAIGN_ID')
CALL_EMERGENCY = getenv('CALL_EMERGENCY')

TG_TOKEN = getenv('TG_TOKEN')
