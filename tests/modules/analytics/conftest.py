import pytest
from dateutil import tz
import arrow

from unifispot.core.models import Wifisite,Device,Guesttrack,Guest
from unifispot.core.guestutils import init_track,validate_track,redirect_guest
from unifispot.modules.payment.models import Package,Transaction,Paymentconfig
from tests.helpers import randomMAC

@pytest.fixture(scope='function')
def populate_analytics_tracks(request,session):
    '''fixture used to create a number of guestracks spans today,yesterday and day after
       
    '''
    site1        = Wifisite.query.filter_by(id=1).first()  

    tzinfo = tz.gettz(site1.timezone)
    day_start   = arrow.now(tzinfo).floor('day').to('UTC')

    apmac =randomMAC()

    #create 20 tracks, starting from day start and spaced 1minutes apart
    for i in range(20):
        track_dict = {'num_visits':1}
        track = init_track(site1,guestmac=randomMAC(),apmac=apmac)
        track.timestamp = day_start.replace(minutes=+i*1).naive

        track.save()

    day_start = arrow.now(tzinfo).floor('day').to('UTC').replace(days=-1)
    #create 20 tracks, starting from day start and spaced 1minutes apart on previous day
    for i in range(20):
        track_dict = {'num_visits':1}
        track = init_track(site1,guestmac=randomMAC(),apmac=apmac)
        track.timestamp = day_start.replace(minutes=+i*1).naive
        track.save()

    day_start = arrow.now(tzinfo).floor('day').to('UTC').replace(days=+1)
    #create 20 tracks, starting from day start and spaced 1minutes apart on next day
    for i in range(20):

        track = init_track(site1,guestmac=randomMAC(),apmac=apmac)
        track.loginstat = {'num_visits':1}
        track.timestamp = day_start.replace(minutes=+i*1).naive
        track.save() 

@pytest.fixture(scope='function')
def populate_analytics_logins(request,session):
    '''fixture used to create a number of guestracks with logins
       
    '''
    site1        = Wifisite.query.filter_by(id=1).first()  

    tzinfo = tz.gettz(site1.timezone)
    day_start   = arrow.now(tzinfo).floor('day').to('UTC')

    apmac =randomMAC()

    #create 20 tracks, for email login
    #half of them new user
    for i in range(20):        
        track = init_track(site1,guestmac=randomMAC(),apmac=apmac)
        track.timestamp = day_start.replace(minutes=+i*1).naive
        track.loginstat =  {'num_visits':1,'auth_email':1}
        track.save()
        if i%2:
            track.updatestat('newguest',1)
            track.save()    
    #create 20 tracks, for FB login
    #half of them new user
    for i in range(20):        
        track = init_track(site1,guestmac=randomMAC(),apmac=apmac)
        track.timestamp = day_start.replace(minutes=+i*1).naive
        track.loginstat =  {'num_visits':1,'auth_facebook':1,'fbcheckedin':1}
        track.save()
        if i%2:
            track.updatestat('newguest',1)
            track.updatestat('fbliked',1)
            track.save()                

@pytest.fixture(scope='function')
def populate_analytics_logins_site3(request,session):
    '''fixture used to create a number of guestracks with logins
       
    '''
    site1        = Wifisite.query.filter_by(id=3).first()  

    tzinfo = tz.gettz(site1.timezone)
    day_start   = arrow.now(tzinfo).floor('day').to('UTC')

    apmac =randomMAC()

    #create 20 tracks, for email login
    #half of them new user
    for i in range(20):        
        track = init_track(site1,guestmac=randomMAC(),apmac=apmac)
        track.timestamp = day_start.replace(minutes=+i*1).naive
        track.loginstat =  {'num_visits':1,'auth_email':1}
        track.save()
        if i%2:
            track.updatestat('newguest',1)
            track.save()    
    #create 20 tracks, for FB login
    #half of them new user
    for i in range(20):        
        track = init_track(site1,guestmac=randomMAC(),apmac=apmac)
        track.timestamp = day_start.replace(minutes=+i*1).naive
        track.loginstat =  {'num_visits':1,'auth_facebook':1,'fbcheckedin':1}
        track.save()
        if i%2:
            track.updatestat('newguest',1)
            track.updatestat('fbliked',1)
            track.save()              