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

from tests.helpers import loggin_as_admin,loggin_as_client


fake = Faker()

def test_client_nositeid(session,populate_analytics_logins,
        populate_analytics_logins_site3):

    client = loggin_as_client()
    site1        = Wifisite.query.filter_by(id=1).first()  
    site3        = Wifisite.query.filter_by(id=3).first()  
    now    = arrow.utcnow()
    update_daily_stat(site1,now)  
    update_daily_stat(site3,now)  


    resp = client.get('/s/analytics/api/').json

    assert resp['maxsocial'] == 20