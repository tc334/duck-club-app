from os import environ

SECRET_KEY = environ.get('SECRET_KEY')

SQL_UNAME = environ.get('SQL_UNAME')
SQL_PASSWORD = environ.get('SQL_PASSWORD')
SQL_IPADDR = environ.get('SQL_IPADDR')
SQL_PORT = environ.get('SQL_PORT')