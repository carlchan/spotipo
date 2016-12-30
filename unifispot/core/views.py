import logging
import string
import time
import arrow
import random,os
from functools import wraps
from  flask import render_template 
from flask import url_for,flash,redirect
from flask_classful import FlaskView,route
from flask_security import current_user,login_required
from flask import Flask, request, jsonify,abort,current_app
from flask_menu.classy import classy_menu_item
from flask_menu import current_menu
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequestKeyError


from unifispot.utils.translation import _l,_n,_
from unifispot.core.templates import render_dt_buttons
from unifispot.core.db import db
from unifispot.core.models import User,Admin,Client,Wifisite,\
                                    Landingpage,Sitefile,Guest,Account,Notification
from unifispot.core.forms import UserForm,get_wifisite_form,LandingPageForm,\
                                LandingFilesForm,SimpleLandingPageForm,AccountForm
from unifispot.core.baseviews import RESTView,SiteModuleAPI,SiteDataViewAPI
from unifispot.core.utils import allow_only_self,admin_required,\
                get_account_validator,admin_menu,admin_site_menu,site_menu,\
                prevent_self_delete,get_form_errors,validate_site_ownership


logger = logging.getLogger()


class AdminDashboard(FlaskView):
    decorators = [login_required]

    @classy_menu_item('.dashboard', 'Dashboard', order=0,icon='fa-home',
                     visible_when=admin_menu)
    def index(self):
        account = Account.query.get(current_user.account_id)
        if account.firstrun == 1:
            account.firstrun =0
            account.save()
            flash("Please configure your controller details",'warning')
            return redirect(url_for('AccountManage:index'))

        return render_template('core/dashboard.html')



class UserAPI(RESTView):
    ''' View used for user api (profile updation etc)

    '''
    decorators = [login_required,allow_only_self]

    def get_modal_obj(self):
        return User()

    def get_form_obj(self):
        return UserForm()

    def get_name(self):
        return 'User'

    def index(self): 
        abort(405)   

    def post(self): 
        abort(405)             
 
    def delete(self,id): 
        abort(405)  

                 
 
         
class AdminAPI(RESTView):
    ''' View used for Admin api 

    '''
    decorators = [login_required,admin_required,get_account_validator('Admin'),
                    prevent_self_delete]
    displaycolumns = ['email','displayname','id']
    displayfilters = {'id' :render_dt_buttons}

    def get_modal_obj(self):
        return Admin()

    def get_form_obj(self):
        return UserForm()

    def get_name(self):
        return 'Admin'

    def get_extrafields_modal(self):
        return {'account_id':current_user.account_id,'active':1}

class AdminManage(FlaskView):
    decorators = [login_required,admin_required]

    @classy_menu_item('.manage.admin', _l('Admins'), order=0,
                        visible_when=admin_menu)
    @classy_menu_item('.manage', _l('Manage'), order=1,icon='fa-cogs',
                        visible_when=admin_menu)
    def index(self):
        return render_template('core/admins.html')


class ClientAPI(RESTView):
    ''' View used for Admin api 

    '''
    decorators = [login_required,admin_required,get_account_validator('Client')]
    displaycolumns = ['email','displayname','id']
    displayfilters = {'id' :render_dt_buttons}    

    def get_modal_obj(self):
        return Client()

    def get_form_obj(self):
        return UserForm()

    def get_name(self):
        return 'Client'

    def get_extrafields_modal(self):
        return {'account_id':current_user.account_id,'active':1}

class ClientManage(FlaskView):
    decorators = [login_required,admin_required]

    @classy_menu_item('.manage.client', _l('Clients'),visible_when=admin_menu)
    def index(self):
        return render_template('core/clients.html')

class NotificationAPI(RESTView):
    ''' View used for user api (profile updation etc)

    '''
    decorators = [login_required]

    def get_modal_obj(self):
        return User()

    def get_form_obj(self):
        return UserForm()

    def get_name(self):
        return 'User'

    def index(self): 
        abort(405)   

    def post(self): 
        abort(405)             
 
    def delete(self,id): 
        abort(405)  

    def put(self,id): 
        mark = Notification.mark_as_read(id,current_user.account_id)
        if mark:
            return jsonify({'status': 1,'msg':'Suucessfully marked as read'})
        else:
            return jsonify({'status': 0,'msg':'Error Occured while marking'})

class AccountAPI(RESTView):
    ''' View used for Account api 

    '''
    decorators = [login_required,admin_required]

    def get_modal_obj(self):
        return Account()

    def get_form_obj(self):
        return AccountForm()

    def get_name(self):
        return 'Settings'

    def index(self): 
        abort(405)   

    def post(self): 
        abort(405)             
 
    def delete(self,id): 
        abort(405)     

class AccountManage(FlaskView):
    decorators = [login_required,admin_required]

    @classy_menu_item('.manage.settings', _l('Settings'),visible_when=admin_menu)
    def index(self):
        settingsform = AccountForm()
        return render_template('core/settings.html',settingsform=settingsform)        

class WifisiteAPI(RESTView):
    ''' View used for Wifisite api, returns rendered form when calling form

    '''
    decorators = [login_required,admin_required,get_account_validator('Wifisite')]
    displaycolumns = []

    def get_modal_obj(self):
        return Wifisite()

    def get_form_obj(self):
        return get_wifisite_form()

    def get_name(self):
        return 'Site'

    def get_extrafields_modal(self):
        return {'account_id':current_user.account_id}

    def index(self):
        '''Returns a list of { 'id':siteid ,'name':sitename,'url':dashbordurl} dicts,

            used for site list drop down
        '''
        try:
            data = []
            sites = self.get_modal_obj().query.filter_by(account_id=
                        current_user.account_id).all()
            for site in sites:
                data.append({'id':site.id,'name':site.name,
                                'url':url_for('SiteDashboard:index',siteid=site.id)})
        except:
            logger.exception("Exception while trying to get site list")
            return jsonify({'status':0,'data':'','msg':_l('Error in getting site list')})
        else:
            return jsonify({'status':1,'data':data,'msg':'','sites_available':1})
    
    def post(self):
        ''' Need custom post here to handle wifisite creation with limited parameters

        '''
        itemform = get_wifisite_form(baseform=True)
        itemform.populate()
        if itemform.validate_on_submit(): 
            try:
                item = self.get_modal_obj()
                item.site_from_baseform(itemform)
                item.populate_from_dict(self.get_extrafields_modal())
                item.save()
                #create a landing page along with site
                landingpage = Landingpage()
                landingpage.siteid = item.id 
                landingpage.save()

            except SQLAlchemyError as exception:
                db.session.rollback()
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

    def put(self,id):
        ''' Need custom post here to handle to configure sitekey etc

        '''        
        item = self.get_modal_obj().query.get(id) 
        if item:
            itemform = self.get_form_obj()
            itemform.populate(item)
            if itemform.validate_on_submit(): 
                try:
                    item.populate_from_form(itemform)
                    item.save()
                    item.populate_from_dict(self.get_extrafields_modal())
                except SQLAlchemyError as exception:
                    logger.exception('UserID:%s submited form caused exception'\
                            %(current_user.id))
                    return jsonify({'status':0,'data':{}, 'msg':_('Error while updating %(name)s'\
                            ,name=self.get_name())}) 
                return jsonify({'status':1,'data':{}, 'msg':_('Successfully updated %(name)s'\
                            ,name=self.get_name())}) 

            else:
                logger.debug('UserID:%s submited form with errors:%s'\
                             %(current_user.id,get_form_errors(itemform)))            
                return jsonify({'status':0,'data':{}, 'msg':get_form_errors(itemform)}) 
        else:
            logger.debug('UserID:%s trying to update unknown ID:%s of :%s'\
                    %(current_user.id,id,self.get_name()))
            return jsonify({'status':0,'data':{}, 'msg':_l('Unknown :%(name)s ID \
                    specified',name=self.get_name())})


class WifisiteManage(FlaskView):
    decorators = [login_required,admin_required]

    @classy_menu_item('.settings', _l('Settings'),icon='fa-cogs',
                            visible_when=admin_site_menu,order=1)
    def index(self,siteid):
        wifisite = Wifisite.query.get(siteid)
        siteform = get_wifisite_form()
        siteform.populate(wifisite)
        return render_template('core/site-settings.html',siteid=siteid,
                                siteform=siteform)        


class SiteDashboard(FlaskView):
    decorators = [login_required]


    @classy_menu_item('.sitedash', _l('Dashboard'),icon='fa-home',
                            visible_when=site_menu,order=0)
    def index(self,siteid):
        return render_template('core/site-dashboard.html',siteid=siteid)           


class LandingpageAPI(FlaskView):
    ''' View used for Landingpage api

    '''
    decorators = [login_required,admin_required,validate_site_ownership]

    def get_modal_obj(self):
        return Landingpage()

    def get_form_obj(self):
        return LandingPageForm()

    def get_name(self):
        return 'Landingpage'
        
    def get_extrafields_modal(self):
        #should return a dict with modal fields as keys
        #and values to be set as vals
        return {}

    def index(self,siteid):
        item = self.get_modal_obj().query.filter_by(siteid=siteid).first()
        if item:
             return jsonify({'status':1,'data':item.to_dict()})   
        else:
            logger.debug('UserID:%s trying to access emptry :%s of site :%s'\
                    %(current_user.id,self.get_name(),siteid))
            return jsonify({'status':1,'data':{}, 'msg':''})   

    def post(self,siteid):
        item = self.get_modal_obj().query.filter_by(siteid=siteid).first()  
        if not item:
            item =  self.get_modal_obj()
            item.siteid = siteid
        itemform = self.get_form_obj()
        itemform.populate()
        if itemform.validate_on_submit(): 
            try:
                item.populate_from_form(itemform)
                item.save()
                item.populate_from_dict(self.get_extrafields_modal())
            except SQLAlchemyError as exception:
                db.session.rollback()
                logger.exception('UserID:%s submited form caused exception'\
                        %(current_user.id))
                return jsonify({'status':0,'data':{}, 'msg':_('Error while updating %(name)s'\
                        ,name=self.get_name())}) 
            return jsonify({'status':1,'data':{}, 'msg':_('Successfully updated %(name)s'\
                        ,name=self.get_name())}) 

        else:
            logger.debug('UserID:%s submited form with errors:%s'\
                         %(current_user.id,get_form_errors(itemform)))            
            return jsonify({'status':0,'data':{}, 'msg':get_form_errors(itemform)})      

class FileAPI(SiteModuleAPI):
    ''' View used for Landingpage api

    '''

    def get_modal_obj(self):
        return Sitefile()

    def get_name(self):
        return 'File'

    def index(self,siteid):
        pass

    def __filename_gen(self,filename,size=6, chars=string.ascii_uppercase + string.digits):
        #get file extension if exists and add to the randomly 
        ##generated filename
        file_extension = ''
        if '.' in filename:
            file_extension = '.'+filename.rsplit('.', 1)[1]
        fname= ''.join(random.choice(chars) for _ in range(size))
        return fname + file_extension

    def __handleUpload(self,file,):
        """ Generic handler for uploading file, 
            Based on https://bitbucket.org/adampetrovic/flask-uploader/
            And http://stackoverflow.com/questions/17584328/any-current-examples-using-flask-and-jquery-file-upload-by-blueimp

        """
        basefolder = current_app.config['PROJECT_ROOT']
        uploadfolder = current_app.config['UPLOAD_DIR'] 
        if not file:
            return None
        else :
            filename = time.strftime('%Y%m%d-%H%M%S') + '-' \
                                + self.__filename_gen(file.filename)
            full_file_name = os.path.join(basefolder,'static',uploadfolder, \
                                            filename)
            file.save(full_file_name)
            rel_filepath = '/static/'+uploadfolder +'/'+ filename
     
            return {'filename':rel_filepath,'thumbname':''}
    def post(self,siteid):
        #upload new file
        try:
            try:
                upload_file = request.files['logofile']
            except BadRequestKeyError:
                try:
                    upload_file = request.files['bgfile']
                except BadRequestKeyError:
                    try:
                        upload_file = request.files['tosfile']
                    except BadRequestKeyError:
                        return jsonify({'status': '0',
                                        'msg':_('Unknown file!! only logofile,\
                                        bgfile and tosfile are allowed')})
            if upload_file:
                filetoupload = self.__handleUpload(upload_file)   
                if not filetoupload  :
                    return jsonify({'status': '0','msg':_('Error Occured \
                                         hwwebmile trying to upload file')})
                newfile = self.get_modal_obj()
                newfile.file_location   = filetoupload['filename']
                newfile.file_label = secure_filename(upload_file.filename)
                newfile.siteid = siteid
                try:
                    db.session.add(newfile)
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    return jsonify({'status': None,'msg':_('Value already \
                                exists in the database for this file ')})
                else:
                    return jsonify({'status': 1,'singleitem':newfile.to_dict(),
                        'msg':_('Uploaded new file')})
        except:
            logger.exception("Fileupload exception")
            return jsonify({'status': '0','msg':_('Error Occured While trying \
                to upload file')})            

    
class LandingpageManage(FlaskView):
    decorators = [login_required,admin_required]

    @classy_menu_item('.landingpage', _l('Landingpage'),icon='fa-desktop',
                            visible_when=admin_site_menu,order=2)
    def index(self,siteid):
        landingform = LandingPageForm()
        landingform.populate()
        simplelandingpageform = SimpleLandingPageForm()
        simplelandingpageform.populate()
        landingfilesform = LandingFilesForm()
        landingfilesform.populate()
        wifisite = Wifisite.query.get(siteid)
        return render_template('core/site-landing.html',siteid=siteid,
                                landingform=landingform,simplelandingpageform=simplelandingpageform,
                                landingfilesform=landingfilesform,wifisite=wifisite)        

class LandingpagePreview(FlaskView):
    decorators = [login_required,admin_required]

    def index(self,siteid):
        wifisite = Wifisite.query.get(siteid)
        landingpage = Landingpage.query.filter_by(siteid=wifisite.id).first()
        methodslist = wifisite.get_methods('auth_methods')
        ltypes =[]
        for method in methodslist:
            name = method.split('_')[1]
            ltypes.append({'url':url_for('unifispot.modules.%s.guest_login'%\
                            name,trackid=''),
                          'name':name,
                          'title':name.title()
                })        
        return render_template('guest/%s/multi_landing.html'%wifisite.template,\
                wifisite=wifisite,landingpage=landingpage,ltypes=ltypes)        



class GuestViewAPI(SiteDataViewAPI):
    #columns that will be shown in the datatable
    displaycolumns = ['email','firstname','lastname',
        'phonenumber','agerange','details','created_at']

    def _show_details(row):
        return ','.join('{}:{}'.format(k, v) for k,v in \
                    sorted(row.details.items()))

    def _show_date(row):
        return arrow.get(row.created_at).format('DD-MM-YYYY') 
    #filter that needs to be applied if any for each column
    #https://github.com/Pegase745/sqlalchemy-datatables
    displayfilters = {
            'created_at':_show_date,
            'details':_show_details
    }

    def get_name(self):
        return 'Guest'

    def get_modal_obj(self): 
        return Guest()   

class GuestDataManage(FlaskView):
    decorators = [login_required,admin_required]

    @classy_menu_item('.guestdata', _l('Guests'),icon='fa-users',
                            visible_when=admin_site_menu,order=3)
    def index(self,siteid):
        wifisite = Wifisite.query.get(siteid)
        return render_template('core/site-guestdata.html',siteid=siteid,
                                wifisite=wifisite) 



