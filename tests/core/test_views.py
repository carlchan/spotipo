import sys
import pytest
from flask import current_app,Flask
from flask_wtf import Form
from wtforms import TextField
from wtforms.validators import Required

from unifispot.core.db import db as _db
from unifispot.core.views import UserAPI
from tests.helpers import loggin_as_admin,rest_login_check,rest_allowed_methods_check,\
                        rest_check_status,check_json_status_ok,check_json_status_nok,\
                        loggin_as_client,check_index_datatable


def test_user_view(client,session):      
    #not loggedin users
    rest_login_check(client,'/user/')

    client = loggin_as_admin()
    rest_allowed_methods_check(client,'/user/',methods=['index','post','delete'])

    #try to access id not owned by self
    status = '405 METHOD NOT ALLOWED'
    rest_check_status(client,'/user/',status,4,methods=['get','put'])   

    check_json_status_ok(client,'/user/1','get')     
    check_json_status_nok(client,'/user/1','put') 

    check_json_status_ok(client,'/user/1','put',data={'email':'test@test.com',
        'displayname':'Hellow'})
        
 
def test_admin_view(client,session):      
    #not loggedin users
    rest_login_check(client,'/admin/')

    client = loggin_as_client()
    #loggged in as client
    status = '401 UNAUTHORIZED'
    rest_check_status(client,'/admin/',status,1) 

    #logged in as admin
    client = loggin_as_admin()
    #get self details and admin of another account
    check_json_status_ok(client,'/admin/1','get') 

    status = '401 UNAUTHORIZED'
    rest_check_status(client,'/admin/',status,2,methods=['get','put','delete']) 

    #get index    
    check_index_datatable(client,'/admin/',num_rows=1) 

    #create new admin and check
    check_json_status_ok(client,'/admin/','post',data={'email':'admin3@example.com',
        'displayname':'Admin3'})    
   
    check_index_datatable(client,'/admin/',num_rows=2)     

    #update admin and check
    check_json_status_ok(client,'/admin/1','put',data={'email':'admin5@example.com',
        'displayname':'Admin3'})    

    check_json_status_ok(client,'/admin/5','delete')  
    status = '405 METHOD NOT ALLOWED'
    rest_check_status(client,'/admin/',status,1,methods=['delete'])   

def test_client_view(client,session):      
    #not loggedin users
    rest_login_check(client,'/client/')

    client = loggin_as_client()
    #loggged in as client
    status = '401 UNAUTHORIZED'
    rest_check_status(client,'/client/',status,1) 

    #logged in as admin
    client = loggin_as_admin()
    #get for same account client and another
    check_json_status_ok(client,'/client/3','get') 

    status = '401 UNAUTHORIZED'
    rest_check_status(client,'/client/',status,4,methods=['get','put','delete']) 

    #get index    
    check_index_datatable(client,'/client/',num_rows=1) 

    #create new client and check
    check_json_status_ok(client,'/client/','post',data={'email':'client3@example.com',
        'displayname':'Client3'})    
   
    check_index_datatable(client,'/client/',num_rows=2)     

    #update client and check
    check_json_status_ok(client,'/client/3','put',data={'email':'client5@example.com',
        'displayname':'Admin3'})    

    check_json_status_ok(client,'/client/3','delete')  
 

def test_wifisite_view(client,session):      
    #not loggedin users
    rest_login_check(client,'/client/')