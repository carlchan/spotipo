from flask import request,abort,render_template,redirect,url_for,flash
import arrow
import logging
from flask_security import current_user
import validators
from functools import wraps
from dateutil import tz


from unifispot.core.app import UnifispotModule
from unifispot.utils.translation import _l,_n,_
from unifispot.core.const import *
from unifispot.core.models import Wifisite,Client,Landingpage
from unifispot.core.guestutils import validate_track,init_track,redirect_guest,\
                                guestlog_warn,guestlog_info,guestlog_error,\
                                guestlog_debug,guestlog_exception,\
                                assign_guest_entry,validate_loginauth_usage,\
                                get_loginauth_validator,handle_override

from unifispot.core.baseviews import SiteModuleAPI
from .models import Phoneconfig,Phoneauth
from .forms import PhoneConfigForm,generate_phoneform,PhoneOverrideForm

logger =logging.getLogger('phone')

module = UnifispotModule('phone','login', __name__, template_folder='templates')




class PhoneConfigAPI(SiteModuleAPI):

    def get_form_obj(self):
        return PhoneConfigForm()

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self): 
        return Phoneconfig()

    def get_config_template(self):
        return 'module_config_phone.html'

PhoneConfigAPI.register(module, route_base='/s/<siteid>/phone/config')


def validate_phoneconfig(f):
    '''Decorator for validating phoneconfig detials. 
        It injects  phoneconfigobjects in kwargs

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        wifisite    =  kwargs.get('wifisite')
        guesttrack  =  kwargs.get('guesttrack')
        #get the function name used 
        fname = f.func_name
        #check if site is configured for phonelogin
        if not wifisite.check_login_en('auth_phone'):
            guestlog_warn('trying to access phone_login for  non configured site',wifisite,guesttrack)
            abort(404)
        #get and validated phoneconfig
        phoneconfig = Phoneconfig.query.filter_by(siteid=wifisite.id).first()
        if not phoneconfig:
            guestlog_warn('empty phoneconfig, creating default one',wifisite,guesttrack)
            phoneconfig = Phoneconfig()
            phoneconfig.siteid = wifisite.id
            client = Client.query.get(wifisite.client_id)
            phoneconfig.account_id = client.account_id
            phoneconfig.save()
        kwargs['phoneconfig'] = phoneconfig
        return f(*args, **kwargs)
    return decorated_function


@module.route('/phone/guest/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_phoneconfig
@get_loginauth_validator(Phoneauth,'phoneconfig','phone','auth_phone')
def guest_login(trackid,guesttrack,wifisite,guestdevice,phoneconfig,loginauth):
    ''' Function to called if the site is configured with phone login    
    
    '''    

    #show the configured landing page
    phone_form = generate_phoneform(phoneconfig)
    if phone_form.validate_on_submit():
        #assign a guest based on form
        newguest = assign_guest_entry(wifisite,guesttrack,form=phone_form)
        #create new auth
        loginauth.populate_auth_details(phoneconfig)
        loginauth.reset()     
        loginauth.state = LOGINAUTH_FIRST
        loginauth.save()
        #update guesttrack   
        guesttrack.state        = GUESTTRACK_POSTLOGIN
        guesttrack.loginauthid  = loginauth.id 
        guesttrack.updatestat('auth_phone',1)
        #update guestdevice
        guestdevice.guestid     = newguest.id
        guestdevice.save()
        #update guest
        newguest.demo           = guesttrack.demo
        newguest.devices.append(guestdevice)
        newguest.save()
        guestlog_debug('phone_login  new guest track ID:%s'%newguest.id,wifisite,guesttrack)
        return redirect_guest(wifisite,guesttrack)

    landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
    return render_template('guest/%s/phone_landing.html'%wifisite.template,\
            wifisite=wifisite,landingpage=landingpage,phone_form=phone_form,
            trackid=trackid)   

@module.route('/phone/override/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_phoneconfig
def guest_override(trackid,guesttrack,wifisite,guestdevice,phoneconfig):
    ''' Function to called if the guest have exceeded daily/monthly limit   
    
    '''    

    return handle_override(guesttrack,wifisite,guestdevice,phoneconfig,
            Phoneauth,PhoneOverrideForm,'limit_override.html',
            'auth_phone')
