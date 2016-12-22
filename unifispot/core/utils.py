# coding: utf -8
import logging
from functools import wraps
from flask import redirect,url_for,abort,current_app,request,jsonify
from flask_security import current_user
from flask_mail import Message
import hashlib

from unifispot.ext.mail import mail
from unifispot.ext.redis import redis
from unifispot.utils.translation import _l,_n,_
from .models import Role,User,Account,Notification,Admin,Client,Wifisite

logger = logging.getLogger()

def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):   
        if not current_user.is_authenticated:
            logger.debug('User:%s trying to access unathorized URL:%s'%(current_user.id,
                request.url))
            return redirect(url_for('security.login', next=request.url))
        if not current_user.type =='client':
            logger.debug('User:%s trying to access unathorized URL:%s'%(current_user.id,
                request.url))
            return abort(401)           
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            logger.debug('User:%s trying to access unathorized URL:%s'%(current_user.id,
                request.url))
            return redirect(url_for('security.login', next=request.url))
        if not current_user.type =='admin':
            logger.debug('User:%s trying to access unathorized URL:%s'%(current_user.id,
                request.url))
            return abort(401)
        return f(*args, **kwargs)
    return decorated_function 


def allow_only_self(f):
    '''This API is restricted only to self id
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):   
        id = kwargs.get('id')         
        if id and str(id) != str(current_user.id):
            logger.debug('User:%s trying to access unathorized URL:%s'%(current_user.id,
                request.url))
            abort(405)
        return f(*args, **kwargs)
    return decorated_function    

def prevent_self_delete(f):
    '''This API is restricted only to self id
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):   
        id = kwargs.get('id')         
        if request.method == "DELETE" and  str(id) == str(current_user.id):
            logger.debug('User:%s trying to delete himself:%s'%(current_user.id,
                request.url))
            abort(405)
        return f(*args, **kwargs)
    return decorated_function 

def get_account_validator(modeltype):
    def validate_account(f):
        '''This API is used to check if id belongs 
            to the same account
        '''
        @wraps(f)
        def decorated_function(*args, **kwargs):   
            id = kwargs.get('id')         

            if id :
                item = eval(modeltype).query.get(id)
                if not item or item.account_id != current_user.account_id:
                    logger.debug('User:%s trying to access unathorized URL:%s'%\
                        (current_user.id,request.url))
                    abort(401)
            return f(*args, **kwargs)
        return decorated_function 
    return  validate_account

def validate_site_ownership(f):
    '''This API is used to check if siteid belongs 
        to the same account
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs): 
        siteid = kwargs.get('siteid')
        if not siteid:
            logger.debug('UserID:%s trying to :%s with no siteid'\
                %(current_user.id,request.url))
            abort(401)
        wifisite = Wifisite.query.get(siteid)
        if not wifisite:
            logger.debug('UserID:%s trying to :%s with invalid siteid:%s'\
                %(current_user.id,request.url,siteid))
            abort(401)     
        #client can access only his own sites
        if current_user.type == 'client' and wifisite.client_id != current_user.id:
            logger.debug('UserID:%s trying to :%s with siteid:%s  which is now owned by him'\
                %(current_user.id,request.url,siteid))
            abort(401)        
        #admin can access only sites in his account      
        if current_user.type == 'admin' and wifisite.account_id != current_user.account_id:
            logger.debug('UserID:%s trying to :%s with siteid:%s  which is now owned by him'\
                %(current_user.id,request.url,siteid))
            abort(401)           
        return f(*args, **kwargs)
    return decorated_function 
           

def admin_menu():
    '''Function will return True if the user has admin privilege
        and current view is an admin view

    '''
    if current_user.is_authenticated and current_user.type =='admin' and \
        '/a/' in request.path:
        return True
    else:
        return False

def admin_site_menu():
    '''Function will return True if the user has admin privilege
        and current view is an admin view

    '''
    if current_user.is_authenticated and current_user.type =='admin'and \
        '/s/' in request.path:
        return True
    else:
        return False

def site_menu():
    '''Function will return True if the user has admin privilege
        and current view is an admin view

    '''
    if current_user.is_authenticated and '/s/' in request.path:
        return True
    else:
        return False                

def print_form_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            print "Error in the %s field - %s" % \
                (getattr(form, field).label.text,error)

def get_form_errors(form):
    """ Return form errors as string """
    form_errors = ""
    for field, errors in form.errors.items():
        for error in errors:
            form_errors = form_errors+ _l("Error in the %(fieldname)s field - %(errors)s </br>",\
                 fieldname=getattr(form, field).label.text,errors=error)
    return form_errors


def compare_versions(version1,version2):
    '''Compare two versions of format '1.0.0-XXXX' #manjor.minor.patch-CUSTOM

        return 0 if same version
               1 if version1 > version2
               -1 if version1 < version2

    '''
    if version1 == version2:
        return 0
    numeric_v1 = version1.split('-')[0].split('.')
    numeric_v2 = version2.split('-')[0].split('.')
    for idx, val in enumerate(numeric_v1):
        if val > numeric_v2[idx]:
            return 1
        elif val < numeric_v2[idx]:
            return -1


# Email throttling.
EMAIL_THROTTLE = 'unifispot:email_throttle:{md5}'  # Lock.

def send_email(subject, body=None, html=None, recipients=None, throttle=None):
    """Send an email. Optionally throttle the amount an identical email goes out.

    If the throttle argument is set, an md5 checksum derived from the subject, body, html, and recipients is stored in
    Redis with a lock timeout. On the first email sent, the email goes out like normal. But when other emails with the
    same subject, body, html, and recipients is supposed to go out, and the lock hasn't expired yet, the email will be
    dropped and never sent.

    Positional arguments:
    subject -- the subject line of the email.

    Keyword arguments.
    body -- the body of the email (no HTML).
    html -- the body of the email, can be HTML (overrides body).
    recipients -- list or set (not string) of email addresses to send the email to. 
            Defaults to the ADMINS list in the
        Flask config.
    throttle -- time in seconds or datetime.timedelta object between 
                sending identical emails.
    """
    recipients = recipients or current_app.config['ADMINS']
    if throttle is not None:
        md5 = hashlib.md5('{}{}{}{}'.format(subject, body, html, recipients))\
                        .hexdigest()
        seconds = throttle.total_seconds() if hasattr(throttle, 'total_seconds') \
                    else throttle
        lock = redis.lock(EMAIL_THROTTLE.format(md5=md5), timeout=int(seconds))
        have_lock = lock.acquire(blocking=False)
        if not have_lock:
            logger.debug('Suppressing email: {}'.format(subject))
            return
    msg = Message(subject=subject, recipients=recipients, body=body, html=html)
    mail.send(msg)
