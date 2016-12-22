from flask_sqlalchemy import SQLAlchemy,SignallingSession, SessionBase
from flask_security import RoleMixin,UserMixin,current_user
from flask_security.utils import encrypt_password
from flask_security import SQLAlchemyUserDatastore
from sqlalchemy import and_,or_
import arrow
import datetime


from unifispot.core.db import db,FORMAT_DATETIME,JSONEncodedDict
from unifispot.core.const import *
from unifispot.utils.modelhelpers import SerializerMixin,CRUDMixin,ExportMixin
from unifispot.utils.translation import format_datetime


#Roles for flask-security
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    def __repr__(self):
        return "<Role Name:%s Description:%s>"%(self.name,self.description)




#going to use joined table inheritance as given in 
#http://docs.sqlalchemy.org/en/rel_1_0/orm/inheritance.html#joined-table-inheritance
class User(CRUDMixin,SerializerMixin,db.Model, UserMixin):
    id              = db.Column(db.Integer, primary_key=True)
    email           = db.Column(db.String(255), unique=True)
    password        = db.Column(db.String(255))
    roles           = db.relationship('Role', secondary=roles_users,backref=db.backref('users', lazy='dynamic'))
    displayname     = db.Column(db.String(255))
    last_login_at   = db.Column(db.DateTime)
    current_login_at= db.Column(db.DateTime)
    last_login_ip   = db.Column(db.String(100))
    current_login_ip= db.Column(db.String(100))
    login_count     = db.Column(db.Integer)
    confirmed_at    = db.Column(db.DateTime)
    active          = db.Column(db.Boolean())
    type            = db.Column(db.String(50))
    __mapper_args__ = {'polymorphic_identity': 'user',
            'polymorphic_on':type}
            
    #serialiser arguement
    __json_hidden__ = ['password']
    __json_modifiers__ = { 'last_login_at':FORMAT_DATETIME,
                           'current_login_at':FORMAT_DATETIME,
                           'confirmed_at':FORMAT_DATETIME }

    def populate_from_form(self,form):
        self.email = form.email.data
        self.displayname = form.displayname.data
        if form.password.data:
            self.password = encrypt_password(form.password.data)


    def set_password(self,password):
        self.password = encrypt_password(password)
        db.session.commit()

    def __repr__(self):
        return "<User Name:%s Email:%s>"%(self.displayname,self.email)

user_datastore = SQLAlchemyUserDatastore(db,User,Role)


class Account(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to general settings


    '''
    id              = db.Column(db.Integer, primary_key=True)    
    name            = db.Column(db.Text)
    unifi_server    = db.Column(db.String(255),index=True,default="localhost")    
    unifi_server_ip = db.Column(db.String(255),index=True,default="127.0.0.1")    
    unifi_user      = db.Column(db.String(255),index=True,default="ubnt")    
    unifi_pass      = db.Column(db.String(255),index=True,default="ubnt")   
    unifi_port      = db.Column(db.Integer,index=True,default=8443)  
    unifi_version   = db.Column(db.String(5),index=True,default='v4')  
    mysql_server    = db.Column(db.String(255),index=True,default="localhost")       
    mysql_user      = db.Column(db.String(255),index=True,default="ubnt")    
    mysql_pass      = db.Column(db.String(255),index=True,default="ubnt")   
    mysql_port      = db.Column(db.Integer,index=True,default=8443)      
    firstrun        = db.Column(db.Integer, default=1,index=True) 
    token           = db.Column(db.String(50),index=True) 
    db_version      = db.Column(db.String(5),index=True) 
    expiresat       = db.Column(db.DateTime,index=True) 
    createdat       = db.Column(db.DateTime,index=True) 
    capabilities    = db.Column(db.Integer,index=True)
    active          = db.Column(db.Integer, default=1,index=True) 
    logins_allowed  = db.Column(db.Integer, default=1000,index=True)

    notifications   = db.relationship('Notification', backref='account',lazy='dynamic')


    #serialiser arguement
    __json_public__ = ['id','unifi_server','unifi_user',
                        'unifi_pass','unifi_port']

    __form_fields_avoid__ = ['id','firstrun','token','db_version','account_type',
                                'expiresat','capabilities','logins_allowed',
                                'active','mysql_server','mysql_user','mysql_pass',
                                'mysql_port','name','unifi_server_ip','createdat']


class Notification(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to represent notifications.


    '''
    id              = db.Column(db.Integer, primary_key=True)    
    content         = db.Column(db.Text)      
    created_at      = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)
    viewed          = db.Column(db.Boolean(),default=0,index=True)
    viewed_at       = db.Column(db.DateTime)
    user_id         = db.Column(db.Integer, index=True) 
    account_id      = db.Column(db.Integer, db.ForeignKey('account.id'))
    notifi_type     = db.Column(db.Integer, index=True) 
    notifi_id       = db.Column(db.String(20), index=True) 

    @classmethod
    def get_common_notifications(cls,account_id):
        notifications = Notification.query.filter_by(viewed=0,user_id=0,account_id=account_id).all()
        return notifications

    @classmethod
    def get_user_notifications(cls,account_id,user_id):
        notifications = Notification.query.filter_by(viewed=0,user_id=user_id,account_id=account_id).all()        
        return notifications

    @classmethod
    def mark_as_read(cls,id,account_id):
        notification = Notification.query.filter_by(id=id,account_id=account_id).first()   
        if not notification:
            return None     
        notification.viewed = 1
        notification.viewed_at = arrow.now().naive
        db.session.commit()
        return 1 

    @classmethod
    def mark_as_unread(cls,id,account_id):
        notification = Notification.query.filter_by(id=id,account_id=account_id).first()   
        if not notification:
            return None     
        notification.viewed = 0
        notification.viewed_at = None
        db.session.commit()
        return 1 

    @classmethod
    def check_notify_added(cls,notifi_id):
        if Notification.query.filter_by(notifi_id=notifi_id).first():
            return True
        return False        

    def get_type(self):
        if self.notifi_type == NOTIFI_TYPE_DANGER:
            return 'danger'
        elif self.notifi_type == NOTIFI_TYPE_INFO:
            return 'info'        
        elif self.notifi_type == NOTIFI_TYPE_SUCCESS:
            return 'success' 
        elif self.notifi_type == NOTIFI_TYPE_WARNING:
            return 'warning' 
        else:
            return ''


class Admin(User):
    ''' Class to represent admin, each admin will be associated with a user of type admin

    '''
    id              = db.Column(db.Integer,db.ForeignKey('user.id'), primary_key=True)    
    account_id      = db.Column(db.Integer, db.ForeignKey('account.id')) 
    __mapper_args__ = {'polymorphic_identity': 'admin'}



    def check_admin(self):
        return True

    def get_account_id(self):  
        return self.account_id

    def check_client(self):
        return False

    def get_user_type(self):
        return 'admin'

    def get_query(self):
        return Admin.query.filter_by(account_id=current_user.account_id)

class Client(User):
    ''' Class to represent admin, each admin will be associated with a user of type admin

    '''
    id          = db.Column(db.Integer,db.ForeignKey('user.id'), primary_key=True) 
    __mapper_args__ = {'polymorphic_identity': 'client'}
    account_id      = db.Column(db.Integer, db.ForeignKey('account.id')) 


    def check_admin(self):        
        return False

    def get_account_id(self):  
        return self.account_id

    def check_client(self):
        return True

    def get_user_type(self):
        return 'client'

    def get_query(self):
        return Client.query.filter_by(account_id=current_user.account_id)        


class Wifisite(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to represent wifi sites. Each client can have multiple sites


    '''
    id                  = db.Column(db.Integer, primary_key=True)
    client_id           = db.Column(db.Integer, db.ForeignKey('client.id'))
    admin_id            = db.Column(db.Integer, db.ForeignKey('admin.id'))
    account_id          = db.Column(db.Integer, db.ForeignKey('account.id'))     
    name                = db.Column(db.String(255),index=True,default="defaultsite")  
    default_landing     = db.Column(db.Integer)
    sitekey             = db.Column(db.String(50),index=True,default="default")
    backend_type        = db.Column(db.String(50),default='unifi')
    template            = db.Column(db.String(50),default='default')  
    reports_type        = db.Column(db.String(10),default='none')
    reports_list        = db.Column(db.String(400))
    redirect_url        = db.Column(db.String(200),default='http://www.spotipo.com')
    timezone            = db.Column(db.Text(100),default='UTC')
    #define special methodfields which will store all the enabled methods
    preauth_methods     = db.Column(JSONEncodedDict(255)) 
    auth_methods        = db.Column(JSONEncodedDict(255),
                    default={'auth_email':1}) 
    postauth_methods    = db.Column(JSONEncodedDict(255)) 
    export_methods      = db.Column(JSONEncodedDict(255))  


    #serializer arguement
    __json_hidden__ = ['default_landing','admin_id','account_id']

    __json_modifiers__ = { 'preauth_methods':'modeljson_to_dict',
                           'auth_methods':'modeljson_to_dict',
                           'postauth_methods':'modeljson_to_dict', 
                           'export_methods':'modeljson_to_dict', }  

    __form_fields_avoid__ = ['id','default_landing','admin_id',
                             'account_id','template']

    __form_fields_modifiers__ =  { 'preauth_methods':'form_to_modeljson',
                           'auth_methods':'form_to_modeljson',
                           'postauth_methods':'form_to_modeljson', 
                           'export_methods':'form_to_modeljson', }
    
    def get_num_methods(self,methodtype):
        #get number of configured methods for this method type
        methods = getattr(self,methodtype)
        num = 0
        if methods:
            for key,val in methods.iterm():
                if val:
                    num = num +1 
        else:
            num = 0
        return num

    def get_methods(self,methodtype):
        #get all the configured methods for this method type
        methodslist = []
        methods = getattr(self,methodtype)        
        if methods:
            for key,val in methods.items():
                if val:
                    methodslist.append(key)
        return methodslist


    def check_login_en(self,ltype):
        if self.auth_methods:
            return self.auth_methods.get(ltype)
        else:
            return None

    def site_from_baseform(self,form):
        #create 
        self.name           = form.name.data
        self.timezone       = form.timezone.data
        self.client_id      = form.client_id.data
        self.backend_type   = form.backend_type.data

     
class Landingpage(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to represent landing page design

    '''
    id              = db.Column(db.Integer, primary_key=True)
    siteid          = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    logofile        = db.Column(db.String(200),default='/static/img/logo.png')
    bgfile          = db.Column(db.String(200),default='/static/img/bg.jpg')
    pagebgcolor     = db.Column(db.String(10),default='#ffffff')
    bgcolor         = db.Column(db.String(10),default='#ffffff')
    headerlink      = db.Column(db.String(200))
    basefont        = db.Column(db.Integer,default=2)
    topbgcolor      = db.Column(db.String(10),default='#ffffff')
    toptextcolor    = db.Column(db.String(10))
    topfont         = db.Column(db.Integer,default=2)
    toptextcont     = db.Column(db.String(2000),default='Please Sign In for WiFi')
    middlebgcolor   = db.Column(db.String(10),default='#ffffff')
    middletextcolor = db.Column(db.String(10))
    middlefont      = db.Column(db.Integer,default=2)
    bottombgcolor   = db.Column(db.String(10),default='#ffffff')
    bottomtextcolor = db.Column(db.String(10))
    bottomfont      = db.Column(db.Integer,default=2)
    footerbgcolor   = db.Column(db.String(10),default='#ffffff')
    footertextcolor = db.Column(db.String(10))
    footerfont      = db.Column(db.Integer,default=2)
    footertextcont  = db.Column(db.String(2000))
    btnbgcolor      = db.Column(db.String(10))
    btntxtcolor     = db.Column(db.String(10))
    btnlinecolor    = db.Column(db.String(10),default='#000000')
    tosfile         = db.Column(db.String(200),default='/static/img/tos.pdf')
    copytextcont    = db.Column(db.String(2000))
    #set up cascading to delete automatically
    site            = db.relationship(Wifisite, backref=db.backref("landingpages", cascade="all,delete"))

    __form_fields_avoid__ = ['id','siteid']    

#entry to store the details of uploaded files
class Sitefile(db.Model):
    ''' Class to represent Files, each entry will point to a file stored in the HD

    '''
    id              = db.Column(db.Integer, primary_key=True)   
    siteid         = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    file_location   = db.Column(db.String(255))
    file_label      = db.Column(db.String(255))
    site            = db.relationship(Wifisite, backref=db.backref("sitefiles", cascade="all,delete"))

    def to_dict(self):
        return { 'file_location':self.file_location,
                    'id':self.id,
                    'file_label':self.file_label}

    def populate_from_form(self,form):
        self.file_label     = form.file_label.data

    def update_ownership(self,siteid):
        self.siteid = siteid

    def get_file_path(self,fileid):
        if fileid == 0:
            return '/static/img/default_file.png'
        file_path = Sitefile.query.filter_by(id=fileid).first()
        return file_path


class Loginauth(CRUDMixin,SerializerMixin,db.Model):
    '''Class to store Loginauth credentials, 
            could be FBLogin,VoucherLogin,EMail,SMS etc

        All logins should be inherited from this class

    '''
    id                  = db.Column(db.Integer, primary_key=True)
    account_id          = db.Column(db.Integer, db.ForeignKey('account.id'))
    siteid              = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    deviceid            = db.Column(db.Integer, db.ForeignKey('device.id'))
    sessions            = db.relationship('Guestsession', backref='loginauth',\
                            lazy='dynamic')
    starttime           = db.Column(db.DateTime,default=datetime.datetime.utcnow,\
                            index=True)
    endtime             = db.Column(db.DateTime,default=datetime.datetime.utcnow,\
                            index=True)
    last_login_at       = db.Column(db.DateTime,default=datetime.datetime.utcnow,\
                            index=True)    #to track last login
    data_limit          = db.Column(db.BigInteger) #in MB
    time_limit          = db.Column(db.Integer,default=60)    #in mins
    speed_ul            = db.Column(db.Integer,default=0)    
    speed_dl            = db.Column(db.Integer,default=0)  
    state               = db.Column(db.Integer,default=LOGINAUTH_INIT)  
    relogin             = db.Column(db.Integer,default=0)  
    blocked             = db.Column(db.Integer,default=0)  
    site                = db.relationship(Wifisite, backref=db.backref("loginauths", 
                                cascade="all,delete"))
    type                = db.Column(db.String(50),index=True)

    __mapper_args__ = {'polymorphic_identity': 'loginauth',
            'polymorphic_on':type}

    def time_available(self):
        '''Check validity  and return remaining minutes'''
        if not self.time_limit: #if no limit set return a large value
            return 480        
        utcnow = arrow.utcnow()
        validity = arrow.get(self.starttime).replace(minutes=self.time_limit)
        availabletime = validity.timestamp - utcnow.timestamp
        if availabletime > 60: # convert from seconds to mins
            return int(availabletime/60)
        else:
            return 0


    def data_available(self,*args,**kwargs):
        '''Check validity '''
        if not self.data_limit: #if no limit set return a large value
            return 10000
        data_used = 0
        sessions = Guestsession.query.filter(and_(Guestsession.siteid == self.siteid,
                    Guestsession.loginauthid == self.id,
                    Guestsession.override == 0,
                    Guestsession.starttime >= self.starttime)).all()
        for sess in sessions:
            if sess.data_used:
                data_used = int(sess.data_used) + data_used
        data = int(self.data_limit) - data_used
        if data >0:
            return data
        else:
            return 0

    def get_usage(self,fromtime):
        '''Check validity '''
        data_used = 0
        time_used = 0
        sessions = Guestsession.query.filter(and_(Guestsession.siteid == self.siteid,
                    Guestsession.loginauthid == self.id,
                    Guestsession.override == 0,
                    Guestsession.starttime >= fromtime)).all()
        for sess in sessions:
            if sess.data_used:
                data_used = int(sess.data_used) + data_used
            if sess.duration:
                time_used = int(sess.duration) + time_used
        return (time_used,data_used)

    def reset_usage(self,fromtime):       
        '''Reset all sessions from given time to now '''
        sessions = Guestsession.query.filter(and_(Guestsession.siteid == self.siteid,
                    Guestsession.loginauthid == self.id,
                    Guestsession.override == 0,
                    Guestsession.starttime >= fromtime)).all()
        for sess in sessions:
            sess.override = 1
            sess.save()

    def populate_auth_details(self,modconfig):
        '''Method to populate session details from modconfig

        '''
        self.data_limit     = modconfig.data_limit
        self.time_limit     = modconfig.time_limit
        self.speed_ul       = modconfig.speed_ul
        self.speed_dl       = modconfig.speed_dl 
        self.save()  
 
    def reset(self):
        self.starttime = arrow.utcnow().naive
        self.save()

    def reset_lastlogin(self):
        self.last_login_at = arrow.utcnow().naive
        self.save()

    def login_completed(self,loginconfig):
        if self.state == LOGINAUTH_INIT:
            return False
        else:
            return True

    def is_blocked(self):
        if self.blocked:
            return True
        else:
            return False


    def is_currently_active(self):
        '''check if any of the session is currently on going

        '''
        utcnow = arrow.utcnow().naive
        if Guestsession.query.filter(and_(Guestsession.loginauthid==self.id,
              Guestsession.stoptime > utcnow)).count():
            return True
        else:
            return False

class Preloginauth(SerializerMixin,db.Model):
    '''Base class to store preoginauth credentials, could be SMS or something

        All logins should be inherited from this class

    '''
    id                  = db.Column(db.Integer, primary_key=True)
    client_id           = db.Column(db.Integer, db.ForeignKey('client.id'))
    account_id          = db.Column(db.Integer, db.ForeignKey('account.id'))
    siteid              = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    tracks              = db.relationship('Guesttrack', backref='preloginauth',\
                            lazy='dynamic')    
    site                = db.relationship(Wifisite, backref=db.backref("preloginauths", \
                                cascade="all,delete"))
    type            = db.Column(db.String(50))
    __mapper_args__ = {'polymorphic_identity': 'preloginauth',
            'polymorphic_on':type}

class Guest(ExportMixin,CRUDMixin,SerializerMixin,db.Model):
    ''' Class to represent guest profile, it will be filled fully/partially 
            depending upon site configuration

    '''
    id          = db.Column(db.Integer, primary_key=True)
    siteid     = db.Column(db.Integer, db.ForeignKey('wifisite.id')) 
    firstname   = db.Column(db.String(60))
    lastname    = db.Column(db.String(60))
    age         = db.Column(db.Integer,index=True)
    gender      = db.Column(db.String(10),index=True)
    state       = db.Column(db.Integer,index=True)
    fbcheckedin = db.Column(db.Integer,index=True,default=0)
    fbliked     = db.Column(db.Integer,index=True,default=0)
    state       = db.Column(db.Integer,index=True)
    email       = db.Column(db.String(60))
    phonenumber = db.Column(db.String(15))
    agerange    = db.Column(db.String(15))
    created_at  = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)
    apisync     = db.Column(db.Integer,index=False)  #Flag to be set after syncing to API
    synchedat   = db.Column(db.DateTime,index=True) #synched time in UTC
    demo        = db.Column(db.Boolean(),default=0,index=True)
    newsletter  = db.Column(db.Boolean(),default=0,index=True)
    dob         = db.Column(db.String(15))
    details     = db.Column(JSONEncodedDict(255)) #used for handling extra details
    site        = db.relationship(Wifisite, backref=db.backref("guests", \
                                cascade="all,delete"))


    def get_device_phonenumber(self):
        for device in self.devices:
            phonenumber = device.get_phonenumber()
            if phonenumber:
                return phonenumber
        return ''

    def get_gender(self):
        if self.gender == 1 :
            return 'M'
        elif self.gender == 2:
            return 'F'
        else:
            return 'N/A'

    def populate_from_guest_form(self,form,wifisite):
        details = {}
        if hasattr(form,'email'):
            self.email = form.email.data        
        if hasattr(form,'firstname'):
            self.firstname = form.firstname.data
        if hasattr(form,'lastname'):
            self.lastname = form.lastname.data
        if hasattr(form,'phonenumber'):
            self.phonenumber = form.phonenumber.data
        if hasattr(form,'dob'):
            self.dob = form.dob.data    
        if hasattr(form,'newsletter'):
            self.newsletter = form.newsletter.data                       
        if hasattr(form,'extra1'):
            details.update({form.extra1.label.text:form.extra1.data})
        if hasattr(form,'extra2'):
            details.update({form.extra2.label.text:form.extra2.data})   
        self.details = details   

    def populate_from_fb_profile(self,profile,wifisite):
        self.firstname  = profile.get('first_name')
        self.lastname   = profile.get('last_name')
        self.email      = profile.get('email')       
        self.gender     = profile.get('gender')
        age_range       = profile.get('age_range')
        dob             = profile.get('birthday')
        if dob:
            #convert MM-DD-YYY to DD-MM-YYYY
            self.dob = arrow.get(dob,'MM/DD/YYYY').format('DD/MM/YYYY')        
        if age_range:
            self.agerange = '%s-%s'%(age_range.get('min',''),age_range.get('max',''))

    def get_query(self,siteid,startdate,enddate):

        return Guest.query.filter_by(siteid=siteid,demo=0)        


class Device(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to represent guest's device, each guest can have 
            multiple devices attached to his account

    '''
    id              = db.Column(db.Integer, primary_key=True)
    devicemac       = db.Column(db.String(30),index=True)
    hostname        = db.Column(db.String(60),index=True)
    state           = db.Column(db.Integer)
    created_at      = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)
    guestid         = db.Column(db.Integer, db.ForeignKey('guest.id'))
    siteid          = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    expires_at      = db.Column(db.DateTime)          #Expiry time for last used voucher  
    demo            = db.Column(db.Integer,default=0,index=True)
    sms_confirm     = db.Column(db.Integer,default=0,index=True) #used to verify if the device's phone number is confirmed
    guest           = db.relationship(Guest, backref=db.backref("devices", \
                                cascade="all,delete"))
    loginauths      = db.relationship('Loginauth', backref='device',\
                            lazy='dynamic')

    def get_monthly_usage(self):
        '''Returns the total monthly free data usage for this device

            Excludes voucher usage
        '''
        firstday    = arrow.now(self.site.timezone).floor('month').to('UTC').naive
        sessions    = Guestsession.query.filter(and_(Guestsession.device_id==self.id,
                        Guestsession.starttime >= firstday)).all()
        total_data  = 0
        for session in sessions:
            if session.state != GUESTRACK_VOUCHER_AUTH and session.data_used:
                total_data += int(session.data_used)

        #convert bytes to Mb

        data_mb = int(math.ceil((total_data/1024000.0)))
        return data_mb

    def get_phonenumber(self):
        '''Returns the phonenumber connected to this account

        '''
        return ';'.join([x.phonenumber for x in self.smsdatas])

    def get_voucher(self):
        '''Returns a valid voucher id if any associated with this device, if nothing found returns None

        '''
        for voucher in self.vouchers:
            if voucher.check_validity():
                return voucher.id

        return None

class Guestsession(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to represent guest session. Each session is associated to a Guest and will have a state associated with it.

    '''
    id          = db.Column(db.Integer, primary_key=True)
    siteid      = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    deviceid    = db.Column(db.Integer, db.ForeignKey('device.id'))
    loginauthid = db.Column(db.Integer, db.ForeignKey('loginauth.id'))
    trackid     = db.Column(db.Integer, db.ForeignKey('guesttrack.id'))
    starttime   = db.Column(db.DateTime,default=datetime.datetime.utcnow,index=True)
    lastseen    = db.Column(db.DateTime,index=True,default=datetime.datetime.utcnow)
    stoptime    = db.Column(db.DateTime,index=True)   #Time at which session is stopped, to be filled by session updator
    expiry      = db.Column(db.DateTime,index=True,default=datetime.datetime.utcnow)   #predicted expiry time,default to 60 minutes
    temp_login  = db.Column(db.Integer,default=0)
    duration    = db.Column(db.Integer,default=0)
    override    = db.Column(db.Integer,default=0) # to disable considering the session from considering while usage calculation
    ban_ends    = db.Column(db.DateTime,index=True)
    data_used   = db.Column(db.String(20),default=0)            #Data used up in this session
    state       = db.Column(db.Integer)
    mac         = db.Column(db.String(30),index=True)
    d_updated   = db.Column(db.String(20))            #data updated last
    demo        = db.Column(db.Integer,default=0,index=True)
    obj_id      = db.Column(db.String(30),index=True)  #_id of document in guest collection of unifi



class Guesttrack(CRUDMixin,SerializerMixin,db.Model):
    ''' Class to track connection attempts, this is also used to track login process

    '''
    id              = db.Column(db.Integer, primary_key=True)
    trackid         = db.Column(db.String(40),index=True,unique=True)
    siteid          = db.Column(db.Integer, db.ForeignKey('wifisite.id'))
    preloginauthid  = db.Column(db.Integer, db.ForeignKey('preloginauth.id'))
    loginauthid     = db.Column(db.Integer, db.ForeignKey('loginauth.id'))
    deviceid        = db.Column(db.Integer, db.ForeignKey('device.id'))
    apmac           = db.Column(db.String(20),index=True)
    devicemac       = db.Column(db.String(20),index=True)
    timestamp       = db.Column(db.DateTime,default=datetime.datetime.utcnow,
                            index=True)
    state           = db.Column(db.Integer,index=True,
                            default=GUESTTRACK_PRELOGIN)
    origurl         = db.Column(db.String(200))
    demo            = db.Column(db.Integer,default=0,index=True)
    site            = db.relationship(Wifisite, 
                                backref=db.backref("guesttracks",
                                cascade="all,delete"))
    loginstat       = db.Column(JSONEncodedDict(255)) #store relevant stats
                                                       # will have value like {'auth_facebook':1,
                                                       #   'fb_liked':1,'newlogin':1}

    def updatestat(self,key,val):
        '''method to update statistics value for this track

        '''
        oldstat = dict(self.loginstat)
        oldstat[key] = val
        self.loginstat = oldstat
        self.save()

    def increamentstat(self,key):
        '''method to increament value of stat for a particular key

        '''
        oldstat = dict(self.loginstat) if self.loginstat else {}
        oldval = oldstat.get(key)
        if oldval:
            oldstat[key] = oldval + 1
        else:
            oldstat[key] =  1
        self.loginstat = oldstat
        self.save()




