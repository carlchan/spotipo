import sys
import pytest
from flask import current_app,url_for
from flask_wtf import Form
from wtforms import TextField
from faker import Faker
import arrow
import uuid


from unifispot.core.models import Wifisite,Device,Guesttrack,Guest,Loginauth,\
                                    Guestsession
from unifispot.core.guestutils import init_track,validate_track,redirect_guest,\
            assign_guest_entry,validate_loginauth_usage
from tests.helpers import randomMAC,get_guestauth_url

fake = Faker()


def test_init_track(session):
    #
    site1 = Wifisite.query.get(1)
    apmac = randomMAC()
    mac = randomMAC()
    #test creating a new track
    track = init_track(site1,guestmac=mac,apmac=apmac)
    count = Guesttrack.query.count()
    assert 1 == count,'Guesttrack count is :%s instead of expected 1 '%count

    #another track for same MAC done immediately shouldn't create track
    track = init_track(site1,guestmac=mac,apmac=apmac)
    count = Guesttrack.query.count()
    assert 1 == count,'Guesttrack count is :%s instead of expected 1 '%count
    assert isinstance(track,Guesttrack),'init_track is not returning Guestrack instance'

    #different MAC
    track = init_track(site1,guestmac=randomMAC(),apmac=apmac)
    count = Guesttrack.query.count()
    assert 2 == count,'Guesttrack count is :%s instead of expected 2 '%count

    #same MAC after track expiry
    track = Guesttrack.query.get(1)
    track.timestamp = arrow.utcnow().replace(seconds= -(current_app.config['GUESTTRACK_LIFETIME'] + 100)).naive
    session.commit()
    track = init_track(site1,guestmac=mac,apmac=apmac)
    count = Guesttrack.query.count()
    assert 3 == count,'Guesttrack count is :%s instead of expected 3 '%count    

    #check device count
    dcount = Device.query.count()
    assert 2 == dcount,'Device count is :%s instead of expected 2 '%count    


def test_validate_track(session,client,register_testvalidateview):
    #needs a fixture defined in conftest as its a decorator
    trackid = str(uuid.uuid4())
    mac = randomMAC()
    #invalid track ID
    status = client.get('/validate_track/%s'%trackid).status
    assert '404 NOT FOUND' == status,'Status is :%s instead of 404 for invalid \
            trackid'%status

    #valid track but non-valid site
    guesttrack = Guesttrack(trackid=trackid,devicemac=mac)
    session.add(guesttrack)
    session.commit()
    status = client.get('/validate_track/%s'%trackid).status
    assert '404 NOT FOUND' == status,'Status is :%s instead of 404 for invalid \
            site'%status

    #valid site but no device
    site1 = Wifisite.query.get(1)
    guesttrack.siteid = site1.id 
    session.commit
    status = client.get('/validate_track/%s'%trackid).status
    assert '404 NOT FOUND' == status,'Status is :%s instead of 404 for invalid \
            device'%status

    device = Device(devicemac=mac,siteid=site1.id)
    session.add(device)
    session.commit()
    status = client.get('/validate_track/%s'%trackid).status
    assert '200 OK' == status,'Status is :%s instead of 200 OK for valid \
            track'%status



def test_redirect_guest(client,session):
    site1 = Wifisite.query.get(1)
    track = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())
    #nologin methods
    with current_app.test_request_context():
        resp = redirect_guest(site1,track)
        url = get_guestauth_url(site1,track.trackid)
        assert url == resp.location, 'Guest in no auth site is getting redirected to :%s instead of :%s'%\
                        (resp.location,url)


def test_assign_guest_entry(client,session):

    #create dummy email and phone forms
    class DummyForm1(Form):
        email           = TextField('Email')
        firstname       = TextField('Firstname')
        extra1          = TextField('Extra1')
        extra2          = TextField('Extra2')

    class DummyForm2(Form):
        phonenumber     = TextField('Email')
        firstname       = TextField('Firstname')
        extra1          = TextField('Extra1')

    class DummyFBProfile():
        first_name = None
        last_name = None
        email = None
        gender = None
        birthday = None
        age_range = None

    eform = DummyForm1()
    eform.email.data = 'test@gmail.com'
    eform.firstname.data = 'firstname'
    eform.extra1.data = 'extra1'
    eform.extra2.data = 'extra2'
    
    pform = DummyForm2()
    pform.phonenumber.data = '+1234567890'
    pform.firstname.data = 'firstname'
    pform.extra1.data = 'extra1'

    profile = {
        'first_name': 'first_name',  
        'last_name':'last_name',  
        'email': 'test23@gmail.com', 
        'age_range': { 'min': 21, 'max':28}  }

    site1 = Wifisite.query.get(1)
    #test creating a new track



    ##-----test email form
    track1 = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())
    track2 = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())    
    guest1 = assign_guest_entry(site1,track1,form=eform)
    guest1 = assign_guest_entry(site1,track2,form=eform)
    cnt = Guest.query.count()
    assert 1 == cnt, 'number of guest created is not 1 but :%s '%cnt
    newguest = Guest.query.get(1)
    assert newguest.details == {'Extra1':'extra1','Extra2':'extra2'}, 'Guest details is :%s insteads \
                                of expected :%s'%(newguest.details,{'Extra1':'extra1','Extra2':'extra2'})

    assert newguest.siteid == site1.id, "Guest siteid is not correctly populated"
    assert 1 == Guesttrack.query.get(1).loginstat.get('newguest'),\
            'newguest is not set to 1 after new guest added'
    assert None == Guesttrack.query.get(2).loginstat.get('newguest'),\
            'newguest is not set to None after existing guest found'

    ##-----test phone form
    track3 = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())
    track4 = init_track(site1,guestmac=randomMAC(),apmac=randomMAC()) 
    guest2 = assign_guest_entry(site1,track3,form=pform)
    guest2 = assign_guest_entry(site1,track4,form=pform)
    cnt = Guest.query.count()
    assert 2 == cnt, 'number of guest created is not 2 but :%s '%cnt
    assert 1 == Guesttrack.query.get(3).loginstat.get('newguest'),\
            'newguest is not set to 1 after new guest added'
    assert None == Guesttrack.query.get(4).loginstat.get('newguest'),\
            'newguest is not set to None after existing guest found'


    ##-----test FB profile    
    track5 = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())
    track6 = init_track(site1,guestmac=randomMAC(),apmac=randomMAC())      
    guest1 = assign_guest_entry(site1,track5,fbprofile=profile)
    guest1 = assign_guest_entry(site1,track6,fbprofile=profile)
    cnt = Guest.query.count()
    assert 3 == cnt, 'number of guest created is not 3 but :%s '%cnt
    newguest = Guest.query.get(3)
    assert 'test23@gmail.com' == newguest.email,'Wrong email '
    assert '21-28' == newguest.agerange, 'Wrong age range'
    assert 1 == Guesttrack.query.get(5).loginstat.get('newguest'),\
            'newguest is not set to 1 after new guest added'
    assert None == Guesttrack.query.get(6).loginstat.get('newguest'),\
            'newguest is not set to None after existing guest found'    

def test_validate_loginauth_usage(client,session):
    site1 = Wifisite.query.get(1)
    apmac = randomMAC()
    mac = randomMAC()
    #test creating a new track
    track = init_track(site1,guestmac=mac,apmac=apmac)
    loginauth = Loginauth(siteid=site1.id,deviceid=track.deviceid) 
    loginauth.save()

    #timenow for refference
    utcnow = arrow.utcnow()

    #create bunch of sessions
    for i in range(10):
        #wtih unused sessions
        days = -(i+1)
        session = Guestsession(siteid=site1.id,deviceid=track.deviceid,
                        loginauthid=loginauth.id)
        session.starttime = utcnow.replace(days=days).naive
        session.data_used = 50
        session.duration = 20
        session.save()    

    #fake login config
    class Loginconfig:
        def __init__(self,time_limit,data_limit):
            self.time_limit = time_limit
            self.data_limit = data_limit

    #expired data
    lconf = Loginconfig(100,50)
    starttime = utcnow.replace(days=-2).naive
    assert False == validate_loginauth_usage(site1,track,lconf,
                loginauth,starttime),'Expired datalimit not returning false'

    #expired time
    lconf = Loginconfig(20,500)
    starttime = utcnow.replace(days=-2).naive
    assert False == validate_loginauth_usage(site1,track,lconf,
                loginauth,starttime),'Expired timelimit not returning false'

    #nonexpired
    lconf = Loginconfig(200,500)
    starttime = utcnow.replace(days=-2).naive
    assert True == validate_loginauth_usage(site1,track,lconf,
                loginauth,starttime),'Non limits not returning True'    

    chkauth = Loginauth.query.get(1)
    assert int(chkauth.data_limit) == 400,'datlimit is :%s instead of expected 400'%\
                            chkauth.data_limit
    assert int(chkauth.time_limit) == 160,'time_limit is :%s instead of expected 160'%\
                            chkauth.time_limit      

    #unlimited data and limited time not expired
    lconf = Loginconfig(50,0)
    starttime = utcnow.replace(days=-2).naive
    assert True == validate_loginauth_usage(site1,track,lconf,
                loginauth,starttime),'Non limits not returning True'  
    chkauth = Loginauth.query.get(1)
    assert int(chkauth.data_limit) == 1000,'datlimit is :%s instead of expected 1000'%\
                            chkauth.data_limit
    assert int(chkauth.time_limit) == 10,'time_limit is :%s instead of expected 10'%\
                            chkauth.time_limit        
    #unlimited data and limited time  expired
    lconf = Loginconfig(30,0)
    starttime = utcnow.replace(days=-2).naive
    assert False == validate_loginauth_usage(site1,track,lconf,
                loginauth,starttime),'Non limits not returning True'  
                                                                             
    #unlimited time and limited data not expired
    lconf = Loginconfig(0,300)
    starttime = utcnow.replace(days=-2).naive
    assert True == validate_loginauth_usage(site1,track,lconf,
                loginauth,starttime),'Non limits not returning True'  
    chkauth = Loginauth.query.get(1)
    assert int(chkauth.data_limit) == 200,'datlimit is :%s instead of expected 200'%\
                            chkauth.data_limit
    assert int(chkauth.time_limit) == 480,'time_limit is :%s instead of expected 480'%\
                            chkauth.time_limit        
    #unlimited time and limited data  expired
    lconf = Loginconfig(0,30)
    starttime = utcnow.replace(days=-2).naive
    assert False == validate_loginauth_usage(site1,track,lconf,
                loginauth,starttime),'Non limits not returning True'                                                                              

    