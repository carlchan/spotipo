from flask_sqlalchemy import SQLAlchemy,SignallingSession, SessionBase
from flask_security import RoleMixin,UserMixin,current_user
from flask_security.utils import encrypt_password
from flask_security import SQLAlchemyUserDatastore
import arrow
import datetime


from unifispot.core.db import db,FORMAT_DATETIME,JSONEncodedDict
from unifispot.core.const import *
from unifispot.utils.modelhelpers import SerializerMixin,CRUDMixin
from unifispot.utils.translation import format_datetime
from unifispot.core.models import Wifisite


class Sitestat(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to represent daily statistics

    '''
    id              = db.Column(db.Integer, primary_key=True)   
    siteid          = db.Column(db.Integer, db.ForeignKey('wifisite.id')) 
    account_id      = db.Column(db.Integer, db.ForeignKey('account.id'))  
    date            = db.Column(db.DateTime,index=True)   #used as key
    login_stat      = db.Column(JSONEncodedDict(255))  # to hold individual stats
    num_visits      = db.Column(db.Integer,default=0)
    num_newlogins   = db.Column(db.Integer,default=0)
    num_repeats     = db.Column(db.Integer,default=0)
    avg_time        = db.Column(db.Integer,default=0)
    avg_data        = db.Column(db.Integer,default=0)     
    last_updated    = db.Column(db.DateTime,default=datetime.datetime.utcnow,
                            index=True)
    #set up cascading to delete automatically
    site            = db.relationship(Wifisite, 
                        backref=db.backref("sitestats", cascade="all,delete"))

    def json_to_dict(self,field_name):
        '''used for updating dict representation with values for login_stat

        '''
        return getattr(self,field_name) or {}  


    __json_hidden__ = ['admin_id','account_id','avg_time','avg_data',
                        'last_updated','date']
    __json_modifiers__ = { 'login_stat':json_to_dict}

    def get_total_logins(self):
        '''returns total logins for the day ''' 
        return self.num_newlogins + self.num_repeats