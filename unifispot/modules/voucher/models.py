import logging
import arrow
from wtforms import BooleanField,TextField,IntegerField
from sqlalchemy import and_,or_
import math

from unifispot.core.db import db,FORMAT_DATETIME,JSONEncodedDict
from unifispot.core.const import *
from unifispot.core.models import Loginauth,Wifisite
from unifispot.utils.modelhelpers import SerializerMixin,CRUDMixin,ExportMixin
from unifispot.utils.translation import format_datetime
from unifispot.utils.translation import _l,_n,_

logger= logging.getLogger('voucher.model')

class Voucherconfig(CRUDMixin,SerializerMixin,db.Model): 
    id                  = db.Column(db.Integer, primary_key=True)
    account_id          = db.Column(db.Integer, db.ForeignKey('account.id'))
    siteid              = db.Column(db.Integer, db.ForeignKey('wifisite.id'))    
    enable_fields       = db.Column(JSONEncodedDict(255))
    mandate_fields      = db.Column(JSONEncodedDict(255))
    labelfor_fields     = db.Column(JSONEncodedDict(255))
    site                = db.relationship(Wifisite, backref=db.backref("voucherconfigs", \
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
class Voucherauth(Loginauth):
    voucherid        = db.Column(db.Integer, 
                                db.ForeignKey('voucher.id'))
    __mapper_args__ = {'polymorphic_identity': 'voucherauth'} 

    def populate_auth_details(self,voucher):
        '''Method to populate session details from transaction

        '''
        self.data_limit     = voucher.bytes_t
        self.time_limit     = voucher.time_available()
        self.speed_ul       = voucher.speed_ul
        self.speed_dl       = voucher.speed_dl 
        self.siteid         = voucher.siteid
        self.account_id     = voucher.account_id
        self.save()   


#Store vouchers
class Voucher(CRUDMixin,SerializerMixin,db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    batchid         = db.Column(db.String(10),index=True)
    voucher         = db.Column(db.String(20),index=True,unique=True)
    notes           = db.Column(db.String(50),index=True)
    duration_type   = db.Column(db.Integer,default=1)
    duration_val    = db.Column(db.BigInteger(),default=3600)
    bytes_t         = db.Column(db.BigInteger(),default=1000)
    speed_dl        = db.Column(db.BigInteger(),default=256)
    speed_ul        = db.Column(db.BigInteger(),default=256)
    used            = db.Column(db.Boolean(),default=False,index=True)
    num_devices     = db.Column(db.Integer,default=1,index=True)
    active          = db.Column(db.Integer,default=1,index=True) 
    siteid          = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    account_id      = db.Column(db.Integer, db.ForeignKey('account.id'))
    used_at         = db.Column(db.DateTime,index=True)   #used time in UTC,filled once voucher is used
    site            = db.relationship(Wifisite, backref=db.backref("vouchers", \
                                cascade="all,delete"))

    __form_fields_avoid__ = ['id','siteid','account_id','voucher',
                                'used_at','used','active']

    def get_duration(self):
        '''Returns duration in minutes'''
        if self.duration_type == 1:           
            return self.duration_val
        elif self.duration_type == 2:           
            return self.duration_val * 60        
        elif self.duration_type == 3:           
            return self.duration_val * 60 * 24
        else:
            return 0                  

    def get_query(self,siteid,startdate,enddate):
        return Voucher.query.filter_by(siteid=siteid)   

    def check_and_update_validity(self,loginauth,starttime=None):
        '''Check if current device can do login

        '''
        if starttime:
            utcnow = starttime.naive
        else:
            utcnow = arrow.utcnow().naive

        #get currently active auths for this account
        auths = Voucherauth.query.filter(and_(Voucherauth.voucherid==\
                    self.id,Voucherauth.endtime > utcnow)).all()   
        devices = []    
        for auth in auths:
            devices.append(auth.deviceid)

        
        #check if max number of devices are already connected
        if loginauth.deviceid not in devices and \
            len(devices) >= self.num_devices:
            logger.warning('Max device limit reached for:%s, not able to login\
                    device:%s'%(self.id,loginauth.deviceid))
            return (None,_l('Looks like max allowed devices are already connected'))


        #check timelimit if voucher is already used
        
        if self.used_at:
            usage = arrow.get(utcnow).timestamp - arrow.get(self.used_at).timestamp
            duration = self.get_duration()*60 - usage
            startedat = self.used_at
        else:
            duration = self.get_duration()*60
            self.used_at = utcnow
            self.used = True
            self.save()
            startedat = utcnow


        if not duration > 60:
            logger.warning('Time limit reached for:%s, not able to login\
                    device:%s'%(self.id,loginauth.deviceid)) 
            return (None,_l('Looks like you have reached max time limit'))

        time_available = int(math.floor(duration/60))

        data_available = 0

        if self.bytes_t: # if data limit is specified
            (time_used,data_used) = loginauth.get_usage(startedat)

            if not data_used < self.bytes_t:
                logger.warning('Max data limit reached for:%s, not able to login\
                    device:%s'%(self.id,loginauth.deviceid))
                return (None,_l('Looks like you have reached max data limit'))
            else:
                data_available = self.bytes_t - data_used
        else:
             data_available = 1000

        #all good, update login auth and return it
        loginauth.starttime = utcnow
        loginauth.time_limit = time_available
        loginauth.data_limit = data_available
        loginauth.endtime = arrow.get(utcnow).\
                        replace(minutes=time_available).naive              
        loginauth.speed_ul = self.speed_ul
        loginauth.speed_dl = self.speed_dl
        loginauth.save()
        return (True,'')




class Voucherdesign(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to represent Voucher design

    '''
    id              = db.Column(db.Integer, primary_key=True)
    siteid          = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    logofile        = db.Column(db.String(200),default='/static/img/logo.png')
    showlogo        = db.Column(db.Integer,default=1)
    shownotes       = db.Column(db.Integer,default=1)
    showqr          = db.Column(db.Integer,default=1)
    showduration    = db.Column(db.Integer,default=1)
    showdata        = db.Column(db.Integer,default=1)
    showspeed       = db.Column(db.Integer,default=1)
    bgcolor         = db.Column(db.String(10),default='#ffffff')
    txtcolor        = db.Column(db.String(10),default='#000000')
    bordercolor     = db.Column(db.String(10),default='#000000')    

    __form_fields_avoid__ = ['id','siteid','account_id']    