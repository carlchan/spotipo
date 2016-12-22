import os
import logging
import arrow
import math
from flask import render_template,current_app
from premailer import transform,Premailer
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from dateutil import tz
from sqlalchemy import and_,or_
from pymongo import MongoClient

from unifispot.core.models import Wifisite,Guestsession,Loginauth,Account
from unifispot.ext.celeryext import celery

from .controller import Controller

logger =logging.getLogger('unifi.tasks')

@periodic_task(run_every=(crontab(minute="*/5")))
def celery_session_monitor(*args, **kwargs):
    logger.info('-----------Running celery_session_monitor-----------------------')
    sites = Wifisite.query.filter_by(backend_type='unifi').all()
    for site in sites:         
        logger.info('celery_session_monitor processing Site:%s'%site.name)       
        account = Account.query.get(site.account_id)
        try:
            c = Controller(account=account,sitekey=site.sitekey) 
            #get all STAs
            stas = c.get_clients()
            for sta in stas:
                if sta.get('is_guest') and sta.get('authorized'):
                    rx_bytes = int(sta.get('rx_bytes'))
                    tx_bytes = int(sta.get('tx_bytes'))
                    total_data = rx_bytes + tx_bytes 
                    data_mb    = int(math.ceil((total_data/1024000.0)))                    
                    mac = sta.get('mac')
                    guestsession = Guestsession.query.filter_by(siteid=site.id,
                                        mac=mac).first()
                    if not guestsession:
                        logger.warn('celery_session_monitor - MAC:%s in site:%s have no \
                                    session'%(mac,site.name))
                        continue
                    logger.debug(' celery_session_monitor - MAC:%s in site:%s seems to \
                            have used data:%s Mb'%(mac,site.name,data_mb))                         
                    loginauth = Loginauth.query.get(guestsession.loginauthid)
                    if data_mb > loginauth.data_available():
                        logger.debug('celery_session_monitor.mac_kick MAC:%s site:%s'%\
                                            (mac,site.name))
                        c.unauthorize_guest(mac)                     

        except:
            logger.exception('Exception while monitoring site:%s'%site.name)                



@periodic_task(run_every=(crontab(minute="*/5")))
def celery_session_history(*args, **kwargs):
    logger.info('-----------Running celery_session_history-----------------------')
    client = MongoClient('localhost', 27117)
    mongodb = client['ace']
    guests = mongodb['guest']
    sites  = mongodb['site']

    #get all sites in mongodb and try to map to an equivalent wifisite
    site_dict = {}
    for site in sites.find():
        print site
        wifisite = Wifisite.query.filter_by(sitekey=site['name']).first()
        siteid = None
        if wifisite:
            siteid = wifisite.id    

        site_dict[str(site['_id'])] = siteid


    #get all sessions
    utcwindow = arrow.utcnow().replace(minutes=-10).timestamp

    logger.debug('Checking guest sessions')

    for guest in guests.find({'end':{'$gt':utcwindow}}):
        start = arrow.get(guest.get('start')).humanize()
        end   = arrow.get(guest.get('end')).humanize()
        tx_bytes = guest.get('tx_bytes',0)
        rx_bytes = guest.get('rx_bytes',0)
        obj_id = str(guest['_id'])
        mac = guest['mac']
        logger.debug('MAC:%s Start:%s End:%s  Site:%s TX:%s RX:%s'%(mac,start,
                            end,site_dict.get(guest['site_id']),tx_bytes,rx_bytes))
        #check if the guest belongs to a known wifisite
        siteid = site_dict.get(guest['site_id'])
        if siteid:            
            guestsession = Guestsession.query.filter_by(obj_id=obj_id,siteid=siteid).first()
            data_mb = int(math.ceil(((tx_bytes + rx_bytes)/1024000.0))) 
            #if this session was logged before
            if guestsession:
                duration              = guest.get('duration')
                if duration:
                    guestsession.duration = int(duration/60.0)
                guestsession.stoptime = arrow.get(guest.get('end')).naive
                guestsession.data_used = data_mb
                guestsession.save()
                logger.debug('Updated Guestsession:%s for MAC:%s in SiteID:%s \
                                Starttime:%s to:%s'%(guestsession.id,mac,siteid,start,
                                obj_id))
            else:
                #find all recent sessions of this MAC
                session_start = arrow.get(guest.get('start')).replace(minutes=-1).naive
                guestsession = Guestsession.query.filter(and_(Guestsession.siteid==siteid,
                        Guestsession.mac==mac,Guestsession.starttime >=session_start)).first()
                if not guestsession:
                    logger.error('No session found for MAC:%s in SiteID:%s \
                                Starttime:%s'%(mac,siteid,start))
                    continue
                guestsession.stoptime = arrow.get(guest.get('end')).naive
                guestsession.data_used = data_mb
                guestsession.obj_id = obj_id
                guestsession.save()
                logger.debug('Connected Guestsession:%s for MAC:%s in SiteID:%s\
                         Starttime:%s to :%s'%(guestsession.id,mac,siteid,start,obj_id))
            #validate if this session has exceeded limit
            
            loginauth = Loginauth.query.get(guestsession.loginauthid)
            if data_mb > loginauth.data_available():
                site = Wifisite.query.get(siteid)
                account = Account.query.get(site.account_id)
                logger.debug('celery_session_history.mac_kick MAC:%s site:%s'\
                            %(mac,site.name))
                c = Controller(account=account,sitekey=site.sitekey) 
                c.unauthorize_guest(mac) 




