import os
from os.path import abspath
import logging
from flask import current_app
from flask_script import Manager
from flask_assets import ManageAssets
from flask_migrate import Migrate, MigrateCommand


from unifispot.ext.celeryext import celery 
from unifispot import create_app
import logging
from logging.handlers import RotatingFileHandler
logging.basicConfig(level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())


app = create_app(mode= 'development')    
#solution to start fresh flask-sqlalchemy session on each 
#task https://gist.github.com/twolfson/a1b329e9353f9b575131
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['CELERY_ALWAYS_EAGER'] = True
app.app_context().push()



#
#log_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),'logs','celeryworker.log')
#file_handler = RotatingFileHandler(log_file,'a', 1 * 1024 * 1024, 10)
#app.logger.setLevel(logging.DEBUG)
#file_handler.setLevel(logging.DEBUG)
#file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s \
#                                 [in %(pathname)s:%(lineno)d]'))
#app.logger.addHandler(file_handler)
#logging.getLogger().addHandler(file_handler)