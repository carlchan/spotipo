#! flask/bin/python
from os.path import abspath

from flask import current_app
from flask_script import Manager
from flask_assets import ManageAssets
from flask_migrate import Migrate, MigrateCommand

from unifispot import create_testapp
from unifispot.core.db import db


app = create_testapp()
manager = Manager(app)
migrate = Migrate(app, db,directory='migrations_test')
manager.add_command('db', MigrateCommand)


manager.run()