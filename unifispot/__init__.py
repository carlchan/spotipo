# -*- coding: utf-8 -*-
import warnings
from flask.exthook import ExtDeprecationWarning
#warnings.simplefilter("ignore", category=ExtDeprecationWarning)
# The above hack is needed because flask_mongoengine and flask_cache
# Did not migrated from old flask.ext style
from flask import render_template,redirect,url_for,Config,abort
from flask_security import Security,SQLAlchemyUserDatastore
from flask_security import current_user,login_required

from unifispot.core.models import user_datastore,User
from unifispot.ext import configure_extensions, configure_extension  # noqa
from unifispot.core.app import UnifispotApp


def create_app_base(config=None, test=False, ext_list=None, 
                    **settings):
    app = UnifispotApp(__name__,instance_relative_config=True)
    # Load the default configuration
    app.config.from_object('config.default')

    if test or app.config.get('TESTING'):
        #app.testing = True
        app.config.from_object('config.testing')
    if ext_list:
        for ext in ext_list:
            configure_extension(ext, app=app)
    return app


def create_app(mode="development"):
    """Create webapp instance."""

    app = create_app_base ()
    # Load the configuration from the instance folder
    app.config.from_pyfile('config.py')

    configure_extensions(app,user_datastore)

    return app

def create_testapp():
    """Create webapp instance."""
    app = create_app_base (test=True)
    # Load the configuration from the instance folder
    app.config.from_pyfile('config_test.py')
    configure_extensions(app,user_datastore)

    return app