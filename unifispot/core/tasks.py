import os
import logging
import arrow
from flask import render_template,current_app
from premailer import transform,Premailer
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from dateutil import tz
import requests


from unifispot.core.models import Wifisite,Guestsession,Notification,Account
from unifispot.ext.celeryext import celery
from unifispot.core.utils import send_email,compare_versions
from unifispot.version import version

logger =logging.getLogger('core.tasks')


@periodic_task(run_every=(crontab(minute=0,hour="*/1")))
def celery_get_notification(*args, **kwargs):
    '''Connect to https://notify.unifispot.com/notify.json and get notifications

    '''
    logger.info('-----------Running celery_get_notification-----------------------')
    accounts = Account.query.all()
    for account in accounts:
        token= account.token
        url = current_app.config['NOTIFICATION_URL'] + token
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        for notify in data.get('notifications'):
            if not  Notification.check_notify_added(notify.get('notifi_id')):
                #check if version id specified
                if  notify.get('version') and compare_versions(notify.get('version'),version) != 0:
                    break
                elif notify.get('min_version') and compare_versions(notify.get('min_version'),version) == 1:
                    break
                elif notify.get('max_version') and compare_versions(notify.get('max_version'),version) == -1:
                    break
                n =Notification(content=notify['content'],notifi_type=notify['notifi_type'],
                                notifi_id=notify['notifi_id'],user_id=0,account_id=account.id)
                n.save()
         
    return 1