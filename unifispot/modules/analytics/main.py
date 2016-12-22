from flask import request,abort,render_template,redirect,url_for,jsonify
import arrow
import logging
from flask_security import current_user,login_required
import validators
from functools import wraps


from unifispot.core.app import UnifispotModule
from unifispot.core.utils import  get_form_errors,validate_site_ownership
from unifispot.core.models import Wifisite
from .models import Sitestat
logger =logging.getLogger('analytics')

module = UnifispotModule('analytics','general', __name__, template_folder='templates')


@module.route('/s/analytics/api/',methods = ['GET', 'POST'])
@module.route('/s/analytics/api/<id>',methods = ['GET', 'POST'])
@login_required
def get_analytics(id=None):
    #need to do custom id validation
    start = request.args.get('start')
    end   = request.args.get('end') 
    try:
        end_date    = arrow.get(end,'DD-MM-YYYY')
        start_date  = arrow.get(start,'DD-MM-YYYY')
    except:
        logger.exception('Exception while converting start/end dates in :%s'\
                        %request.url)
        end_date    = arrow.now() 
        start_date  = end_date.replace(days=-29)   
    if id:
        wifisite = Wifisite.query.get(1)     
        if not wifisite or ( current_user.type == 'admin' and \
                wifisite.account_id != current_user.account_id) or\
                (current_user.type =='client' and wifisite.client_id != current_user.id):
            logger.error('User:%s trying to access invalid/unauth site:%s'%\
                            (current_user.id,id))
        basequery = Sitestat.query.filter(Sitestat.siteid==id)
    else:
        if current_user.type == 'client':
            basequery = Sitestat.query.outerjoin(Wifisite).\
                filter(Wifisite.client_id==current_user.id)
        else:
            basequery = Sitestat.query.outerjoin(Wifisite).\
                filter(Wifisite.account_id==current_user.account_id)   

    #loop over dates
    newguests = []
    totallogins = []
    totalcheckins = []
    totallikes = []
    combinedstats = {}
    currdate = start_date   
    maxlogin = 0
    maxsocial = 0
    numlikes =0 
    numcheckins =0
    while currdate <= end_date:
        
        timestamp = currdate.timestamp * 1000
        daystat = basequery.filter(Sitestat.date==currdate.floor('day').naive).first()
        if daystat:
            statdict = daystat.to_dict()
            logins = daystat.num_newlogins + daystat.num_repeats
            #create new guests list            
            newguests.append((timestamp,daystat.num_newlogins))
            #update maxlogin
            if logins > maxlogin:
                maxlogin = logins
            #create checkins list
            numcheckins = statdict.get('fbcheckedin',0)
            totalcheckins.append((timestamp,numcheckins))
            if numcheckins > maxsocial:
                maxsocial = numcheckins
            #create likes list
            numlikes = statdict.get('fbliked',0)
            totallikes.append((timestamp,numlikes))
            if numlikes > maxsocial:
                maxsocial = numlikes
            #create total logins list
            totallogins.append((timestamp,logins))
            #update combinestats
            keys = list(set(combinedstats.keys( ) + statdict.keys()))
            for key in keys:
                try:
                    val1 = int(combinedstats.get(key,0))
                    val2 = int(statdict.get(key,0))
                except:
                    pass
                else:
                    combinedstats[key] = val1 + val2               
        else:
            newguests.append((timestamp,0))
            totallogins.append((timestamp,0))     
            totalcheckins.append((timestamp,0))     
            totallikes.append((timestamp,0))     
        currdate=currdate.replace(days=1)      


    combinedstats.update({'status': 1,'logins':totallogins,
            'newlogins':newguests,'maxlogin':maxlogin,
            'likes':totallikes,
            'checkins':totalcheckins,
            'maxsocial':maxsocial,
            'numcheckins':numcheckins,
            'numlikes':numlikes})
    return jsonify(combinedstats)