from flask_wtf import Form
from wtforms import TextField, HiddenField,BooleanField,TextAreaField,\
                        IntegerField,PasswordField,SelectField
from wtforms.validators import Required,DataRequired,Email
from wtforms.fields.html5 import EmailField

from unifispot.core.const import *
from unifispot.utils.translation import _l,_n,_



def generate_phoneform(emailconfig):
    enable_fields   = emailconfig.enable_fields
    mandate_fields  = emailconfig.mandate_fields
    labelfor_fields = emailconfig.labelfor_fields

    class F(Form):
        pass

    def get_field(fieldname,fieldtype,extravalidators=[]):
        if enable_fields.get('enable_%s'%fieldname):
            label = labelfor_fields.get('labelfor_%s'%fieldname)
            if mandate_fields.get('mandate_%s'%fieldname):
                validators = [Required()]
                validators.extend(extravalidators)
                setattr(F, fieldname, fieldtype('%s*'%label,validators = validators)) 
            else:
                setattr(F, fieldname, fieldtype('%s'%label))    

    get_field('phonenumber',TextField,extravalidators=[DataRequired()])
    get_field('firstname',TextField,extravalidators=[])
    get_field('lastname',TextField,extravalidators=[])
    get_field('dob',TextField,extravalidators=[])
    get_field('extra1',TextField,extravalidators=[])
    get_field('extra2',TextField,extravalidators=[])


    return F()

class PhoneConfigForm(Form):
    enable_phonenumber  = BooleanField(_l('Phone'),default=1)
    enable_firstname    = BooleanField(_l('First Name'),default=1)
    enable_lastname     = BooleanField(_l('Last Name'),default=1)
    enable_dob          = BooleanField(_l('DOB'),default=1)
    enable_extra1       = BooleanField(_l('Extra1'),default=1)    
    enable_extra2       = BooleanField(_l('Extra2'),default=1)    
    mandate_phonenumber = BooleanField(_l('Phone'),default=1)
    mandate_firstname   = BooleanField(_l('First Name'),default=1)
    mandate_lastname    = BooleanField(_l('Last Name'),default=1)
    mandate_dob         = BooleanField(_l('DOB'),default=1)
    mandate_extra1      = BooleanField(_l('Extra1'),default=1)    
    mandate_extra2      = BooleanField(_l('Extra2'),default=1) 
    labelfor_phonenumber= TextField(_l('Phone Number'))
    labelfor_firstname  = TextField(_l('Firstname Field'))
    labelfor_lastname   = TextField(_l('Lastname Field'))
    labelfor_dob        = TextField(_l('DOB Field'))
    labelfor_extra1     = TextField(_l('Extra Field1'))
    labelfor_extra2     = TextField(_l('Extra Field2'))
    data_limit          = IntegerField(_l('Data Limit(Mb)'),default=0)
    time_limit          = IntegerField(_l('Time Limit(Min)'),default=0)
    speed_ul            = IntegerField(_l('Ul Speed Limit(Kbps)'),default=0)
    speed_dl            = IntegerField(_l('DL Speed Limit(Kbps)'),default=0)
    session_limit_control= SelectField(_l('Restrict Sessions'),coerce=int,choices=[])
    session_overridepass= TextField(_l('Override Password'))
    relogin_policy      = SelectField(_l('Guest has to login'),choices=[])
    def populate(self):
        self.session_limit_control.choices = [(0,_l('No Limit')),
                            (1,_l('Daily')),(2,_l('Monthly'))]
        self.relogin_policy.choices=[('always','Always'),('onetime','One Time'),
                                        ('monthly','Monthly')]
class PhoneOverrideForm(Form):
    password            = PasswordField(_l('Password'),validators = [Required()])

   