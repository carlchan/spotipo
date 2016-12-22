import os
import logging
import arrow
from flask import render_template,current_app
from premailer import transform,Premailer
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from dateutil import tz


from unifispot.core.models import Wifisite,Guestsession
from unifispot.ext.celeryext import celery
from unifispot.core.utils import send_email

from .methods import update_daily_stat

logger =logging.getLogger('analytics.tasks')

@periodic_task(run_every=(crontab(minute="*/5")))
def celery_update_stat(*args, **kwargs):
    logger.info('-----------Running celery_update_stat-----------------------')
    sites = Wifisite.query.all()
    for site in sites:
        tzinfo = tz.gettz(site.timezone)
        now    = arrow.now(tzinfo)
        #process today's status for this site
        update_daily_stat(site,now)
        if now.hour < 2:
            #process yesterday's stats as well
            yesterday = now.replace(days=-1)
            update_daily_stat(site,yesterday)

@celery.task(autoretry_on=Exception,max_retries=5)
def celery_test(guestid=None):     
    logger.info('-----------Running TESTSTSSTSS-----------------------')       
    sites = Wifisite.query.all()
    for site in sites: 
        logger.info('-----------SITE NAME:-----------------------'%site.name)