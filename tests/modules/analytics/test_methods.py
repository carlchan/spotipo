import sys
import pytest
from flask import current_app,url_for
from flask_wtf import Form
from wtforms import TextField
from faker import Faker
import arrow
import uuid
import stripe


from unifispot.core.models import Wifisite,Device,Guesttrack,Guest
from unifispot.core.guestutils import init_track,validate_track,redirect_guest
from unifispot.core.const import *

from unifispot.modules.analytics.methods import update_daily_stat
from unifispot.modules.analytics.models import Sitestat


from tests.helpers import randomMAC

fake = Faker()

def test_update_daily_stat1(session,client):
    '''test with empty tracks 

    '''
    site1        = Wifisite.query.filter_by(id=1).first()  
    now    = arrow.utcnow()
    update_daily_stat(site1,now)  

    assert 1 == Sitestat.query.count() , 'Sitestat is not created '


def test_update_daily_stat2(session,populate_analytics_tracks):
    '''Check if time validation is fine

    '''
    site1        = Wifisite.query.filter_by(id=1).first()  
    now    = arrow.utcnow()
    update_daily_stat(site1,now)  

    sitestat = Sitestat.query.get(1) 
    assert 20 == sitestat.num_visits

def test_update_daily_stat3(session,populate_analytics_logins):
    '''Check if stat counting is fine

    '''    
    site1        = Wifisite.query.filter_by(id=1).first()  
    now    = arrow.utcnow()
    update_daily_stat(site1,now)  

    sitestat = Sitestat.query.get(1) 
    assert 40 == sitestat.num_visits    
    assert 20 == sitestat.num_newlogins    
    assert 20 == sitestat.num_repeats    
    assert {'auth_email': 20, 'auth_facebook': 20, 'fbcheckedin': 20, 
            'fbliked': 10,'newguest': 20, u'num_visits': 40}\
                         == sitestat.login_stat    