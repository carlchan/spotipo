import sys
import pytest
from flask import current_app
from flask_wtf import Form
from wtforms import TextField
from faker import Faker
import arrow
import uuid


from unifispot.core.models import Wifisite,Device,Guesttrack
from tests.helpers import get_guestentry_url,randomMAC,loggin_as_admin

def test_guest_portal(session,client):
    #test unifi entry point
    site1 = Wifisite.query.get(1)


    #with emptry MAC/APMAC
    res = client.get(get_guestentry_url(site1)).status
    assert '404 NOT FOUND' == res , 'Getting :%s instead 404 for\
         with empty MAC/APMAC' %res


    #with invalid  MAC/APMAC
    res = client.get(get_guestentry_url(site1,mac='11:22:33:44',apmac='22:44:55')).status
    assert '404 NOT FOUND' == res , 'Getting :%s instead 404 for\
         with empty MAC/APMAC' %res         


    #with invalid  sitekey
    site2 = Wifisite(sitekey = 'test',backend_type='unifi')
    res = client.get(get_guestentry_url(site2,mac=randomMAC(),apmac=randomMAC())).status
    assert '404 NOT FOUND' == res , 'Getting :%s instead 404 for\
         with invalid sitekey' %res    

    #with everything valid
    res = client.get(get_guestentry_url(site1,mac=randomMAC(),apmac=randomMAC())).status
    assert '302 FOUND' == res , 'Getting :%s instead 302 FOUND for\
         with valid data' %res             
    assert 1 == Guesttrack.query.count(),'More than one guesttrack '

    #check demo is not set with no-auth visit
    mac=randomMAC()
    res = client.get(get_guestentry_url(site1,mac=mac,apmac=randomMAC(),demo=1)).status
    assert '302 FOUND' == res , 'Getting :%s instead 302 FOUND for\
         with valid data' %res             
    assert 0 == Guesttrack.query.filter_by(devicemac=mac).first().demo,\
                'Demo is not rejected for non auth visits '


    #check demo is not set with auth visit
    mac=randomMAC()
    admin = loggin_as_admin()
    res = admin.get(get_guestentry_url(site1,mac=mac,apmac=randomMAC(),demo=1)).status
    assert '302 FOUND' == res , 'Getting :%s instead 302 FOUND for\
         with valid data' %res             
    assert 1 == Guesttrack.query.filter_by(devicemac=mac).first().demo,\
                'Demo is  rejected for auth visits '

