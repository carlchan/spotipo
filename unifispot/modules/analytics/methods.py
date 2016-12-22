import os
import logging
import arrow
from flask import render_template,current_app
from premailer import transform,Premailer
from dateutil import tz
from sqlalchemy import and_,or_


from unifispot.core.models import Wifisite,Guestsession,Guesttrack,Loginauth,\
                                    Guest,Device
from .models import Sitestat

logger =logging.getLogger('analytics.methods')



def update_daily_stat(wifisite,daydate):
    '''Update daily status of a particular site on the given date.

        siteid => siteid
        daydate => arrow date with timezone

        Creates/updates an entry in Sitestat corresponding to 
            given date start (on site's timezone/logical time)

    '''
    day_start   = daydate.floor('day').to('UTC').naive
    day_end     = daydate.ceil('day').to('UTC').naive

    tracks_dict     = {} 
    logins_dict     = {}  

    def update_login_types(track):
        loginauth_stats = track.loginstat
        #update logins_dict with combined 
        dict1 = logins_dict
        
        keys = list(set(dict1.keys( ) + loginauth_stats.keys()))
        for key in keys:
            logins_dict[key] = int(dict1.get(key,0)) + \
                                int(loginauth_stats.get(key,0))    

    tracks = Guesttrack.query.filter(and_(Guesttrack.siteid==wifisite.id,
                    Guesttrack.timestamp>=day_start,
                    Guesttrack.timestamp<=day_end)).all()  



    for track in tracks:
        #count the number of logins
        prv_track = tracks_dict.get(track.deviceid)    
        if prv_track:
            #sess already added,check time difference
            prv_time = arrow.get(prv_track)
            new_time = arrow.get(track.timestamp)
            time_diff = (new_time - prv_time).seconds
            if time_diff > 600:
                #more than 10min difference       
                update_login_types(track)       
            elif time_diff > 0:
                #update mac time
                tracks_dict[track.deviceid] = new_time
        else:
            tracks_dict[track.deviceid] = arrow.get(track.timestamp)  
            update_login_types(track)    

    day_key = daydate.floor('day').naive
    #check if sitestat entry already exists for this site on the date
    check_sitestat = Sitestat.query.filter_by(siteid=wifisite.id,
                    date=day_key).first()
    if not check_sitestat:
        #add new entry
        check_sitestat = Sitestat(siteid=wifisite.id,
                        account_id=wifisite.account_id,
                        date=day_key)
        check_sitestat.save()

    #get total logins count
    num_logins = 0
    for key in logins_dict.keys():
        if key.startswith('auth_'):
            num_logins = num_logins + logins_dict.get(key,0)


    check_sitestat.login_stat       = logins_dict
    check_sitestat.num_newlogins    = logins_dict.get('newguest',0)
    check_sitestat.num_repeats      = num_logins - logins_dict.get('newguest',0)
    check_sitestat.num_visits       = logins_dict.get('num_visits',0)
    check_sitestat.last_updated     = arrow.utcnow().naive
    check_sitestat.save()





