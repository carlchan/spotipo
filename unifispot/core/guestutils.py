from functools import wraps
import logging
import arrow
import uuid
from flask import abort,current_app,url_for,redirect,flash
from flask import render_template
from flask_security import current_user
from sqlalchemy import and_,or_
from flask import request
from dateutil import tz
import validators

from unifispot.core.models import Wifisite,Guesttrack,Device,Guest,\
                                Landingpage
from unifispot.core.const import *
from unifispot.utils.translation import _l,_n,_

logger = logging.getLogger()

def init_track(wifisite,guestmac,apmac=None,origurl=None,demo=0):
    '''Method to create a track, if an already existing guestrack is found, use that

    '''
    timelimit     = arrow.utcnow().replace(seconds= -current_app.config['GUESTTRACK_LIFETIME']).naive

    if not demo:
        guesttrack  = Guesttrack.query.filter(and_(Guesttrack.siteid==wifisite.id,Guesttrack.devicemac==guestmac,\
                    Guesttrack.timestamp >= timelimit)).first()
    else:
        guesttrack = None # always create new guestrack for demo
    if not guesttrack:
        guesttrack  = Guesttrack(siteid=wifisite.id,devicemac=guestmac,apmac=apmac)
                       
        guesttrack.trackid   = str(uuid.uuid4())
        guesttrack.demo      = demo
        guesttrack.origurl   = origurl
        guesttrack.save()

    #update visit counter
    guesttrack.increamentstat('num_visits')

    #Check if the device was ever logged
    guestdevice =  Device.query.filter_by(devicemac=guestmac,siteid=wifisite.id).first()
    #check for guest device
    if not guestdevice:
        #device was never logged, create a new device
        guestdevice = Device(devicemac=guestmac,siteid=wifisite.id)
        guestdevice.demo = demo
        guestdevice.save()
    guesttrack.deviceid = guestdevice.id
    guesttrack.save()

    return guesttrack


def validate_track(f):
    '''Decorator for validating guesttrack detials. 
        It injects  guest_track,wifisite and device objects in kwargs

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        trackid=  kwargs.get('trackid')
        #get the function name used 
        fname = f.func_name
        #get and validated guesttrack
        guesttrack = Guesttrack.query.filter_by(trackid=trackid).first()
        if not guesttrack:
            logger.error("Called %s with wrong track ID:%s URL:%s"%(fname,trackid,request.url))
            abort(404)
        kwargs['guesttrack'] = guesttrack
        #get and validate wifisite
        wifisite = Wifisite.query.filter_by(id=guesttrack.siteid).first()
        if not wifisite:
            logger.error("Called %s with trackid:%s not connected to any site URL:%s"%\
                            (fname,trackid,request.url))
            abort(404)  
        kwargs['wifisite'] = wifisite
        #get and validate device
        guestdevice = Device.query.filter(and_(Device.siteid==wifisite.id,\
                    Device.devicemac==guesttrack.devicemac)).first()
        if not guestdevice:
            logger.error("Called %s with trackid:%s not connected to any device URL:%s"%\
                            (fname,trackid,request.url))
            abort(404)     
        kwargs['guestdevice'] = guestdevice     
        current_app.logger.debug('Wifiguest Log - Site ID:%s guestdevice MAC:%s just visited %s'%\
                            (wifisite.id,guesttrack.devicemac,request.url))

        return f(*args, **kwargs)
    return decorated_function


def guestlog_warn(msg,wifisite,guesttrack=None):
    if guesttrack:
        logger.warn('Siteid:%s guestrtrack:%s -%s'%(wifisite.id,guesttrack.id,msg))
    else:
        logger.warn('Siteid:%s -%s'%(wifisite.id,msg))

def guestlog_info(msg,wifisite,guesttrack=None):
    if guesttrack:
        logger.info('Siteid:%s guestrtrack:%s -%s'%(wifisite.id,guesttrack.id,msg))
    else:
        logger.info('Siteid:%s -%s'%(wifisite.id,msg))

def guestlog_debug(msg,wifisite,guesttrack=None):
    if guesttrack:
        logger.debug('Siteid:%s guestrtrack:%s -%s'%(wifisite.id,guesttrack.id,msg))
    else:
        logger.debug('Siteid:%s -%s'%(wifisite.id,msg))        

def guestlog_error(msg,wifisite,guesttrack=None):
    if guesttrack:
        logger.error('Siteid:%s guestrtrack:%s -%s'%(wifisite.id,guesttrack.id,msg))
    else:
        logger.error('Siteid:%s -%s'%(wifisite.id,msg))   

def guestlog_exception(msg,wifisite,guesttrack=None):
    if guesttrack:
        logger.exception('Siteid:%s guestrtrack:%s -%s'%(wifisite.id,guesttrack.id,msg))
    else:
        logger.exception('Siteid:%s -%s'%(wifisite.id,msg))                  

def redirect_guest(wifisite,guesttrack):
    #function used for redirecting a guest to right end point


    ##check preauth settings for this site
    if guesttrack.state == GUESTTRACK_PRELOGIN:
        #check if any pre login methods are configured for this site
        guesttrack.state = GUESTTRACK_LOGIN
        guesttrack.save()


    if guesttrack.state == GUESTTRACK_LOGIN:
        ##check auth settings for this site
        methodslist = wifisite.get_methods('auth_methods')
        ##check if QR scan is done
        if wifisite.check_login_en('auth_voucher'):
            url = guesttrack.origurl
            if url:
                voucher = validate_scan2login(url) 
                if voucher:
                    return  redirect(url_for('unifispot.modules.voucher.guest_login',
                                trackid=guesttrack.trackid,voucherid=voucher))
        if len(methodslist) > 1:
            #more than one login type configured
            ltypes =[]
            for method in methodslist:
                name = method.split('_')[1]
                ltypes.append({'url':url_for('unifispot.modules.%s.guest_login'%\
                                name,trackid=guesttrack.trackid),
                              'name':name,
                              'title':name.title()
                    })



            landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
            return render_template('guest/%s/multi_landing.html'%wifisite.template,
                            wifisite=wifisite,landingpage=landingpage,ltypes=ltypes)              

        elif len(methodslist) == 1:
            #only one login type configured
            #redirect guest to guest_login of that module
            #method will be named auth_<module>
            auth_module = methodslist[0].split('_')[1]
            return  redirect(url_for('unifispot.modules.%s.guest_login'%\
                                auth_module,trackid=guesttrack.trackid))
        else:
            #seems no login methods configured,move to post login
            guesttrack.state = GUESTTRACK_POSTLOGIN
            guesttrack.save()


    if guesttrack.state == GUESTTRACK_POSTLOGIN:
        #check if any post login methods are configured for this site
        guesttrack.state = GUESTTRACK_AUTH
        guesttrack.save()

    if guesttrack.state == GUESTTRACK_AUTH:
        #redirect guest to configured backend
        return redirect(url_for('unifispot.modules.%s.guest_auth'%\
                wifisite.backend_type,trackid=guesttrack.trackid))


    if guesttrack.state == GUESTTRACK_POST_AUTH:
        #redirect guest to POST AUTH methods
        redirect_url = wifisite.redirect_url or \
                    current_app.config['DEFAULT_POST_AUTH_URL']
        landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
        return render_template('guest/%s/post_auth.html'%wifisite.template,\
                wifisite=wifisite,landingpage=landingpage,trackid=guesttrack.trackid,
                redirect_url=redirect_url) 
                    

        guestlog_warn('unknown state :%s for guestrack '%guesttrack.state,wifisite,guesttrack)
        abort(404)        
   

def assign_guest_entry(wifisite,guesttrack,form=None,fbprofile=None):
    #method to add/update guest entry and trigger export plugins
    new = False
    
    if form:
        #check if this guest data is already logged
        if hasattr(form,'email'):
            guest = Guest.query.filter_by(email=form.email.data,siteid=wifisite.id).first()
        elif hasattr(form,'phonenumber'):
            guest = Guest.query.filter_by(phonenumber=form.phonenumber.data,siteid=wifisite.id).first()
        if not guest:
            guest = Guest(siteid=wifisite.id)
            new = True
            #update newguestcounter
            guesttrack.updatestat('newguest',1)            
        #update guest
        guest.populate_from_guest_form(form,wifisite)
        guest.save()
    elif fbprofile:
        #check if this guest data is already logged
        guest = Guest.query.filter_by(email=fbprofile.get('email'),siteid=wifisite.id).first()
        if not guest:
            guest = Guest(siteid=wifisite.id)
            new = True
            #update newguestcounter
            guesttrack.updatestat('newguest',1)
        #update guest
        guest.populate_from_fb_profile(fbprofile,wifisite)
        guest.save()
    #call export function if its a new guest
    if new:
        pass
        #celery_export_api.delay(guest.id) 
    return guest


def validate_loginauth_usage(wifisite,guesttrack,loginconfig,loginauth,starttime):
    #------------get and check usage
    (time_usage,data_usage) = loginauth.get_usage(starttime)
    if loginconfig.time_limit and \
            ( loginconfig.time_limit - time_usage) <= 1: #less than 1 min
        guestlog_warn('validate_loginauth_usage timelimit expired LIMIT:%s USAGE:%s'%\
                    (loginconfig.time_limit,time_usage),wifisite,guesttrack)
        return False
        
    elif loginconfig.data_limit and \
            (loginconfig.data_limit - data_usage) <= 1: #less than 1 Mb
        guestlog_warn('validate_loginauth_usage data expiredLIMIT:%s USAGE:%s'%\
                    (loginconfig.data_limit,data_usage),wifisite,guesttrack)
        return False

    #update loginauth details 
    if loginconfig.data_limit:
        loginauth.data_limit = loginconfig.data_limit - data_usage
    else:
        loginauth.data_limit = 1000
    if loginconfig.time_limit:
        loginauth.time_limit = (loginconfig.time_limit - time_usage)
    else:
        loginauth.time_limit = 480
    loginauth.save()
    return True

def guest_auto_relogin_allowed(loginauth,loginconfig):
    if not loginauth or loginconfig :
        return False
    if not loginauth.login_completed():
        return False
    if loginconfig.relogin_policy =='onetime':
        return True
    elif loginconfig.relogin_policy =='always':
        return False
    elif loginconfig.relogin_policy =='monthly':
        #check last login time 
        lastlogin_timelimit = arrow.utcnow().replace(days=30).timestamp
        if arrow.get(loginauth.last_login_at).timestamp >= lastlogin_timelimit:
            return True
        else:
            return False
    else:
        return False


def get_loginauth_validator(AuthModel,lconfigstr,modname,logintypestr):
    ''''    AuthModel - name of auth model (egEmailauth)
            lconfigstr - name of loginconfig instance passed via kwargs
            modname - name of login module using this validor eg email,facebook
            logintypestr - logintype string to be used for updating track stat
                            eg auth_email

            -- tested along with email login
    '''

    def validate_loginauth(f):
        '''Decorator for validating loginauth detials if exsists,
            It injects  loginconfig object in kwargs

        '''
        @wraps(f)
        def decorated_function(*args, **kwargs):
            wifisite    =  kwargs.get('wifisite')
            guesttrack  =  kwargs.get('guesttrack')
            guestdevice =  kwargs.get('guestdevice')
            loginconfig =  kwargs.get(lconfigstr)
            #get the function name used 
            fname = f.func_name
            #get and validated emailauth
            loginauth = AuthModel.query.filter_by(siteid=wifisite.id,
                            deviceid=guestdevice.id).first()
            if not loginauth:
                guestlog_debug('in :%s empty %s, creating default one'%(fname,
                            AuthModel),wifisite,guesttrack)
                loginauth = AuthModel(siteid=wifisite.id,deviceid=guestdevice.id,
                                        account_id=wifisite.account_id)
                loginauth.save()
            elif loginauth.is_blocked():
                flash(_l("Looks like you have been blocked from using WiFi"),'danger')
                landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
                return render_template('guest/%s/base_landing.html'%wifisite.template,\
                        wifisite=wifisite,landingpage=landingpage,trackid=guesttrack.trackid)                 
            elif loginauth.login_completed(loginconfig) and \
                        guest_auto_relogin_allowed(loginauth,loginconfig):
                if loginconfig.is_limited():
                    #email auth from a previous session,
                    #check if its valid still
                    starttime = loginconfig.get_limit_starttime()               

                    expired_url =url_for('unifispot.modules.%s.guest_override'%modname,
                                    trackid=guesttrack.trackid)

                    if not validate_loginauth_usage(wifisite,guesttrack,
                                loginconfig,loginauth,starttime):
                        return redirect(expired_url)
                else:
                    loginauth.time_limit = 480
                    loginauth.data_limit = 1000

                loginauth.state = LOGINAUTH_REPEATED
                loginauth.reset()
                loginauth.save()
                #update guesttrack   
                guesttrack.state        = GUESTTRACK_POSTLOGIN
                guesttrack.loginauthid  = loginauth.id 
                guesttrack.updatestat(logintypestr,1)
                guesttrack.updatestat('relogin',1)
                guesttrack.save()

                guestlog_debug('%s guest   relogin '%modname,
                                    wifisite,guesttrack)
                return redirect_guest(wifisite,guesttrack)
                
            kwargs['loginauth'] = loginauth
            return f(*args, **kwargs)
        return decorated_function    
    return validate_loginauth

def handle_override(guesttrack,wifisite,guestdevice,loginconfig,AuthModel,OverrideForm,templatefile,logintypestr):

    '''method to handle limit override functionality
        guesttrack - track object 
        loginconfig - config instance
        logintypestr - for using in guestrack stat eg auth_email
    '''

    if not loginconfig.is_limited():
        guestlog_debug('guest_override called for unlimited loginconfig',
                            wifisite,guesttrack)
        abort(404)

    loginauth = AuthModel.query.filter_by(siteid=wifisite.id,
                    deviceid=guestdevice.id).first()
    if not loginauth or loginauth.state == LOGINAUTH_INIT:
        guestlog_debug('guest_override called for empty loginauth',
                            wifisite,guesttrack)
        abort(404)

    override_form = OverrideForm()
    if override_form.validate_on_submit():
        if override_form.password.data == loginconfig.session_overridepass:
            #update guesttrack   
            guesttrack.state        = GUESTTRACK_POSTLOGIN
            guesttrack.loginauthid  = loginauth.id 
            guesttrack.save()
            #override all existing sessions
            #reset sessions of the day or month
            tzinfo = tz.gettz(wifisite.timezone)
            starttime = None
            if loginconfig.is_daily_limited():               
                starttime = arrow.now(tzinfo).floor('day').naive

            elif loginconfig.is_monthly_limited():
                starttime = arrow.now(tzinfo).floor('month').naive            
            loginauth.reset_usage(starttime)
            #reset loginauth
            loginauth.reset()
            loginauth.populate_auth_details(loginconfig)
            guestlog_debug('%s override login '%logintypestr,
                        wifisite,guesttrack)
            guesttrack.updatestat(logintypestr,1)
            guesttrack.updatestat('relogin',1)            
            return redirect_guest(wifisite,guesttrack)
        else:
            flash(_l('Wrong password'),'danger')

    landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
    return render_template(templatefile,base=wifisite.template,\
            wifisite=wifisite,landingpage=landingpage,
            override_form=override_form,trackid=guesttrack.trackid)      




def validate_scan2login(url):
    '''Function to validate client's URL and check if its scan2login URL

    '''
    if not validators.url(url):
        return False

    parsed = urlparse(url)


    if not parsed.netloc == 'scan2log.in':
        return False

    voucher_code =  parse_qs(parsed.query).get('voucher')

    if voucher_code:
        return voucher_code
    else:
        return False    