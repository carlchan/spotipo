from wtforms import BooleanField,TextField,IntegerField
from dateutil import tz
import arrow

from unifispot.core.db import db,FORMAT_DATETIME,JSONEncodedDict
from unifispot.core.const import *
from unifispot.core.models import Loginauth,Wifisite
from unifispot.utils.modelhelpers import SerializerMixin,CRUDMixin
from unifispot.utils.translation import format_datetime



class Emailconfig(CRUDMixin,SerializerMixin,db.Model): 
    id                  = db.Column(db.Integer, primary_key=True)
    account_id          = db.Column(db.Integer, db.ForeignKey('account.id'))
    siteid              = db.Column(db.Integer, db.ForeignKey('wifisite.id'))    
    enable_fields       = db.Column(JSONEncodedDict(255))
    mandate_fields      = db.Column(JSONEncodedDict(255))
    labelfor_fields     = db.Column(JSONEncodedDict(255))
    data_limit          = db.Column(db.BigInteger,default=0)
    time_limit          = db.Column(db.Integer,default=60)    
    speed_ul            = db.Column(db.Integer,default=0)    
    speed_dl            = db.Column(db.Integer,default=0)    
    session_limit_control= db.Column(db.Integer)
    session_overridepass = db.Column(db.String(50)) 
    relogin_policy      = db.Column(db.String(25),default='onetime')
    site                = db.relationship(Wifisite, backref=db.backref("emailconfigs", \
                                cascade="all,delete"))
    def __init__(self):
        '''Initial values for fields

        '''
        self.enable_fields = {'enable_email': 1, 'enable_firstname':1,
                            'enable_lastname':1,'enable_dob':0,
                            'enable_extra1':0,'enable_extra2':0 }
        self.mandate_fields = {'mandate_email': 1, 'mandate_firstname':1,
                            'mandate_lastname':1,'mandate_dob':0,
                            'mandate_extra1':0,'mandate_extra2':0 }                            
        self.labelfor_fields = {'labelfor_email': 'Email Address', 
                                'labelfor_firstname':'First Name',
                            'labelfor_lastname':'Last Name','labelfor_dob':'',
                            'labelfor_extra1':'','labelfor_extra2':'' }    
    #serializer arguement
    __json_hidden__ = []

    __json_modifiers__ = { 'enable_fields':'modeljson_to_dict',
                           'mandate_fields':'modeljson_to_dict',
                           'labelfor_fields':'modeljson_to_dict'}
  

    __form_fields_avoid__ = ['id','siteid','account_id']

    __form_fields_modifiers__ =  { 'enable_fields':'form_to_modeljson',
                           'mandate_fields':'form_to_modeljson',
                           'labelfor_fields':'form_to_modeljson', }

    def is_limited(self):
        #check if any limits are configured (daily/monthly)                           
        if self.session_limit_control:
            return True
        else:
            return False

    def is_daily_limited(self):
        if self.session_limit_control == 1:
            return True
        else:
            return False

    def is_monthly_limited(self):
        if self.session_limit_control == 2:
            return True
        else:
            return False          

    def get_limit_starttime(self):
        tzinfo = tz.gettz(self.site.timezone)
        if self.is_daily_limited():               
            starttime = arrow.now(tzinfo).floor('day').naive
        elif self.is_monthly_limited():
            starttime = arrow.now(tzinfo).floor('month').naive
        else:
            starttime = arrow.utcnow().naive
        return starttime


class Emailauth(Loginauth):
    __mapper_args__ = {'polymorphic_identity': 'emailauth'}    

    def get_stat(self):
        if self.is_valid():
            if self.relogin:
                return { 'auth_email':1,'relogin':1}
            else:
                return { 'auth_email':1,'relogin':0}
        else:
            return { 'auth_email':0 }




    def activate(self,emailconfig):
        '''Activate an emailloginauth

        '''
        return NotImplemented
        self.state = LOGINAUTH_READY
        self.activatedat = arrow.utcnow().naive
        self.save()




