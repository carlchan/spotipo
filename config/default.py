import os
from passlib.hash import sha256_crypt

#Configure DB
basedir = os.path.join(os.path.abspath(os.path.dirname(__file__)),'..','unifispot')
EMAIL_TEMPLATES = os.path.join(basedir,'templates','emails') 
PROJECT_ROOT = basedir
MODULE_PATH = 'modules'
GUEST_TEMPLATES = os.path.join(basedir,'templates','guest')
UPLOAD_DIR = 'uploads'

SECRET_KEY = 'once-a-cat-went-to-talk-asndksadmnkamndkamkda'
SECURITY_REGISTERABLE = False
SECURITY_PASSWORD_HASH = 'sha256_crypt'
SECURITY_PASSWORD_SALT = "AJSHASJHAJSHASJHSAJHASJAHSJAHJSA"
SECURITY_UNAUTHORIZED_VIEW = '/login'
SECURITY_POST_LOGIN_VIEW = '/'
SECURITY_POST_LOGOUT_VIEW = '/login'
SECURITY_RECOVERABLE = True

SECURITY_MSG_INVALID_PASSWORD = ("Bad username or password", "error")
SECURITY_MSG_PASSWORD_NOT_PROVIDED = ("Bad username or password", "error")
SECURITY_MSG_USER_DOES_NOT_EXIST = ("Bad username or password", "error")
SECURITY_EMAIL_SENDER = 'no-reply@unifispot.com'
SECURITY_TOKEN_MAX_AGE = 1800
SECURITY_TRACKABLE = True


CELERY_ALWAYS_EAGER = False
CELERYD_CONCURRENCY=1

CELERY_BROKER_URL = 'sqlite:///'+os.path.join(os.path.abspath(os.path.dirname(__file__)),'celery.db')

SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(os.path.abspath(os.path.dirname(__file__)),'..','instance','database.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_COMMIT_ON_TEARDOWN =False
#http://primalpappachan.com/devops/2013/07/30/aws-rds--mysql-server-has-gone-away/
#--Fix for aws-rds-server has gone away
SQLALCHEMY_POOL_RECYCLE = 3600
SQLALCHEMY_TRACK_MODIFICATIONS = False


"""
Extensions needed by default, do not change this list
if you plan to add new extensions use EXTRA_EXTENSIONS
"""
CORE_EXTENSIONS = [
    'unifispot.core.db.db.init_app',
    'unifispot.ext.mail.configure',
    'unifispot.ext.security.configure',
    'unifispot.ext.babel.configure',
    'unifispot.ext.views.configure',
    'unifispot.ext.flaskmenu.configure',
    'unifispot.ext.modules.load_from_folder',
    'unifispot.ext.middleware.configure',
    'unifispot.ext.celeryext.configure',
    'unifispot.ext.redis.configure',
    'unifispot.ext.qrcode.configure',

]


DEFAULT_THEME = 'default'

GUESTTRACK_LIFETIME = 300 #life time of guesttrack in seconds

GUESTLOGIN_MODULES = []

DEFAULT_POST_AUTH_URL = 'http://unifispot.com'
TEMPLATES_AUTO_RELOAD = True

NO_UNIFI=False


NOTIFICATION_URL = 'http://spotipo.com/notifications/'