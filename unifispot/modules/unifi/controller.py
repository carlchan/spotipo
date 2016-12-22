#based on https://github.com/calmh/unifi-api
#This file is licensed under MIT
#https://github.com/calmh/unifi-api/blob/master/LICENSE
try:
    # Ugly hack to force SSLv3 and avoid
    # urllib2.URLError: <urlopen error [Errno 1] _ssl.c:504:
    # error:14077438:SSL routines:SSL23_GET_SERVER_HELLO:tlsv1 alert internal error>
    import _ssl
    _ssl.PROTOCOL_SSLv23 = _ssl.PROTOCOL_TLSv1
except:
    pass

try:
    # Updated for python certificate validation
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass


import cookielib
import urllib2
import requests
import os
import hashlib
import pickle
import requests_cache
import json
import logging
from time import time
import urllib


log = logging.getLogger(__name__)


class APIError(Exception):
    pass


class Controller:

    """Interact with a UniFi controller.

    Uses the JSON interface on port 8443 (HTTPS) to communicate with a UniFi
    controller. Operations will raise unifi.controller.APIError on obvious
    problems (such as login failure), but many errors (such as disconnecting a
    nonexistant client) will go unreported.

    >>> from unifi.controller import Controller
    >>> c = Controller('192.168.1.99', 'admin', 'p4ssw0rd')
    >>> for ap in c.get_aps():
    ...     print 'AP named %s with MAC %s' % (ap['name'], ap['mac'])
    ...
    AP named Study with MAC dc:9f:db:1a:59:07
    AP named Living Room with MAC dc:9f:db:1a:59:08
    AP named Garage with MAC dc:9f:db:1a:59:0b

    """

    def __init__(self,account,sitekey):
        """Create a Controller object.

        Arguments:
            host     -- the address of the controller host; IP or name
            username -- the username to log in with
            password -- the password to log in with
            port     -- the port of the controller host
            version  -- the base version of the controller API [v2|v3|v4]
            sitekey  -- the site ID to connect to (UniFi >= 3.x)

        """

        self.host = account.unifi_server
        self.port = account.unifi_port
        self.version = account.unifi_version or 'v4'
        self.username = account.unifi_user
        self.password = account.unifi_pass
        self.sitekey = sitekey
        self.url = 'https://' + self.host + ':' + str(self.port) + '/'
        self.api_url = self.url + self._construct_api_path(self.version)
        #keep cookies in a file for later use
        cookie_folder = os.path.join(os.path.abspath(
                            os.path.dirname(__file__)),'..','..','..','instance')
        url_hash = hashlib.md5(self.url).hexdigest()
        self.cookiefile = os.path.join(cookie_folder,url_hash)
        self.session = requests.Session()
        #automatic request retries http://www.mobify.com/blog/http-requests-are-hard/
        # `mount` a custom adapter that retries failed 
        # connections for HTTP and HTTPS requests.
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries=4))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries=4))
        log.debug('Controller for %s', self.url)


    def save_cookies(self):
        with open(self.cookiefile, 'w') as f:
            f.truncate()
            pickle.dump(self.session.cookies._cookies, f)



    def load_cookies(self):
        if not os.path.isfile(self.cookiefile):
            return False

        with open(self.cookiefile) as f:
            cookies = pickle.load(f)
            if cookies:
                jar = requests.cookies.RequestsCookieJar()
                jar._cookies = cookies
                self.session.cookies = jar
                return True
            else:
                return False

    def _jsondec(self, data):
        obj = json.loads(data)

        if 'meta' in obj:
            if obj['meta']['rc'] != 'ok':
                raise APIError(obj['meta']['msg'])
        if 'data' in obj:
            return obj['data']
        return obj

    def _construct_api_path(self, version,sitekey=None):
        """Returns valid base API path based on version given

           The base API path for the URL is different depending on UniFi server version.
           Default returns correct path for latest known stable working versions.

        """
        if not sitekey:
            sitekey = self.sitekey

        V2_PATH = 'api/'
        V3_PATH = 'api/s/' + sitekey + '/'

        if(version == 'v2'):
            return V2_PATH
        if(version == 'v3'):
            return V3_PATH
        if(version == 'v4'):
            return V3_PATH
        else:
            return V2_PATH        

    def _read(self, url, params=None,cache=False,method='get'):
        if not self.load_cookies() :           
            log.debug('No cookies found for controller %s going to try login'%self.url)
            self._login()

        func = getattr(self.session,method)

        r = func(url,json=params,verify=False)
        if r.status_code == 401: # maybe session expired
            log.debug('Looks like session expired for %s going to try login'%self.url)
            self._login()   
            r = func(url,json=params,verify=False)
            r.raise_for_status() 
        else:
            r.raise_for_status()   
        return self._jsondec(r.text)

    def _login(self):
        log.debug('login() as %s', self.username)
        params = "{'username':'" + self.username + "',\
                    'password':'" + self.password + "'}"
        r = self.session.post(self.url + 'api/login',data=params,verify=False)
        r.raise_for_status()
        self.save_cookies()

    def get_events(self):
        """Return a list of all Events."""

        return self._read(self.api_url + 'stat/event')

    def get_clients(self):
        """Return a list of all active clients, with significant information about each."""

        return self._read(self.api_url + 'stat/sta')
        
    def _run_command(self, command, params={}, mgr='stamgr',sitekey =None):
        if not sitekey:
            sitekey = self.sitekey
        api_url = self.url + self._construct_api_path(self.version,sitekey=sitekey)
        log.debug('_run_command(%s)', command)
        params.update({'cmd': command})
        return self._read(api_url+ 'cmd/' + mgr, params,method='post')

    def _set_setting(self,sitekey, params={}, category='super_smtp'):
        if not sitekey:
            sitekey = self.sitekey
        api_url = self.url + self._construct_api_path(self.version,sitekey=sitekey)
        log.debug('_set_setting(%s)', category)
        return self._read(api_url + 'set/setting/' + category, params)        

    def authorize_guest(self, guest_mac, minutes=60, up_bandwidth=None, 
                            down_bandwidth=None, byte_quota=None, ap_mac=None):
        """
        Authorize a guest based on his MAC address.

        Arguments:
            guest_mac     -- the guest MAC address : aa:bb:cc:dd:ee:ff
            minutes       -- duration of the authorization in minutes
            up_bandwith   -- up speed allowed in kbps (optional)
            down_bandwith -- down speed allowed in kbps (optional)
            byte_quota    -- quantity of bytes allowed in MB (optional)
            ap_mac        -- access point MAC address (UniFi >= 3.x) (optional)
        """
        cmd = 'authorize-guest'
        if minutes > 480 :
            minutes = 480
        js = {'mac': guest_mac, 'minutes': minutes}

        if up_bandwidth:
            js['up'] = up_bandwidth
        if down_bandwidth:
            js['down'] = down_bandwidth
        if byte_quota:
            js['bytes'] = byte_quota
        if ap_mac and self.version != 'v2':
            js['ap_mac'] = ap_mac

        try:
            self._run_command(cmd, params=js)
        except Exception as e:
            log.exception('Error while trying to authorize guest:%s \
                                for controller:%s'%(guest_mac,self.url))


    def get_sites(self):
        """Return a list of all sites, with significant information about each."""
        
        return self._read(self.url + 'api/self/sites')            

    def unauthorize_guest(self, guest_mac):
        """
        Unauthorize a guest based on his MAC address.

        Arguments:
            guest_mac -- the guest MAC address : aa:bb:cc:dd:ee:ff
        """
        cmd = 'unauthorize-guest'
        js = {'mac': guest_mac}
        try:
            self._run_command(cmd, params=js)
        except:
            log.exception('Error while trying to unauthorize-guest guest:%s \
                                for controller:%s'%(guest_mac,self.url))  
            return None
        return 1                      

    def set_guest_access(self,sitekey,site_code,portal_ip,portal_subnet,portal_hostname):

        """Set SMTP seetings for this site

        Arguments:


        """
        log.debug('setting Guest settings for site:%s',sitekey )


        fb_ips = ['204.15.20.0/22','69.63.176.0/20','66.220.144.0/20','66.220.144.0/21','69.63.184.0/21','69.63.176.0/21','74.119.76.0/22','69.171.255.0/24','173.252.64.0/18','69.171.224.0/19','69.171.224.0/20','103.4.96.0/22','69.63.176.0/24','173.252.64.0/19','173.252.70.0/24','31.13.64.0/18','31.13.24.0/21','66.220.152.0/21','66.220.159.0/24','69.171.239.0/24','69.171.240.0/20','31.13.64.0/19','31.13.64.0/24','31.13.65.0/24','31.13.67.0/24','31.13.68.0/24','31.13.69.0/24','31.13.70.0/24','31.13.71.0/24','31.13.72.0/24','31.13.73.0/24','31.13.74.0/24','31.13.75.0/24','31.13.76.0/24','31.13.77.0/24','31.13.96.0/19','31.13.66.0/24','173.252.96.0/19','69.63.178.0/24','31.13.78.0/24','31.13.79.0/24','31.13.80.0/24','31.13.82.0/24','31.13.83.0/24','31.13.84.0/24','31.13.85.0/24','31.13.86.0/24','31.13.87.0/24','31.13.88.0/24','31.13.89.0/24','31.13.90.0/24','31.13.91.0/24','31.13.92.0/24','31.13.93.0/24','31.13.94.0/24','31.13.95.0/24','69.171.253.0/24','69.63.186.0/24','31.13.81.0/24','179.60.192.0/22','179.60.192.0/24','179.60.193.0/24','179.60.194.0/24','179.60.195.0/24','185.60.216.0/22','45.64.40.0/22','185.60.216.0/24','185.60.217.0/24','185.60.218.0/24','185.60.219.0/24','129.134.0.0/16','157.240.0.0/16','204.15.20.0/22','69.63.176.0/20','69.63.176.0/21','69.63.184.0/21','66.220.144.0/20','69.63.176.0/20']

        params =  {"portal_enabled":True,"auth":"custom","x_password":"",
                    "expire":"480","redirect_enabled":False,"redirect_url":'',
                    "custom_ip":portal_ip,"portal_customized":False,
                    "portal_use_hostname":True,"portal_hostname":portal_hostname,
                    "voucher_enabled":False,"payment_enabled":False,
                    "gateway":"paypal","x_paypal_username":"","x_paypal_password":"",
                    "x_paypal_signature":"","paypal_use_sandbox":False,
                    "x_stripe_api_key":"","x_quickpay_merchantid":"",
                    "x_quickpay_md5secret":"","x_authorize_loginid":"",
                    "x_authorize_transactionkey":"","authorize_use_sandbox":False,
                    "x_merchantwarrior_merchantuuid":"","x_merchantwarrior_apikey":"",
                    "x_merchantwarrior_apipassphrase":"",
                    "merchantwarrior_use_sandbox":False,"x_ippay_terminalid":"",
                    "ippay_use_sandbox":False,"restricted_subnet_1":"192.168.0.0/16",
                    "restricted_subnet_2":"172.16.0.0/12",
                    "restricted_subnet_3":"10.0.0.0/8","allowed_subnet_1":portal_subnet,
                    "key":"guest_access","sitekey":site_code}  

        index = 2
        for ip in fb_ips:
            params['allowed_subnet_%s'%index] = ip
            index += 1

        return self._set_setting(sitekey=sitekey,params=params, category='guest_access')  

