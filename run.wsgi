#! flask/bin/python
from os.path import abspath
import os
import site
import sys

site.addsitedir('C:\\spotipo\\env\\Lib\\site-packages')

sys.path.append('C:\\spotipo')
sys.path.append('C:\\spotipo\\unifispot')


activate_this = 'C:\\spotipo\\env\\Scripts\\activate_this.py'
execfile(activate_this, dict(__file__=activate_this))


from flask import current_app
from flask_script import Manager
from flask_assets import ManageAssets
from flask_migrate import Migrate, MigrateCommand

from unifispot import create_app
import logging
from logging.handlers import RotatingFileHandler
logging.basicConfig(level=logging.DEBUG)

application = create_app(mode= 'development')

log_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),'logs','prod.log')
file_handler = RotatingFileHandler(log_file,'a', 1 * 1024 * 1024, 10)
application.logger.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s \
                                 [in %(pathname)s:%(lineno)d]'))
application.logger.addHandler(file_handler)

#app.logger.error("--------------------------APP RESTART------------------------------------------------------------")


