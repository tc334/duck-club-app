from os import environ

SECRET_KEY = environ.get('SECRET_KEY')
SIGNUP_CODE = environ.get('SIGNUP_CODE')

COCKROACH_URL = environ.get('COCKROACH_URL')
DB_NAME = environ.get('DB_NAME')

ADMIN_EMAIL = "tegan.counts@gmail.com"
ADMIN_PASSWORD = "password"

REDIS_IPADDR = environ.get('REDIS_IPADDR')
REDIS_PORT = environ.get('REDIS_PORT')

REDIS_URL = environ.get('REDIS_URL')
