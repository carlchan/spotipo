# coding: utf-8
from flask_security import Security 
from flask_security import Security,SQLAlchemyUserDatastore
from unifispot.core.templates import render_template as custom_render_template


security = Security()


def configure(app,user_datastore):
    security.init_app(app,user_datastore)
