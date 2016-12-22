from flask_wtf import Form
from wtforms import TextField, HiddenField,BooleanField,TextAreaField,\
                        IntegerField,PasswordField,SelectField
from wtforms.validators import Required,DataRequired,Email
from wtforms.fields.html5 import EmailField

from unifispot.core.const import *
from unifispot.utils.translation import _l,_n,_

class FbConfigForm(Form):
    data_limit          = IntegerField(_l('Data Limit(Mb)',default=0))
    time_limit          = IntegerField(_l('Time Limit(Min)',default=0))
    speed_ul            = IntegerField(_l('Ul Speed Limit(Kbps)',default=0))
    speed_dl            = IntegerField(_l('DL Speed Limit(Kbps)',default=0))
    auth_fb_like        = BooleanField(_l('Ask for Like',default=1)) 
    auth_fb_post        = BooleanField(_l('Ask for Checkin',default=1))
    fb_appid            = TextField(_l('FB APP ID'))
    fb_app_secret       = TextField(_l('FB APP Secret'))
    fb_page             = TextField(_l('FB Page'))
    session_limit_control= SelectField(_l('Restrict Sessions'),coerce=int,choices=[])
    session_overridepass= TextField(_l('Override Password'))
    relogin_policy      = SelectField(_l('Guest has to login'),choices=[])
    def populate(self):
        self.session_limit_control.choices = [(0,'Never'),(1,'Daily'),(2,'Monthly')]
        self.relogin_policy.choices=[('always','Always'),('onetime','One Time'),
                                        ('monthly','Monthly')]

class CheckinForm(Form):
    message = TextAreaField('Optional Message')        

class FbOverrideForm(Form):
    password            = PasswordField(_l('Password'),validators = [Required()])
