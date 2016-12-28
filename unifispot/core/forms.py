import os
import logging
from timezones import zones
from flask import current_app,request,flash
from flask_wtf import FlaskForm as Form
from wtforms import TextField, HiddenField,SelectField,FileField,BooleanField,PasswordField,TextAreaField,RadioField,SelectMultipleField,widgets,validators
from wtforms.validators import Required
from flask_security import current_user
import importlib

from unifispot.utils.translation import _l,_n,_
from unifispot.core.const import font_list
from unifispot.core.models import Wifisite


logger = logging.getLogger('core.forms')

class UserForm(Form):
    email       = TextField(_l('Email'),validators = [Required()])
    displayname = TextField(_l('Name'),validators = [Required()])
    password    = PasswordField(_l('Password')) 
    repassword  = PasswordField(_l('Confirm Password'))
    
    def populate(self):
        pass

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        if self.password and (self.password.data != self.repassword.data):
            self.password.errors.append(_l("Entered passwords didn't match"))
            return False
        return True

class AccountForm(Form):
    unifi_server    = TextField(_l('Controller IP'),validators = [Required()])
    unifi_user      = TextField(_l('Controller Username'),validators = [Required()])
    unifi_pass      = PasswordField(_l('Controller Password'),validators = [Required()])
    unifi_port      = TextField(_l('Controller Port'),validators = [Required()])
    unifi_version   = SelectField(_('Controller API version'),choices=[('v4','V4/V5')])

    def populate(self):
        pass


def get_wifisite_form(baseform=False):
    class F(Form):
        name                = TextField(_l('Name'),validators = [Required()])   
        timezone            = SelectField(_l('Site Timezone'),choices=[])
        client_id           = SelectField(_l('Select Client'),coerce=int,
                                    choices=[],default=0)
        backend_type        = SelectField(_l('Select Site Type'),
                                    choices=[('unifi',"UniFi")],default='unifi')  


        def populate(self,wifisite=None):
            from unifispot.core.models import Client
            clients = Client.query.filter_by(account_id=current_user.account_id).all()
            self.client_id.choices = []
            for client in clients:
                self.client_id.choices.append((client.id,client.displayname))

            self.timezone.choices = [ (tz_name,tz_formated)for tz_offset, tz_name, tz_formated in zones.get_timezones() ]


            if not baseform:
                self.sitekey.choices = []
                #populate sitekey with available options if specific id is specified
                if wifisite and wifisite.backend_type:
                    #try to get available sitekeys
                    try:
                        module_path = current_app.config.get('MODULE_PATH', 'modules')
                        backend_module = ".".join([current_app.name, module_path,
                                                    wifisite.backend_type,'main'])
                        backend = importlib.import_module(backend_module)
                        sitekeys = getattr(backend,'get_sitekeys')(wifisite)
                    except:
                        flash(_l('Error while getting sitelist. \
                                        Please check Controller settings'), 'danger')
                        logger.exception("Exception while trying to get sitekeys for :%s"\
                                        %wifisite.id)
                    else:
                        self.sitekey.choices = sitekeys







    if not baseform:
        setattr(F,'redirect_url',TextField(_l('Redirect Guest to URL'),
                        default='http://www.unifispot.com'))
        setattr(F,'reports_list',TextField(_l('Additional Report Recipients')))
        setattr(F,'reports_type',SelectField(_l('Select Reports Frequency'),
                                    choices=[('none','No Reporting'),('weekly','Weekly Reports'),('monthly','Monthly Reports')]))



        setattr(F,'sitekey',SelectField(_l('Site ID'),choices=[]))
        setattr(F,'unifi_id',TextField(_l('UniFi Site')))
        for lmethod in current_app.config['GUESTLOGIN_MODULES']:
            fieldname = 'auth_%s'%lmethod
            fieldlabel = _l('%s Login'%lmethod.title())
            setattr(F,fieldname,TextField(fieldlabel))        

       

    return F() 


class LandingFilesForm(Form):
    logofile        = FileField('Logo File')
    bgfile          = FileField('Background Image')
    tosfile         = FileField('Select T&C pdf')
    def populate(self):
        pass    

class SimpleLandingPageForm(Form):
    pagebgcolor1     = TextField('Page Background Color')
    gridbgcolor     = TextField('Grid Background Color')
    textcolor       = TextField('Text Color')
    textfont        = SelectField('Select Font',coerce=int,default=2)
    def populate(self):
        #Font options
        fonts = [(idx,font) for idx,font in enumerate(font_list)]
        self.textfont.choices = fonts

class LandingPageForm(Form):
    site_id         = HiddenField('Site ID')
    logofile        = HiddenField('Header File')  
    bgfile          = HiddenField('Background Image')
    pagebgcolor     = TextField('Page Background Color')    
    bgcolor         = TextField('Header Background Color')
    headerlink      = TextField('Header Link')
    basefont        = SelectField('Header Base Font',coerce=int,default=2)
    topbgcolor      = TextField('Top Background Color')
    toptextcolor    = TextField('Top Text Color')
    topfont         = SelectField('Top Font',coerce=int,default=2)
    toptextcont     = TextAreaField('Top Content')
    middlebgcolor   = TextField('Middle Background Color')
    middletextcolor = TextField('Middle Text Color')
    middlefont      = SelectField('Bottom Base Font',coerce=int,default=2)
    bottombgcolor   = TextField('Bottom Background Color') 
    bottomtextcolor = TextField('Bottom Text Color')
    bottomfont      = SelectField('Base Font',coerce=int,default=2)
    footerbgcolor   = TextField('Footer Background Color')
    footertextcolor = TextField('Text Color')
    footerfont      = SelectField('Base Font',coerce=int,default=2)
    footertextcont  = TextAreaField('Footer Content')
    btnbgcolor      = TextField('Button Color')
    btntxtcolor     = TextField('Button Text Color')
    btnlinecolor    = TextField('Button Border Color')
    tosfile         = HiddenField('Select T&C pdf')
    copytextcont    = TextAreaField('Copyright Text')
    

    def populate(self):
        #Font options
        fonts = [(idx,font) for idx,font in enumerate(font_list)]
        self.basefont.choices = fonts
        self.topfont.choices = fonts
        self.middlefont.choices = fonts
        self.bottomfont.choices = fonts
        self.footerfont.choices = fonts

