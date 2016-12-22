from flask import current_app,url_for
import random
from faker import Faker
from flask_wtf import Form
from wtforms import TextField

fake = Faker()

def loggin_user(username,password):
    '''fixture used to create a logged in instance of test_client 

        based on multiple examples like http://librelist.com/browser/flask/2012/7/1/giving-context-to-test-client/#dfb70ea7e1b300da59d9d0ba6a2c0d52
    '''

   
    logged_client = current_app.test_client()
    login_resp = logged_client.post(url_for('security.login'),data={ 'email':username, 'password': password },follow_redirects=True)        
    assert 'Bad username or password' not in login_resp.data,'Login Failed '   

    #current_app.test_client = logged_client  #temperarly replace test_client with instance of logged in client
 
    return logged_client

def loggin_as_admin():

    return loggin_user('admin1@example.com','password')

def loggin_as_client():

    return loggin_user('client1@example.com','password')

def rest_check_rsp(client,url,rsp,id=1,methods=['index','get','post','put','delete']):
    '''Test all REST methods against given endpoint and ensure all of them resturns

        given response. id should be a valid one *

    '''
    id = str(id)
    if 'index' in methods:
        assert rsp in client.get(url,
                follow_redirects=True).data,'Index not returning :%s in response for :%s'%\
                (rsp,url)

    if 'get' in methods:
        assert rsp in client.get(url+id,
                follow_redirects=True).data,'Get not returning :%s in response for :%s'%\
                (rsp,url)  
    if 'post' in methods:
        assert rsp in client.post(url,
                follow_redirects=True).data,'Post not returning :%s in response for :%s'%\
                (rsp,url)                         
    if 'put' in methods:
        assert rsp in client.put(url+id,
                follow_redirects=True).data,'Put not returning :%s in response for :%s'%\
                (rsp,url)                                    

    if 'delete' in methods:
        assert rsp in client.delete(url+id,
                follow_redirects=True).data,'Delete not returning :%s in response for :%s'%\
                (rsp,url)   

def rest_check_status(client,url,status,id=1,methods=['index','get','post','put','delete']):
    '''Test given REST methods against given endpoint and ensure all of them resturns

        given status. id should be a valid one *

    '''
    id = str(id)
    if 'index' in methods:
        val = client.get(url,follow_redirects=True).status
        assert status == val  ,'Index returning :%s as status for :%s instead of :%s'%\
                (val,url,status)

    if 'get' in methods:
        val = client.get(url+id,follow_redirects=True).status
        assert status == val  ,'Get returning :%s as status for :%s instead of :%s'%\
                (val,url+id,status)
    if 'post' in methods:
        val = client.post(url,follow_redirects=True).status
        assert status == val  ,'Post returning :%s as status for :%s instead of :%s'%\
                (val,url,status)                    
    if 'put' in methods:
        val = client.put(url+id,follow_redirects=True).status
        assert status == val  ,'Put returning :%s as status for :%s instead of :%s'%\
                (val,url+id,status)  
    if 'delete' in methods:
        val = client.delete(url+id,follow_redirects=True).status
        assert status == val  ,'Delete returning :%s as status for :%s instead of :%s'%\
                (val,url+id,status) 


def check_json_status_ok(client,url,method,data=None,msg=None):
    '''Test given REST method on URL and check if status is 1 and return data part

        optinally check if msg is found in response

    '''
    f = getattr(client,method)
    rsp = f(url,follow_redirects=True,data=data)

    assert rsp.status == '200 OK','200 Ok not received for :%s method:%s'%(url,method)
    assert rsp.json.get('status') == 1,'JSON status not 1 for :%s method:%s'%(url,method)
    if msg:
        assert rsp.json.get('msg') == msg,'Received :%s ad msg instead of :%s for :%s method:%s'\
        %(rsp.json.get('msg'),msg,url,method)
    return rsp.json.get('data')



def check_json_status_nok(client,url,method,data=None,msg=None):
    '''Test given REST method on URL and check if status is 1 and return data part

        optinally check if msg is found in response

    '''
    f = getattr(client,method)
    rsp = f(url,follow_redirects=True,data=data)

    assert rsp.status == '200 OK','200 Ok not received for :%s method:%s'%(url,method)
    assert rsp.json.get('status') == 0,'JSON status not 0 for :%s method:%s'%(url,method)
    if msg:
        assert rsp.json.get('msg') == msg,'Received :%s ad msg instead of :%s for :%s method:%s'\
        %(rsp.json.get('msg'),msg,url,method)
    return rsp.json.get('data')



def check_index_datatable(client,url,data=None,num_rows=1):
    '''Test given REST method on URL and check if status is 1 and return data part

        optinally check if msg is found in response

    '''
    rsp = client.get(url,follow_redirects=True,data=data)

    assert rsp.status == '200 OK','200 Ok not received for :%s'%(url)
    rows = len(rsp.json.get('data'))
    assert num_rows == rows, 'Index returning :%s rows instead of expected :%s'%\
            (rows,num_rows)
    return rsp.json

def rest_login_check(client,endpoint,id=1,methods=['index','get','post','put','delete']):
    '''Test given REST methods against given endpoint and ensure all of them resturns

        login screen. id should be a valid one *

    '''                
    rsp = 'Please log in to access this page.'
    rest_check_rsp(client,endpoint,rsp,id,methods)

def rest_allowed_methods_check(client,endpoint,id=1,methods=['index','get','post','put','delete']):
    '''Test given REST methods against given URL and ensure all of them resturns

        method not allowed screen. id should be a valid one *

    '''                
    status = '405 METHOD NOT ALLOWED'
    rest_check_status(client,endpoint,status,id,methods)    


def randomMAC():
    mac= [ 0x00, 0x16, 0x3e,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

def randomGuestEmailForm():
    class Fakeemailform(Form):
        email       = TextField('Email')
        firstname   = TextField('Firstname')
        lastname    = TextField('Lastname')

    f = Fakeemailform()
    f.firstname.data   = fake.first_name() 
    f.lastname.data    = fake.last_name() 
    f.email.data       = fake.email()

    return f



def get_guestentry_url(site,mac='',apmac='',demo=0):

    base_url = url_for('unifispot.modules.%s.guest_portal'%\
            site.backend_type,sitekey=site.sitekey)
    if demo == 0:
        guest_url = '%s?id=%s&ap=%s'%(base_url,mac,apmac)
    else:
        guest_url = '%s?id=%s&ap=%s&demo=1'%(base_url,mac,apmac)
    return guest_url 

def get_guestauth_url(site,trackid):

    return url_for('unifispot.modules.%s.guest_auth'%\
            site.backend_type,trackid=trackid)    

def get_guestlogin_url(logintype,trackid):

    return url_for('unifispot.modules.%s.guest_login'%\
            logintype,trackid=trackid)   