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
from .models import Emailconfig,Emailauth
from .forms import EmailConfigForm,generate_emailform,EmailOverrideForm

logger =logging.getLogger('email')

module = UnifispotModule('email','login', __name__, template_folder='templates')




class EmailConfigAPI(SiteModuleAPI):

    def get_form_obj(self):
        return EmailConfigForm()

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self): 
        return Emailconfig()

    def get_config_template(self):
        return 'module_config_email.html'

EmailConfigAPI.register(module, route_base='/s/<siteid>/email/config')


def validate_emailconfig(f):
    '''Decorator for validating emailconfig detials. 
        It injects  emailconfigobjects in kwargs

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        wifisite    =  kwargs.get('wifisite')
        guesttrack  =  kwargs.get('guesttrack')
        #get the function name used 
        fname = f.func_name
        #check if site is configured for emaillogin
        if not wifisite.check_login_en('auth_email'):
            guestlog_warn('trying to access email_login for  non configured site',wifisite,guesttrack)
            abort(404)
        #get and validated emailconfig
        emailconfig = Emailconfig.query.filter_by(siteid=wifisite.id).first()
        if not emailconfig:
            guestlog_warn('empty emailconfig, creating default one',wifisite,guesttrack)
            emailconfig = Emailconfig()
            emailconfig.siteid = wifisite.id
            client = Client.query.get(wifisite.client_id)
            emailconfig.account_id = client.account_id
            emailconfig.save()
        kwargs['emailconfig'] = emailconfig
        return f(*args, **kwargs)
    return decorated_function


@module.route('/email/guest/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_emailconfig
@get_loginauth_validator(Emailauth,'emailconfig','email','auth_email')
def guest_login(trackid,guesttrack,wifisite,guestdevice,emailconfig,loginauth):
    ''' Function to called if the site is configured with Email login    
    
    '''    

    #show the configured landing page
    email_form = generate_emailform(emailconfig)
    if email_form.validate_on_submit():
        #assign a guest based on form
        newguest = assign_guest_entry(wifisite,guesttrack,form=email_form)
        #create new auth
        loginauth.populate_auth_details(emailconfig)
        loginauth.reset()     
        loginauth.reset_lastlogin()
        loginauth.state = LOGINAUTH_FIRST
        loginauth.save()
        #update guesttrack   
        guesttrack.state        = GUESTTRACK_POSTLOGIN
        guesttrack.loginauthid  = loginauth.id 
        guesttrack.updatestat('auth_email',1)
        #update guestdevice
        guestdevice.guestid     = newguest.id
        guestdevice.save()
        #update guest
        newguest.demo           = guesttrack.demo
        newguest.devices.append(guestdevice)
        newguest.save()
        guestlog_debug('email_login  new guest track ID:%s'%newguest.id,wifisite,guesttrack)
        return redirect_guest(wifisite,guesttrack)

    landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
    return render_template('guest/%s/email_landing.html'%wifisite.template,\
            wifisite=wifisite,landingpage=landingpage,email_form=email_form,
            trackid=trackid)   

@module.route('/email/override/<trackid>',methods = ['GET', 'POST'])
@validate_track
@validate_emailconfig
def guest_override(trackid,guesttrack,wifisite,guestdevice,emailconfig):
    ''' Function to called if the guest have exceeded daily/monthly limit   
    
    '''    

    return handle_override(guesttrack,wifisite,guestdevice,emailconfig,
            Emailauth,EmailOverrideForm,'limit_override.html',
            'auth_email')
