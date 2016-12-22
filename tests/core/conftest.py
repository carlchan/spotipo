import sys
import pytest
from flask import current_app


from unifispot.core.models import Wifisite,Device,Guesttrack
from unifispot.core.guestutils import validate_track,redirect_guest

from .test_baseviews import TestView


##keep all fixtures here which need to register a view or something
#-------------------------------for test_guestutils----------------------
@pytest.fixture(scope='session')
def register_testvalidateview(app):
    #create a test view for testing validate_track
    @current_app.route('/validate_track/<trackid>')
    @validate_track
    def trackview(trackid,*args,**kwargs):
        assert isinstance(kwargs['wifisite'],Wifisite)
        assert isinstance(kwargs['guesttrack'],Guesttrack)
        assert isinstance(kwargs['guestdevice'],Device)
        return 'OK'

@pytest.fixture(scope='session')
def register_testredirectguest(app):
    #create a test view for testing validate_track
    @current_app.route('/redirectlanding/<trackid>')
    def redirectguest(trackid,*args,**kwargs):
        guesttrack  = Guesttrack.query.filter_by(trackid=trackid).first()
        wifisite    = Wifisite.query.filter_by(id=guesttrack.siteid).first()
        return redirect_guest(wifisite,guesttrack)



###----------------------------for test_redirect_to_landing----------------
@pytest.fixture(scope='session')
def register_testview(app):
    TestView.register(current_app, route_base='/test')        