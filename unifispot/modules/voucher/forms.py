from flask_wtf import Form
from wtforms import TextField, HiddenField,BooleanField,TextAreaField,\
                        PasswordField,SelectField,FileField
from wtforms.validators import Required,DataRequired,Email,NumberRange
from wtforms.fields.html5 import EmailField,IntegerField

from unifispot.utils.translation import _l,_n,_
from unifispot.core.const import *

class VoucherConfigForm(Form):
    enable_email        = BooleanField(_l('Email'),default=1)
    enable_firstname    = BooleanField(_l('First Name'),default=1)
    enable_lastname     = BooleanField(_l('Last Name'),default=1)
    enable_dob          = BooleanField(_l('DOB'),default=1)
    enable_extra1       = BooleanField(_l('Extra1'),default=1)    
    enable_extra2       = BooleanField(_l('Extra2'),default=1)    
    mandate_email       = BooleanField(_l('Email'),default=1)
    mandate_firstname   = BooleanField(_l('First Name'),default=1)
    mandate_lastname    = BooleanField(_l('Last Name'),default=1)
    mandate_dob         = BooleanField(_l('DOB'),default=1)
    mandate_extra1      = BooleanField(_l('Extra1'),default=1)    
    mandate_extra2      = BooleanField(_l('Extra2'),default=1) 
    labelfor_email      = TextField(_l('Email Field'))
    labelfor_firstname  = TextField(_l('Firstname Field'))
    labelfor_lastname   = TextField(_l('Lastname Field'))
    labelfor_dob        = TextField(_l('DOB Field'))
    labelfor_extra1     = TextField(_l('Extra Field1'))
    labelfor_extra2     = TextField(_l('Extra Field2'))


    def populate(self):
        pass


def generate_voucherform(voucherconfig):
    enable_fields   = voucherconfig.enable_fields
    mandate_fields  = voucherconfig.mandate_fields
    labelfor_fields = voucherconfig.labelfor_fields

    class F(Form):
        pass

    setattr(F, 'voucher', TextField('Voucher*',validators = [DataRequired()])) 

    def get_field(fieldname,fieldtype,extravalidators=[]):
        if enable_fields.get('enable_%s'%fieldname):
            label = labelfor_fields.get('labelfor_%s'%fieldname)
            if mandate_fields.get('mandate_%s'%fieldname):
                validators = [Required()]
                validators.extend(extravalidators)
                setattr(F, fieldname, fieldtype('%s*'%label,validators = validators)) 
            else:
                setattr(F, fieldname, fieldtype('%s'%label))    

    get_field('email',EmailField,extravalidators=[Email()])
    get_field('firstname',TextField,extravalidators=[])
    get_field('lastname',TextField,extravalidators=[])
    get_field('dob',TextField,extravalidators=[])
    get_field('extra1',TextField,extravalidators=[])
    get_field('extra2',TextField,extravalidators=[])


    return F()        

class VoucherDesignForm(Form):
    site_id         = HiddenField(_l('Site ID'))
    logofile        = HiddenField(_l('Header File'))   
    bgcolor         = TextField(_l('Background Color'))
    txtcolor        = TextField(_l('Text Color'))
    bordercolor     = TextField(_l('Border Color'))
    showlogo        = BooleanField(_l('Show Logo'),default=1)     
    shownotes       = BooleanField(_l('Show Notes'),default=1)
    showqr          = BooleanField(_l('Show QRcode'),default=1)
    showduration    = BooleanField(_l('Show Duration'),default=1)
    showdata        = BooleanField(_l('Show Data Limit'),default=1)
    showspeed       = BooleanField(_l('Show Speed Limit'),default=1)
    def populate(self):
        pass    

class VoucherFilesForm(Form):
    actuallogofile        = FileField(_l('Logo File'))
    def populate(self):
        pass        

class VoucherForm(Form):  
    duration_val    = IntegerField(_l("Duration"),validators = [DataRequired()])
    batchid         = IntegerField(_l("Batch ID"),[DataRequired(),NumberRange(min=1000,
                            max=9999,message=_l('Batch ID should be a 4 digit number'))])
    notes           = TextField(_l("Note"))
    number          = IntegerField(_l("Create"),validators = [DataRequired()])
    bytes_t         = IntegerField(_l("Total Data in Mb"))
    duration_type   = SelectField(_l("Select"),coerce=int,
                            choices=[(1,'Hours'),(2,'Days'),(3,'Months')] )  
    num_devices     = IntegerField(_l("Devices Allowed"),validators = [DataRequired()])  
    speed_dl        = IntegerField(_l("Download Speed"))
    speed_ul        = IntegerField(_l("Upload Speed"))
    def populate(self):
        pass        