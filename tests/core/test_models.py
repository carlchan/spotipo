import sys
import arrow
import pytest
from flask import current_app
from flask_wtf import Form
from wtforms import TextField

from unifispot.core.guestutils import init_track
from unifispot.core.db import db as _db
from unifispot.core.models import User,Wifisite,Guestsession,Loginauth,Guesttrack
from tests.factories import UserFactory
from tests.helpers import randomMAC

from flask_security.utils import verify_password

def test_user(session,db,request):
    oldcount =  User.query.count()
    testuser = UserFactory()
    testuser.save()
    assert User.query.count() > oldcount , 'User not created'

    testuser.set_password('magic123')

    assert verify_password('magic123',User.query.get(testuser.id).password),\
                'Password setting not working'
    with current_app.app_context():
        assert None == testuser.to_dict().get('password'),"User displaying password"


class SiteForm(Form):
    preauth_test1 = TextField('preauth_test1')
    preauth_test2 = TextField('preauth_test2')
    preauth_test3 = TextField('preauth_test3')
    name                = TextField('preauth_test3')
    timezone            = TextField('preauth_test3')
    redirect_url        = TextField('preauth_test3')
    reports_list        = TextField('preauth_test3')
    reports_type        = TextField('preauth_test3')
    client_id           = TextField('preauth_test3')
    template            = TextField('preauth_test3')
    backend_type        = TextField('preauth_test3')
    sitekey            = TextField('default')

    def populate(self):
        pass

def test_wifisite(session,db,request):
    assert Wifisite.query.count () == 2

    #create a test form which stores data as JSON
    #and check after retriving
    loc1 = Wifisite.query.get(1)
    test_form = SiteForm()
    test_form.preauth_test1.data = 'test1'
    test_form.preauth_test2.data = 'test2'
    test_form.preauth_test3.data = 'test3'
    loc1.populate_from_form(test_form)
    session.commit()
    loc1_dict = Wifisite.query.get(1).to_dict()

    assert loc1_dict['preauth_test1'] == 'test1', '%s is giving :%s instead of test1'%\
                ('preauth_test1',loc1_dict['preauth_test1'])
    assert loc1_dict['preauth_test2'] == 'test2', '%s is giving :%s instead of test2'%\
                ('preauth_test2',loc1_dict['preauth_test2'])
    assert loc1_dict['preauth_test3'] == 'test3', '%s is giving :%s instead of test3'%\
                ('preauth_test3',loc1_dict['preauth_test3'])

@pytest.mark.usefixtures('session') 
class TestLoginAuth:
    #initlize loginauth
    def init_loginauth(self,site1,track):
        loginauth = Loginauth(siteid=site1.id,deviceid=track.deviceid) 
        loginauth.time_limit = 55
        loginauth.data_limit = 500
        loginauth.starttime = arrow.utcnow().replace(minutes=-15).naive
        loginauth.endtime = arrow.utcnow().replace(minutes=40).naive
        loginauth.save()
        return loginauth


    def test_time_available(self):
        site1 = Wifisite.query.get(1)
        track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC()) 
        loginauth = self.init_loginauth(site1,track)
        #
        assert loginauth.time_available() == 40 ,'time_available\
             is  returning :%s instead of %s'%(loginauth.time_available(),40)
        #unlimited timelimit should return 480
        loginauth.time_limit = 0
        loginauth.save()
        assert loginauth.time_available() == 480 ,'Unlimited(0) time_limit\
             is not returning 480'

        #expired loginauth
        loginauth.time_limit = 59
        loginauth.starttime = arrow.utcnow().replace(minutes=-60).naive
        loginauth.save()        
        assert loginauth.time_available() == 0 ,'time_available\
             is  returning :%s instead of %s'%(loginauth.time_available(),0)

    def test_data_available(self):
        site1 = Wifisite.query.get(1)
        track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC()) 
        loginauth = self.init_loginauth(site1,track)
        #without any sessions
        assert loginauth.data_available() == 500 ,'data_lavailable \
             is  returning :%s instead of %s'%(loginauth.time_available(),500)

        #wtih unused sessions
        session = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)
        session.starttime = arrow.utcnow().replace(minutes=-15).naive
        session.save()
        assert loginauth.data_available() == 500 ,'data_lavailable \
             is  returning :%s instead of %s'%(loginauth.time_available(),500) 

        #single session uses some data
        session.data_used = 200
        session.save()
        assert loginauth.data_available() == 300 ,'data_lavailable \
             is  returning :%s instead of %s'%(loginauth.time_available(),300)


        #multiple sessions
        oldsess = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)

        oldsess.starttime = arrow.utcnow().replace(hours=-1).naive #very old
        oldsess.data_used = 450
        oldsess.save()

        oldsess1 = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)

        oldsess1.starttime = arrow.utcnow().replace(minutes=-10).naive #part of current window
        oldsess1.data_used = 100
        oldsess1.save()    

        #overided sessions
        oldsess2 = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)

        oldsess2.starttime = arrow.utcnow().replace(minutes=-10).naive #part of current window
        oldsess2.data_used = 100
        oldsess2.duration = 10
        oldsess2.override = 1
        oldsess2.save()        

        assert loginauth.data_available() == 200 ,'data_lavailable \
             is  returning :%s instead of %s'%(loginauth.time_available(),200)



    def test_get_usage(self):
        site1 = Wifisite.query.get(1)
        track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC()) 
        loginauth = self.init_loginauth(site1,track)
        fromtime = arrow.utcnow().replace(minutes=-30).naive

        #without any sessions
        assert loginauth.get_usage(fromtime) == (0,0) ,'get_usage \
             is  returning :%s instead of (0,0)'%(loginauth.get_usage(fromtime))

        #wtih unused sessions
        session = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)
        session.starttime = arrow.utcnow().replace(minutes=-15).naive
        session.save()
        assert loginauth.get_usage(fromtime) == (0,0) ,'get_usage \
             is  returning :(%s,%s) instead of (0,0)'%(loginauth.get_usage(fromtime)) 

        #single session uses some data
        session.data_used = 200
        session.duration = 5
        session.save()
        assert loginauth.get_usage(fromtime) == (5,200) ,'get_usage \
             is  returning :(%s,%s) instead of (30,200)'%(loginauth.get_usage(fromtime))


        #multiple sessions
        oldsess = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)

        oldsess.starttime = arrow.utcnow().replace(hours=-1).naive #very old
        oldsess.data_used = 450
        oldsess.duration = 30
        oldsess.save()

        oldsess1 = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)

        oldsess1.starttime = arrow.utcnow().replace(minutes=-10).naive #part of current window
        oldsess1.data_used = 100
        oldsess1.duration = 10
        oldsess1.save()        

        #overided sessions
        oldsess2 = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)

        oldsess2.starttime = arrow.utcnow().replace(minutes=-10).naive #part of current window
        oldsess2.data_used = 100
        oldsess2.duration = 10
        oldsess2.override = 1
        oldsess2.save()        


        assert loginauth.get_usage(fromtime) == (15,300) ,'get_usage \
             is  returning :(%s,%s) instead of(15,300)'%loginauth.get_usage(fromtime)

    def test_reset_usage(self):
        site1 = Wifisite.query.get(1)
        track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC()) 
        loginauth = self.init_loginauth(site1,track)
        fromtime = arrow.utcnow().replace(minutes=-30).naive

        session = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)
        session.starttime = arrow.utcnow().replace(minutes=-15).naive
        session.data_used = 200
        session.duration = 5
        session.save()
        #multiple sessions
        oldsess = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)

        oldsess.starttime = arrow.utcnow().replace(hours=-1).naive #very old
        oldsess.data_used = 450
        oldsess.duration = 30
        oldsess.save()
        oldsess1 = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)
        oldsess1.starttime = arrow.utcnow().replace(minutes=-10).naive #part of current window
        oldsess1.data_used = 100
        oldsess1.duration = 10
        oldsess1.save()        
        oldsess2 = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)

        oldsess2.starttime = arrow.utcnow().replace(minutes=-10).naive #part of current window
        oldsess2.data_used = 100
        oldsess2.duration = 10
        oldsess2.override = 1
        oldsess2.save()    
        ##------usage check before and after reset
        assert loginauth.get_usage(fromtime) == (15,300) ,'get_usage \
             is  returning :(%s,%s) instead of(15,300)'%loginauth.get_usage(fromtime)
        loginauth.reset_usage(fromtime)
        assert loginauth.get_usage(fromtime) == (0,0) ,'get_usage \
             is  returning :(%s,%s) instead of(15,300)'%loginauth.get_usage(fromtime)
        ###---session which is before starttime shouldn't be affected
        assert Guestsession.query.get(2).override == 0 



@pytest.mark.usefixtures('session') 
class TestGuesttrack :

    def test_updatestat(self,session):
        site1 = Wifisite.query.get(1)
        track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC()) 

        track.loginstat = {'num_visits':5}  
        track.save()

        track.updatestat('auth_email',1)


        assert track.loginstat == {'num_visits':5,'auth_email':1}, \
                    'login stat is %s'%track.loginstat

    def test_increamentstat(self,session):
        site1 = Wifisite.query.get(1)
        track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC()) 

        track.increamentstat('num_visits')
        track.increamentstat('auth_email')

        assert track.loginstat == {'num_visits':2,'auth_email':1}, \
                    'login stat is %s'%track.loginstat        