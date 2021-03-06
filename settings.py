from os import environ

SECRET_KEY = environ.get('SECRET_KEY')

SQL_DB_NAME = environ.get('SQL_DB_NAME')
SQL_UNAME = environ.get('SQL_UNAME')
SQL_PASSWORD = environ.get('SQL_PASSWORD')
SQL_IPADDR = environ.get('SQL_IPADDR')
SQL_PORT = environ.get('SQL_PORT')

SQL_ADMIN_EMAIL = "tegan.counts@gmail.com"

SIGNUP_CODE = environ.get('SIGNUP_CODE')

CLEARDB_DATABASE_URL = environ.get('CLEARDB_DATABASE_URL')
