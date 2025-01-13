import os 
basedir = os.path.abspath(os.path.dirname(__file__))
class Config:
    DEBUG=True
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORt = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS  = os.environ.get('MAIL_USE_TLS') is None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD  = os.environ.get('MAIL_PASSSWORD')
    ADMIN = ['']
    SECRET_KEY = os.environ.get('SECRET_KEY') or ''
    SQLALCHEMY_DATABASE_URI ='mysql://<username>:<pass>wsl_ip>/<db_name>'
