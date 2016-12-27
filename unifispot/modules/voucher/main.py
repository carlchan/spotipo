from flask import request,abort,render_template,redirect,url_for,jsonify,flash
import arrow
import logging
import uuid
from random import randint
from flask_security import current_user,login_required
import validators
from functools import wraps
from flask_menu.classy import classy_menu_item
from flask_classful import FlaskView
from flask_menu.classy import register_flaskview
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from sqlalchemy import and_,or_


from unifispot.core.app import UnifispotModule
from unifispot.utils.translation import _l,_n,_
from unifispot.core.db import db
from unifispot.core.templates import render_dt_buttons
from unifispot.core.const import *
from unifispot.core.utils import  validate_site_ownership,site_menu,get_form_errors
from unifispot.core.models import Wifisite,Client,Landingpage
from unifispot.core.guestutils import validate_track,init_track,redirect_guest,\
                                guestlog_warn,guestlog_info,guestlog_error,\
                                guestlog_debug,guestlog_exception,assign_guest_entry

from unifispot.core.baseviews import SiteModuleAPI,SiteModuleElementAPI
from .models import Voucherconfig,Voucherdesign,Voucher,Voucherauth
from .forms import VoucherConfigForm,VoucherDesignForm,VoucherForm,\
            VoucherFilesForm,generate_voucherform

logger =logging.getLogger('voucher')

module = UnifispotModule('voucher','login', __name__, template_folder='templates')


class VoucherConfigAPI(SiteModuleAPI):

    def get_form_obj(self):
        return VoucherConfigForm()

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self): 
        return Voucherconfig()

    def get_config_template(self):
        return 'module_config_voucher.html'

VoucherConfigAPI.register(module, route_base='/s/<siteid>/voucher/config')

class VoucherDesignAPI(SiteModuleAPI):

    def get_form_obj(self):
        return VoucherDesignForm()

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self): 
        return Voucherdesign()

    #index method will return json
    def index(self,siteid):
        item = self.get_modal_obj().query.filter_by(siteid=siteid).first()
        if not item:
            item = self.get_modal_obj()
            item.siteid = siteid
            item.save()          
        return jsonify({'status':1,'data':item.to_dict()}) 

VoucherDesignAPI.register(module, route_base='/s/<siteid>/voucher/design/api')
class VoucherDesignView(FlaskView):


    @classy_menu_item('.voucher.design', _l('Design'), order=1,
                        visible_when=site_menu)
    def index(self,siteid):
        decorators = [login_required,validate_site_ownership]


        voucherdesignform = VoucherDesignForm()
        voucherdesignform.populate()

        voucherfilesform =VoucherFilesForm()
        fakevoucher = Voucher(bytes_t=100,voucher='1234567890',
                        duration_type=1,duration_val=1,speed_dl=256,speed_ul=100)
        voucherdesign = Voucherdesign.query.filter_by(siteid=siteid).first()        
        
        return render_template('voucher_designer.html',voucherdesignform=voucherdesignform,
                             siteid=siteid,voucherfilesform=voucherfilesform,
                             fakevoucher=fakevoucher,voucherdesign=voucherdesign)


VoucherDesignView.register(module, route_base='/s/<siteid>/voucher/design/') 
register_flaskview(module, VoucherDesignView)



class VoucherAPI(SiteModuleElementAPI):

    def _show_btn(row):
        '''Create Edit and Delete buttons in datatable corresponding to the ID

        '''

        return '''<a class="btn btn-danger btn-xs delete" 
                href="#" id="%s" alt="Delete">
               Delete</a><a class="btn btn-primary btn-xs print" 
                href="#" id="%s" alt="Print">
               Print</a>'''%(row.id,row.id)



    def _show_duration(row):
        dur_types= { 1:'Minutes',2:'Hrs',3:'Days'}
        if row.duration_val:
            return '%s %s'%(row.duration_val,
                                dur_types[row.duration_type])
        else:
            return '<span class="label label-info">Unlimited</span>'

    def _show_used(row):
        if row.used:
            return '<span class="label label-warning">Used</span>'
        else:
            return '<span class="label label-primary">Not Used</span>'

    def _show_details(row):
        data = '%sMb'%row.bytes_t if row.bytes_t else 'Unlimited'
        speed_ul = '%sKbps'%row.speed_ul if row.speed_ul else 'Unlimited'
        speed_dl = '%sKbps'%row.speed_dl if row.speed_dl else 'Unlimited'
        return 'Data:%s</br> DL:%s </br> UL:%s'%(data,speed_dl,speed_ul)


    #columns that will be shown in the datatable
    displaycolumns = ['voucher','num_devices','duration_val',
                            'bytes_t','used','notes','id']
    displayfilters = {'id' :_show_btn, 'used':_show_used,
                        'duration_val':_show_duration,'bytes_t':_show_details}

    def get_modal_obj(self):
        return Voucher()

    def get_form_obj(self):
        return VoucherForm()

    def get_name(self):
        return 'Voucher'

    def create_voucher(self):
        range_start = 10**(4)
        range_end = (10**5)-1
        return randint(range_start, range_end)        

    #need to overide post
    def post(self,siteid):
        itemform = self.get_form_obj()
        itemform.populate()
        if itemform.validate_on_submit(): 
            try:
                item = self.get_modal_obj()
                item.populate_from_form(itemform)
                item.save()
                #always assign siteid while creation
                item.siteid = siteid
                item.populate_from_dict(self.get_extrafields_modal())

                cnt = 0               
                while cnt < int(itemform.number.data):                         
                    try:
                        item = self.get_modal_obj()  
                        item.populate_from_form(itemform)          
                        #create voucher
                        item.voucher = '%s%s'%(itemform.batchid.data,
                                        self.create_voucher())
                        #always assign siteid while creation
                        item.siteid = siteid
                        item.populate_from_dict(self.get_extrafields_modal())                         
                        db.session.add(item)
                        db.session.commit()
                    except IntegrityError: #check for unique voucherID
                        db.session.rollback()
                    else:
                        cnt = cnt + 1
            except SQLAlchemyError as exception:
                logger.exception('UserID:%s submited form caused exception'\
                        %(current_user.id))
                return jsonify({'status':0,'data':{}, 'msg':_('Error while creating %(name)s'\
                        ,name=self.get_name())}) 
            return jsonify({'status':1,'data':{}, 'msg':_('Successfully added %(name)s'\
                        ,name=self.get_name())}) 

        else:
            logger.debug('UserID:%s submited form with errors:%s'\
                         %(current_user.id,get_form_errors(itemform)))            
            return jsonify({'status':0,'data':{}, 'msg':get_form_errors(itemform)})        

VoucherAPI.register(module, route_base='/s/<siteid>/voucher/vouchers/api/')


class VoucherView(FlaskView):


    @classy_menu_item('.voucher.vouchers', _l('View'), order=0,
                        visible_when=site_menu)
    @classy_menu_item('.voucher', _l('Voucher'), order=7,icon='fa-money',
                        visible_when=site_menu)
    def index(self,siteid):
        decorators = [login_required,validate_site_ownership]

        voucherform = VoucherForm()
        voucherform.populate()
        
        return render_template('vouchers.html',voucherform=voucherform,
                             siteid=siteid)


VoucherView.register(module, route_base='/s/<siteid>/voucher/vouchers/') 
register_flaskview(module, VoucherView)



@module.route('/s/<siteid>/voucher/print/')
@module.route('/s/<siteid>/voucher/print/<voucherid>')
@login_required
@validate_site_ownership
def voucher_print(siteid=None,voucherid=None):
    #Validate SiteID
    wifisite        = Wifisite.query.filter_by(id=siteid).first()
    if not wifisite:
        logger.warn("Site Manage URL called with invalid paramters site_id:%s userid:%s"%(siteid,current_user.id))
        abort(404)
    if voucherid:
         vouchers = Voucher.query.filter(and_(Voucher.siteid==siteid,
            Voucher.used == False,
            Voucher.id==voucherid)).all()
    else: 
        vouchers = Voucher.query.filter(and_(Voucher.siteid==siteid,
                    Voucher.used == False)).all()
    voucherdesign = Voucherdesign.query.filter_by(siteid=siteid).first()
    return render_template("voucher_print.html",vouchers=vouchers,voucherdesign=voucherdesign)


##------guest views----------------------------------------

def validate_voucherconfig(f):
    '''Decorator for validating voucherconfig detials. 
        It injects  voucherconfig in kwargs

    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        wifisite    =  kwargs.get('wifisite')
        guesttrack  =  kwargs.get('guesttrack')
        guestdevice  =  kwargs.get('guestdevice')
        #get the function name used 
        fname = f.func_name
        #check if site is configured for emaillogin
        if not wifisite.check_login_en('auth_voucher'):
            guestlog_warn('trying to access voucher login for  \
                    non configured site',wifisite,guesttrack)
            abort(404)
        #get and validated emailconfig
        voucherconfig = Voucherconfig.query.filter_by(siteid=wifisite.id).first()
        if not voucherconfig:
            guestlog_warn('empty voucherconfig, aborting',wifisite,guesttrack)
            abort(404)
        kwargs['voucherconfig'] = voucherconfig
        #get paymentauth for this device
        voucherauth = Voucherauth.query.filter_by(siteid=wifisite.id,
                        deviceid=guestdevice.id).first()
        if not voucherauth:
            guestlog_debug('in %s empty Paymentauth,creating default one'%fname,
                                wifisite,guesttrack)
            voucherauth = Voucherauth(siteid=wifisite.id,deviceid=guestdevice.id,
                                    account_id=wifisite.account_id)
            voucherauth.save()        
        kwargs['voucherauth'] = voucherauth
        return f(*args, **kwargs)
    return decorated_function

@module.route('/voucher/login/<trackid>',methods = ['GET', 'POST'])
@module.route('/voucher/login/<trackid>/<voucherid>',methods = ['GET', 'POST'])
@validate_track
@validate_voucherconfig
def guest_login(trackid,guesttrack,wifisite,guestdevice,voucherconfig,voucherauth,voucherid=None):
    ''' Function to called if the site is configured with payment login    
    
    '''   
    #show the configured landing page
    voucher_form = generate_voucherform(voucherconfig)
    if voucher_form.validate_on_submit():
        voucher = Voucher.query.filter(and_(Voucher.siteid== wifisite.id,
                    Voucher.voucher==voucher_form.voucher.data)).first()
        if voucher:
            #check and update validity of paymentaccount
            (status,msg) = voucher.check_and_update_validity(voucherauth)
            if status:            
                #assign a guest based on form
                newguest = assign_guest_entry(wifisite,guesttrack,form=voucher_form)
                #update guesttrack   
                guesttrack.state        = GUESTTRACK_POSTLOGIN
                guesttrack.loginauthid  = voucherauth.id 
                guesttrack.updatestat('auth_voucher',1)
                guesttrack.save()
                #update guestdevice
                guestdevice.guestid     = newguest.id
                guestdevice.save()
                #update guest
                newguest.demo           = guesttrack.demo
                newguest.devices.append(guestdevice)
                newguest.save()
                guestlog_debug('voucher_login  new guest track ID:%s'%\
                                newguest.id,wifisite,guesttrack)
                return redirect_guest(wifisite,guesttrack)
            else:
                flash(msg, 'danger')
                guestlog_warn('in voucher.guest_login limit expired',
                    wifisite,guesttrack)                  
        else:
            #transaction failed! display msg
            flash(_l('Wrong voucher entry'), 'danger')
            guestlog_warn('in voucher.guest_login wrong voucher id',
                    wifisite,guesttrack)        

    landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
    return render_template('guest/%s/voucher_landing.html'%wifisite.template,\
            wifisite=wifisite,landingpage=landingpage,voucher_form=voucher_form,
            trackid=trackid)    