#! flask/bin/python
from os.path import abspath
import os
from flask import current_app
from flask_script import Manager
from flask_assets import ManageAssets
from flask_migrate import Migrate, MigrateCommand

from unifispot import create_app
import logging
from logging.handlers import RotatingFileHandler
logging.basicConfig(level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())


app = create_app(mode= 'development')




log_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),'logs','prod.log')
file_handler = RotatingFileHandler(log_file,'a', 1 * 1024 * 1024, 10)
app.logger.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)
logging.StreamHandler().setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s \
                                 [in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(file_handler)
logging.getLogger().addHandler(file_handler)

app.run(host='0.0.0.0',debug = True)