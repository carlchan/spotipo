import sys
import pytest
from flask import current_app,url_for
from flask_wtf import Form
from wtforms import TextField
from faker import Faker
import arrow
import uuid
from sqlalchemy import and_,or_


from unifispot.modules.email.models import Emailconfig,Emailauth
from unifispot.modules.email.main import validate_emailconfig
from unifispot.core.models import Wifisite,Device,Guesttrack,Guest,Guestsession
from unifispot.core.guestutils import init_track,validate_track,redirect_guest
from unifispot.core.const import *
from tests.helpers import randomMAC,get_guestauth_url,get_guestlogin_url

fake = Faker()

def test_guest_login(session,client):
    #try to access non configured site
    site1 = Wifisite.query.get(1)
    track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())

    #site without email_login config
    url = get_guestlogin_url('email',track.trackid)
    resp = client.get(url)

    assert '404 NOT FOUND' == resp.status, 'Email login not configured site is giving :%s instead of \
                                404 NOT FOUND'%resp.status

    #valid site
    site1.auth_methods = {'auth_email' :1}
    session.commit()
    url = get_guestlogin_url('email',track.trackid)
    resp = client.get(url)

    assert '200 OK' == resp.status, 'Email login configured site is giving :%s instead of \
                                200 OK'%resp.status
    #check if Emailconfig is created 
    assert 1 == Emailconfig.query.count(),'Emailconfig is not created  the first time non configured site \
                                            is visited'                                
    assert '200 OK' == resp.status, 'Email login configured site is giving :%s instead of \
                                200 OK'%resp.status
    assert 1 == Emailconfig.query.count(),'Emailconfig is not only  the first time non configured site \
                                            is visited'       



def test_guest_login1(session,client):
    #form submission test of a fresh  device
    site1 = Wifisite.query.get(1)
    track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())

    #configure site with email mandatory
    site1.auth_methods = {'auth_email' :1}
    emailconfig = Emailconfig()
    emailconfig.data_limit = 500
    emailconfig.time_limit = 400
    emailconfig.siteid = site1.id 
    emailconfig.save()

    #emptry post should give same page
    url = get_guestlogin_url('email',track.trackid)
    resp = client.post(url,data={})
    assert None == resp.location, ' email page submited with empty form is not giving same page '

    firstname   = fake.first_name() 
    lastname    = fake.last_name() 
    email       = fake.email()
    form_data = {'firstname':firstname,'email':email,'lastname':lastname}
    url = get_guestlogin_url('email',track.trackid)
    resp = client.post(url,data=form_data)
    auth_url = get_guestauth_url(site1,track.trackid)
    assert auth_url in  resp.location,'Valid email form submission not leading to auth URL:%s instead\
                                    goes to :%s'%(auth_url,resp.location)

    newguest = Guest.query.get(1)
    assert firstname == newguest.firstname , "Guest firstname don't match"
    assert email == newguest.email , "Guest email don't match"
    assert site1.id == newguest.siteid , "Guest siteid don't match"

    #check all values in DB

    ##---check emailauth
    emailauth = Emailauth.query.get(1)
    assert emailauth.state == LOGINAUTH_FIRST , \
        'login state is :%s not LOGINAUTH_FIRST'%emailauth.state
    assert emailauth.data_limit == 500
    assert emailauth.time_limit == 400
    #check if startime is reset
    assert arrow.get(emailauth.starttime) < arrow.utcnow()
    assert arrow.get(emailauth.starttime) > arrow.utcnow().replace(seconds=-10)

    ##--check guesttrack
    track = Guesttrack.query.get(1)
    assert track.state == GUESTTRACK_AUTH , \
        'track state is :%s not GUESTTRACK_AUTH'%emailauth.state    
    assert track.loginstat == {'newguest': 1, 'num_visits': 1 ,'auth_email':1} ,'Check loginstat'
    assert track.loginauthid == 1 , 'check if track is assigned to loginauth'


def test_guest_login2(session,client):
    #form resubmission test of a fresh  device
    site1 = Wifisite.query.get(1)
    guestmac=randomMAC()
    
    track1 = init_track(site1,guestmac=guestmac,apmac=randomMAC())

    #configure site with email mandatory
    site1.auth_methods = {'auth_email' :1}
    emailconfig = Emailconfig()
    emailconfig.session_limit_control = 1
    emailconfig.data_limit = 500
    emailconfig.time_limit = 400
    emailconfig.siteid = site1.id 
    emailconfig.save()

    firstname   = fake.first_name() 
    lastname    = fake.last_name() 
    email       = fake.email()
    form_data = {'firstname':firstname,'email':email,'lastname':lastname}
    url = get_guestlogin_url('email',track1.trackid)
    #first post
    resp = client.post(url,data=form_data)
    #second post
    #simulate client visit after 10minues
    track1.timestamp = arrow.utcnow().replace(minutes=-10).naive
    track1.save()

    track2 = init_track(site1,guestmac=guestmac,apmac=randomMAC())
    assert track2.id == 2 , 'Second track not created'

    url = get_guestlogin_url('email',track2.trackid)
    resp = client.get(url)
    auth_url = get_guestauth_url(site1,track2.trackid)
    assert auth_url in  resp.location,'Valid second login not leading auth URL:%s instead\
                                    goes to :%s'%(auth_url,resp.location)    


    #check all values in DB

    ##---check emailauth
    emailauth = Emailauth.query.get(1)
    assert emailauth.state == LOGINAUTH_REPEATED , \
        'login state is :%s not LOGINAUTH_FIRST'%emailauth.state
    assert emailauth.data_limit == 500
    assert emailauth.time_limit == 400
    #check if startime is reset
    assert arrow.get(emailauth.starttime) < arrow.utcnow()
    assert arrow.get(emailauth.starttime) > arrow.utcnow().replace(seconds=-10)

    ##--check guesttrack
    track = Guesttrack.query.get(2)
    assert track.state == GUESTTRACK_AUTH , \
        'track state is :%s not GUESTTRACK_AUTH'%emailauth.state    
    assert track.loginstat == {'num_visits': 1, 'relogin': 1 ,'auth_email':1} \
                    ,'Check loginstat'
    assert track.loginauthid == 1 , 'check if track is assigned to loginauth'                                    


@pytest.fixture(scope='function')
def populate_dailysessions(app,session,client):
    #login a guest and then create a bunch of sessions 
    #on a day and the day before
    site1 = Wifisite.query.get(1)
    guestmac=randomMAC()
    
    track1 = init_track(site1,guestmac=guestmac,apmac=randomMAC())

    #configure site with email mandatory
    site1.auth_methods = {'auth_email' :1}
    emailconfig = Emailconfig()
    emailconfig.session_limit_control = 1
    emailconfig.data_limit = 500
    emailconfig.time_limit = 400
    emailconfig.siteid = site1.id 
    emailconfig.save()

    firstname   = fake.first_name() 
    lastname    = fake.last_name() 
    email       = fake.email()
    form_data = {'firstname':firstname,'email':email,'lastname':lastname}
    url = get_guestlogin_url('email',track1.trackid)
    #first post
    resp = client.post(url,data=form_data)     
    #get emailauth
    emailauth = Emailauth.query.get(1)
    #create a bunch of sessions 
    daytime = arrow.utcnow().floor('day').replace(hours=12) #12AM of a day
    track1.timestamp = daytime.replace(days=-3).naive
    track1.save()
    for i in range(10):
        #sessions at 11AM,9AM,7AM,5AM,3AM,1AM
        # and previous day 11PM,9PM,7PN,5PM
        time = daytime.replace(hours= -(2*i+1)).naive
        track = init_track(site1,guestmac=guestmac,apmac=randomMAC())
        track.timestamp = time
        track.save()
        sess = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=emailauth.id)
        sess.starttime  = time
        sess.data_used  = 100
        sess.duration   = 10
        sess.save()

@pytest.fixture(scope='function')
def populate_monthlysessions(app,session,client):
    #login a guest and then create a bunch of sessions 
    #on a day and the day before
    site1 = Wifisite.query.get(1)
    guestmac=randomMAC()
    
    track1 = init_track(site1,guestmac=guestmac,apmac=randomMAC())

    #configure site with email mandatory
    site1.auth_methods = {'auth_email' :1}
    emailconfig = Emailconfig()
    emailconfig.session_limit_control = 2
    emailconfig.data_limit = 500
    emailconfig.time_limit = 400
    emailconfig.siteid = site1.id 
    emailconfig.save()

    firstname   = fake.first_name() 
    lastname    = fake.last_name() 
    email       = fake.email()
    form_data = {'firstname':firstname,'email':email,'lastname':lastname}
    url = get_guestlogin_url('email',track1.trackid)
    #first post
    resp = client.post(url,data=form_data)     
    #get emailauth
    emailauth = Emailauth.query.get(1)
    #create a bunch of sessions 
    daytime = arrow.utcnow().floor('month').replace(days=15) #15th of month
    track1.timestamp = daytime.replace(days=-3).naive
    track1.save()
    for i in range(10):
        #sessions at 15th 12th 9th 6th 3rd of this month
        # and 5 days last month
        time = daytime.replace(days= -(3*i+1)).naive
        print time
        track = init_track(site1,guestmac=guestmac,apmac=randomMAC())
        track.timestamp = time
        track.save()
        sess = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=emailauth.id)
        sess.starttime  = time
        sess.data_used  = 100
        sess.duration   = 10
        sess.save()


def test_get_loginauth_validator1(session,client,populate_dailysessions):
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)
    device = Device.query.get(1)


    #both limits configured and not exceeded
    emailconfig.data_limit = 1000
    emailconfig.time_limit = 400
    emailconfig.save()

    track2 = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())
    url = get_guestlogin_url('email',track2.trackid)
    resp = client.get(url)
    auth_url = get_guestauth_url(site1,track2.trackid)
    assert auth_url in  resp.location,'Valid second login not leading auth URL:%s instead\
                                    goes to :%s'%(auth_url,resp.location) 

def test_get_loginauth_validator2(session,client,populate_dailysessions):
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)                                     
    device = Device.query.get(1)


    #both limits are unlimited
    emailconfig.data_limit = 0
    emailconfig.time_limit = 0
    emailconfig.save()

    track2 = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())
    url = get_guestlogin_url('email',track2.trackid)
    resp = client.get(url)
    auth_url = get_guestauth_url(site1,track2.trackid)
    assert auth_url in  resp.location,'Valid second login not leading auth URL:%s instead\
                                    goes to :%s'%(auth_url,resp.location) 
                                     
def test_get_loginauth_validator3(session,client,populate_dailysessions):
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)                                     
    device = Device.query.get(1)


    #data expired, unlimited time
    emailconfig.data_limit = 600
    emailconfig.time_limit = 0
    emailconfig.save()

    track2 = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())
    url = get_guestlogin_url('email',track2.trackid)
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 

    #check DB level values
    track2 = Guesttrack.query.get(track2.id)                            
    assert track2.state == GUESTTRACK_PRELOGIN, 'track2 state is not GUESTTRACK_PRELOGIN but\
                        %s after redirection to override'%track2.state


def test_get_loginauth_validator4(session,client,populate_dailysessions):
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)                                     
    device = Device.query.get(1)

    #data expired, unlimited time
    emailconfig.data_limit = 600
    emailconfig.time_limit = 0
    emailconfig.save()

    track2 = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())
    url = get_guestlogin_url('email',track2.trackid)
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 

def test_get_loginauth_validator5(session,client,populate_dailysessions):
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)                                     
    device = Device.query.get(1)
    
    #time expired, unlimited data
    emailconfig.data_limit = 0
    emailconfig.time_limit = 60
    emailconfig.save()

    track2 = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())
    url = get_guestlogin_url('email',track2.trackid)
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 

def test_get_loginauth_validator6(session,client,populate_dailysessions):
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)                                     
    device = Device.query.get(1)
    
    #time expired,  data expired
    emailconfig.data_limit = 600
    emailconfig.time_limit = 60
    emailconfig.save()

    track2 = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())
    url = get_guestlogin_url('email',track2.trackid)
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 


def test_get_loginauth_validator7(session,client,populate_monthlysessions):
    #monthly limit validation
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)                                     
    device = Device.query.get(1)
    
    track2 = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())
    url = get_guestlogin_url('email',track2.trackid)

    #time expired,  data expired
    emailconfig.data_limit = 500
    emailconfig.time_limit = 50
    emailconfig.save()
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 

    #time available,  data expired
    emailconfig.data_limit = 500
    emailconfig.time_limit = 500
    emailconfig.save()
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 
    #time expired,  data available
    emailconfig.data_limit = 5000
    emailconfig.time_limit = 50
    emailconfig.save()
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 

    #time unlimited,  data expired
    emailconfig.data_limit = 500
    emailconfig.time_limit = 0
    emailconfig.save()
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 
    #time expired,  data unlimited
    emailconfig.data_limit = 0
    emailconfig.time_limit = 50
    emailconfig.save()
    resp = client.get(url)
    assert '/email/override/' in resp.location,'Invalid 2nd login not leading override\
                            instead goes to :%s'%(resp.location) 


    #check DB level values
    track2 = Guesttrack.query.get(track2.id)                            
    assert track2.state == GUESTTRACK_PRELOGIN, 'track2 state is not GUESTTRACK_PRELOGIN but\
                        %s after redirection to override'%track2.state


def test_handle_override1(session,client,):
    #test all negetive cases
    site1 = Wifisite.query.get(1)
    guestmac=randomMAC()
    track = init_track(site1,guestmac=guestmac,apmac=randomMAC())

    #configure site with email mandatory
    site1.auth_methods = {'auth_email' :1}
    emailconfig = Emailconfig()
    emailconfig.data_limit = 500
    emailconfig.time_limit = 400
    emailconfig.siteid = site1.id 
    emailconfig.session_limit_control = 1
    emailconfig.save()

    #try to visit the site with fresh device 
    overrideurl = url_for('unifispot.modules.email.guest_override',trackid=track.trackid)
    assert '404 NOT FOUND' == client.get(overrideurl).status, 'Fresh device not throwing 404'

    #guest visited once trying withour first login
    url = get_guestlogin_url('email',track.trackid)
    resp = client.get(url)    
    assert '404 NOT FOUND' == client.get(overrideurl).status, 'Fresh device not throwing 404'

    #login a guest
    track2 = init_track(site1,guestmac=guestmac,apmac=randomMAC())
    track2.timestamp = arrow.utcnow().replace(days=-1).naive
    track2.save()
    firstname   = fake.first_name() 
    lastname    = fake.last_name() 
    email       = fake.email()
    form_data = {'firstname':firstname,'email':email,'lastname':lastname}
    url = get_guestlogin_url('email',track2.trackid)
    #first post
    resp = client.post(url,data=form_data)     
    #try override URL
    resp = client.get(overrideurl)
    assert '200 OK' == resp.status, \
                    'Already loggedin device not throwing 200'
    assert 'Looks like your quota have expired' in resp.data, \
                    'Quota expired message not seen'

    #

def test_handle_override2(session,client,populate_dailysessions):
    #test password submission
    #for daily override
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)                                     
    device = Device.query.get(1)
    
    #time expired,  data expired
    emailconfig.data_limit = 600
    emailconfig.time_limit = 60
    emailconfig.save()
    track = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())    

    overrideurl = url_for('unifispot.modules.email.guest_override',trackid=track.trackid)

    #try with empty password and empty configured pass
    resp = client.post(overrideurl)
    assert 'This field is required.' in resp.data,'Empty password'

    #try with  password and empty configured pass
    resp = client.post(overrideurl,data={'password':'password'})
    assert 'Wrong password' in resp.data,'wrong password'


    #try with  different password
    emailconfig.session_overridepass = 'password'
    emailconfig.save()
    resp = client.post(overrideurl,data={'password':'password1'})
    assert 'Wrong password' in resp.data,'wrong password'    


    resp = client.post(overrideurl,data={'password':'password'})
    auth_url = get_guestauth_url(site1,track.trackid)
    assert auth_url  in  resp.location,'Valid override login not leading auth URL:%s instead\
                                    goes to :%s'%(auth_url,resp.location)     

    #check DB level values
    track2 = Guesttrack.query.get(track.id)                            
    assert track2.loginstat == {'auth_email': 1, 'num_visits': 1, 'relogin': 1},\
                    'guesttrack loginstat is not properly populated'


    daystart = arrow.utcnow().floor('day')
    daysess  = daystart.replace(hours=11) #11AM of a day
    #check if all today's session are overriden
    for sess in Guestsession.query.filter(and_(Guestsession.starttime > daystart.naive,
                    Guestsession.starttime < daysess.naive)).all():
        assert sess.override == 1 , 'old session of the day not overridden'
    #check if all yesterday's session are not overriden
    for sess in Guestsession.query.filter(and_(Guestsession.starttime < daystart.naive)).all():
        assert sess.override == 0 , ' dau before sessions overridden'


def test_handle_override3(session,client,populate_monthlysessions):
    #test password submission
    #for monthly override
    site1 = Wifisite.query.get(1)     
    emailconfig = Emailconfig.query.get(1)                                     
    device = Device.query.get(1)
    
    #time expired,  data expired
    emailconfig.data_limit = 500
    emailconfig.time_limit = 50
    emailconfig.save()
    track = init_track(site1,guestmac=device.devicemac,apmac=randomMAC())    

    overrideurl = url_for('unifispot.modules.email.guest_override',trackid=track.trackid)

    #try with empty password and empty configured pass
    resp = client.post(overrideurl)
    assert 'This field is required.' in resp.data,'Empty password'

    #try with  password and empty configured pass
    resp = client.post(overrideurl,data={'password':'password'})
    assert 'Wrong password' in resp.data,'wrong password'


    #try with  different password
    emailconfig.session_overridepass = 'password'
    emailconfig.save()
    resp = client.post(overrideurl,data={'password':'password1'})
    assert 'Wrong password' in resp.data,'wrong password'    


    resp = client.post(overrideurl,data={'password':'password'})
    auth_url = get_guestauth_url(site1,track.trackid)
    assert auth_url  in  resp.location,'Valid override login not leading auth URL:%s instead\
                                    goes to :%s'%(auth_url,resp.location)     

    #check DB level values
    track2 = Guesttrack.query.get(track.id)                            
    assert track2.loginstat == {'auth_email': 1, 'num_visits': 1, 'relogin': 1},\
                    'guesttrack loginstat is not properly populated'
