import os
import shutil
import pytest
from flask_security.utils import encrypt_password
from flask import current_app,url_for
from flask_migrate import Migrate,upgrade,migrate,init,downgrade

from unifispot import create_testapp
from unifispot.core.db import db as _db
from unifispot.core.models import user_datastore
from tests.factories import UserFactory
from tests.data import init_data

#from tests.data.data import init_data

#---------------enable logging while tests running-----------
import logging
from logging.handlers import RotatingFileHandler
logfile = 'alltests.log'
os.remove(logfile) if os.path.exists(logfile) else None
file_handler = RotatingFileHandler(logfile, 'a', 1 * 1024 * 1024, 10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
##------------End logging Initilization-----------------------

@pytest.fixture(scope='session')
def app(request):
    """Session-wide test `Flask` application."""

    app = create_testapp()


    # Establish an application context before running the tests.
   # ctx = app.app_context()
   # ctx.push()
    
    ##------------More logging configuration---------------------
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    app.logger.debug('--------------Starting Tests-----------------')
    ##------------More logging configuration END------------------
   # def teardown():
       # ctx.pop()

    #request.addfinalizer(teardown)
    return app

@pytest.fixture(scope='session')
def db(app, request):
    """Session-wide test database."""

    def teardown():
        pass
    _db.app = app

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='function')
def session(db, request):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    db.session = session
    init_data(session)
    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session

