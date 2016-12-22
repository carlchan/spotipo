import logging
import arrow
from functools import wraps
from flask_classful import FlaskView
from flask_security import current_user,login_required
from datatables import ColumnDT, DataTables
from flask import Flask, render_template, request, jsonify,make_response
from sqlalchemy.exc import SQLAlchemyError
from dateutil import tz

from unifispot.utils.translation import _l,_n,_
from unifispot.core.utils import  get_form_errors,validate_site_ownership,\
                                admin_required
from unifispot.core.db import db
from unifispot.core.models import Wifisite


logger = logging.getLogger()

class RESTView(FlaskView):
    '''Base view used for implementing CRUD api for each resourse
        -> index() -> all resources in datatable format
        -> get(id) -> Json representation of a resource
        -> post() -> create new resource
        -> put(id) -> update a resource
        -> delete(id) -> delete a resource

    '''
    decorators = [login_required]
    #columns that will be shown in the datatable
    displaycolumns = []
    #filter that needs to be applied if any for each column
    #https://github.com/Pegase745/sqlalchemy-datatables
    displayfilters = {}

    def get_extrafields_modal(self):
        #should return a dict with modal fields as keys
        #and values to be set as vals
        return {}

    def get_modal_obj(self):
        return NotImplementedError

    def get_form_obj(self):
        return NotImplementedError

    def get_name(self):
        return self.__class__.__name__
 
    def index(self):  
        columns = []
        for col in self.displaycolumns:
            col_filter = self.displayfilters.get(col)
            if col_filter:
                columns.append(ColumnDT(col,filter=col_filter,filterarg='row'))
            else:
                columns.append(ColumnDT(col))

        # defining the initial query depending on your purpose
        query = self.get_modal_obj().get_query()

        # instantiating a DataTable for the query and table needed
        rowTable = DataTables(request.args, self.get_modal_obj(), query, columns)

        # returns what is needed by DataTable
        return jsonify(rowTable.output_result())             
        
    def get(self,id):        
        item = self.get_modal_obj().query.get(id)    
        if item:
            return jsonify({'status':1,'data':item.to_dict()})   
        else:
            logger.debug('UserID:%s trying to access unknown ID:%s of :%s'\
                    %(current_user.id,id,self.get_name()))
            return jsonify({'status':0,'data':{}, 'msg':_l('Unknown :%(name)s ID specified'\
                    ,name=self.get_name())})
                
    def post(self):
        itemform = self.get_form_obj()
        itemform.populate()
        if itemform.validate_on_submit(): 
            try:
                item = self.get_modal_obj()
                item.populate_from_form(itemform)
                item.save()
                item.populate_from_dict(self.get_extrafields_modal())
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

    def put(self,id):
        item = self.get_modal_obj().query.get(id) 
        if item:
            itemform = self.get_form_obj()
            itemform.populate()
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

    def delete(self,id):
        item = self.get_modal_obj().query.get(id)    
        if item:
            try:
                item.delete()
            except SQLAlchemyError as exception:
                logger.exception('UserID:%s submited deletion call exception'\
                        %(current_user.id))
                return jsonify({'status':0,'data':{}, 'msg':_('Error while deleting %(name)s'\
                    ,name=self.get_name())})            
            return jsonify({'status':1,'data':{}, 'msg':_('Successfully deleted %(name)s'\
                        ,name=self.get_name())}) 

        else:
            logger.debug('UserID:%s trying to delete unknown ID:%s of :%s'\
                    %(current_user.id,id,self.get_name()))
            return jsonify({'status':0,'data':{}, 'msg':_l('Unknown :%(name)s ID \
                    specified',name=self.get_name())})


class SiteModuleAPI(FlaskView):
    '''Base view used for APIs connected to site specific modules like Login configs 

        URL route must have a <siteid> and id need not be specified, only POST and INDEX is allowed

        Index return rendered HTMl for config modal

    '''
    decorators = [login_required,admin_required,validate_site_ownership]


    def get_form_obj(self):
        return NotImplementedError

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self): 
        return NotImplementedError

    def get_config_template(self):
        return NotImplementedError

    def get_extrafields_modal(self):
        #should return a dict with modal fields as keys
        #and values to be set as vals
        return {'account_id':current_user.account_id} 

    def index(self,siteid):
        #this view is used to populate 
        item = self.get_modal_obj().query.filter_by(siteid=siteid).first()
        if not item:
            item = self.get_modal_obj()
            item.siteid = siteid
            item.save()  

        itemform = self.get_form_obj()
        itemform.populate()

        #populate form from model
        item_dict = item.to_dict()
        for field in itemform:
            field.data = item_dict.get(field.name)

        return render_template(self.get_config_template(),itemform=itemform)        

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



class SiteDataViewAPI(FlaskView):
    '''Base view used for viewing site specific data like guest data

        Index return JSON for datatable consumption

    '''
    decorators = [login_required,admin_required,validate_site_ownership]

    #columns that will be shown in the datatable
    displaycolumns = []
    #filter that needs to be applied if any for each column
    #https://github.com/Pegase745/sqlalchemy-datatables
    displayfilters = {}

    def get_name(self):
        return self.__class__.__name__

    def get_modal_obj(self): 
        return NotImplementedError    

    def index(self,siteid):
        #this view is used for datatable      
        wifisite = Wifisite.query.get(siteid)
        r_startdate = request.values.get('startdate')
        r_enddate = request.values.get('enddate')
        download = request.values.get('download')
        today     = arrow.now()
        if r_startdate and r_enddate:
            tzinfo = tz.gettz(wifisite.timezone)
            startdate =  arrow.get(r_startdate,'DD/MM/YYYY',tzinfo=tzinfo)
            enddate =  arrow.get(r_enddate,'DD/MM/YYYY',
                                    tzinfo=tzinfo).replace(days=1)          
        else:
            startdate = today.replace(days=1 - today.day)
            enddate = today.replace(days=1)

        if download:
            csvHeading = ','.join(self.get_modal_obj().get_titles())
            elements = self.get_modal_obj().get_query(siteid=siteid,startdate=startdate,
                                    enddate=enddate).all()
            csvList = '\n'.join(','.join(row.to_list()) for row in elements) 

            # We need to modify the response, so the first thing we 
            # need to do is create a response out of the CSV string
            response = make_response(csvHeading+'\n'+csvList)
            # This is the key: Set the right header for the response
            # to be downloaded, instead of just printed on the browser

            ##---create a reasonable name for downloadfile
            ##--- modelname-startdate-enddate.csv
            tstart = startdate.format('MMDDYYYY')
            tend = enddate.format('MMDDYYYY')

            content_header = "attachment; filename=%s-%s-%s.csv"%(self.get_name(),
                                        tstart,tend)
            response.headers["Content-Disposition"] = content_header
            return response     
        else:
            columns = []
            for col in self.displaycolumns:
                col_filter = self.displayfilters.get(col)
                if col_filter:
                    columns.append(ColumnDT(col,filter=col_filter,filterarg='row'))
                else:
                    columns.append(ColumnDT(col))

            # defining the initial query depending on your purpose
            query = self.get_modal_obj().get_query(siteid=siteid,startdate=startdate,
                                    enddate=enddate)
            

            # instantiating a DataTable for the query and table needed
            rowTable = DataTables(request.args, self.get_modal_obj(), query, columns)

            # returns what is needed by DataTable
            return jsonify(rowTable.output_result())           



class SiteModuleElementAPI(FlaskView):
    '''Base view used for managing sitemodule specific elements like vouchers,packages etc

        similar to RESTView but need to specify a siteid mandatory on URL

        also can be accessed by clients
    '''
    decorators = [login_required,validate_site_ownership]


    #columns that will be shown in the datatable
    displaycolumns = []
    #filter that needs to be applied if any for each column
    #https://github.com/Pegase745/sqlalchemy-datatables
    displayfilters = {}

    def get_extrafields_modal(self):
        #should return a dict with modal fields as keys
        #and values to be set as vals
        return {}

    def get_modal_obj(self):
        return NotImplementedError

    def get_form_obj(self):
        return NotImplementedError

    def get_name(self):
        return self.__class__.__name__
 
    def index(self,siteid):  
        #this view is used for datatable      
        wifisite = Wifisite.query.get(siteid)
        r_startdate = request.values.get('startdate')
        r_enddate = request.values.get('enddate')
        download = request.values.get('download')
        today     = arrow.now()
        if r_startdate and r_enddate:
            tzinfo = tz.gettz(wifisite.timezone)
            startdate =  arrow.get(r_startdate,'DD/MM/YYYY',tzinfo=tzinfo)
            enddate =  arrow.get(r_enddate,'DD/MM/YYYY',
                                    tzinfo=tzinfo).replace(days=1)          
        else:
            startdate = today.replace(days=1 - today.day)
            enddate = today.replace(days=1)

        if download:
            csvHeading = ','.join(self.get_modal_obj().get_titles())
            elements = self.get_modal_obj().get_query(siteid=siteid,startdate=startdate,
                                    enddate=enddate).all()
            csvList = '\n'.join(','.join(row.to_list()) for row in elements) 

            # We need to modify the response, so the first thing we 
            # need to do is create a response out of the CSV string
            response = make_response(csvHeading+'\n'+csvList)
            # This is the key: Set the right header for the response
            # to be downloaded, instead of just printed on the browser

            ##---create a reasonable name for downloadfile
            ##--- modelname-startdate-enddate.csv
            tstart = startdate.format('MMDDYYYY')
            tend = enddate.format('MMDDYYYY')

            content_header = "attachment; filename=%s-%s-%s.csv"%(self.get_name(),
                                        tstart,tend)
            response.headers["Content-Disposition"] = content_header
            return response            
        else:
            columns = []
            for col in self.displaycolumns:
                col_filter = self.displayfilters.get(col)
                if col_filter:
                    columns.append(ColumnDT(col,filter=col_filter,filterarg='row'))
                else:
                    columns.append(ColumnDT(col))

            # defining the initial query depending on your purpose
            query = self.get_modal_obj().get_query(siteid=siteid,startdate=startdate,
                                    enddate=enddate)

            # instantiating a DataTable for the query and table needed
            rowTable = DataTables(request.args, self.get_modal_obj(), query, columns)

            # returns what is needed by DataTable
            return jsonify(rowTable.output_result())              
        
    def get(self,siteid,id):        
        item = self.get_modal_obj().query.get(id)    
        if item:
            return jsonify({'status':1,'data':item.to_dict()})   
        else:
            logger.debug('UserID:%s trying to access unknown ID:%s of :%s'\
                    %(current_user.id,id,self.get_name()))
            return jsonify({'status':0,'data':{}, 'msg':_l('Unknown :%(name)s ID specified'\
                    ,name=self.get_name())})
                
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

    def put(self,siteid,id):
        item = self.get_modal_obj().query.get(id) 
        if item:
            itemform = self.get_form_obj()
            itemform.populate()
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

    def delete(self,siteid,id):
        item = self.get_modal_obj().query.get(id)    
        if item:
            try:
                item.delete()
            except SQLAlchemyError as exception:
                logger.exception('UserID:%s submited deletion call exception'\
                        %(current_user.id))
                return jsonify({'status':0,'data':{}, 'msg':_('Error while deleting %(name)s'\
                    ,name=self.get_name())})            
            return jsonify({'status':1,'data':{}, 'msg':_('Successfully deleted %(name)s'\
                        ,name=self.get_name())}) 

        else:
            logger.debug('UserID:%s trying to delete unknown ID:%s of :%s'\
                    %(current_user.id,id,self.get_name()))
            return jsonify({'status':0,'data':{}, 'msg':_l('Unknown :%(name)s ID \
                    specified',name=self.get_name())})        



