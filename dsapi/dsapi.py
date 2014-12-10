#/!/usr/bin/env python

import requests, sys, os, logging, datetime, time, json
import ssl
ssl.OP_NO_TLSv1_2=True
ssl.op_NO_TLSv1_1=True
####mods to force tls1#####
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager


class tlsHttpAdapter(HTTPAdapter):
    """"Transport adapter" that allows us to force use of TLSv1."""

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)
#####end ssl mod####



class DataStreamAPI(object):
    def __init__(self, endpoint, clientid, clientsecret,log_level="WARNING"):
        self._endpoint = endpoint
        self._clientid = clientid
        self._clientsecret = clientsecret
        self._authid = None
        self.session = requests.Session()
        self.session.mount(endpoint, tlsHttpAdapter())       
        self.configure_logging(log_level)

    @property
    def authid(self):
        return self._authid

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def package_dir(self, endpoint):
        self._endpoint = endpoint

    @property
    def clientid(self):
        return self._clientid

    @clientid.setter
    def package_dir(self, clientid):
        self._clientid = clientid

    @property
    def clientsecret(self):
        return self._clientsecret

    @clientsecret.setter
    def package_dir(self, clientsecret):
        self._clientsecret = clientsecret

    def __api_get_auth_key(self, endpoint, clientid, clientsecret):
        """low-level private method to obtain a refreshed auth key from DataStream API
        """
        url = "%soauth/access_token/?grant_type=client_credentials&client_id=%s&client_secret=%s" % (endpoint, clientid, clientsecret)
        logger.debug("Auth key url:%s" % (url))
        r = self.session.get(url)
        logger.debug("request status: %s" % (r.status_code))
        if r.status_code != 200:
            for x in range(10):
                time.sleep(1)
                r = requests.get(url)
                if r.status_code == 200:
                    break;
        if r.status_code !=200:
            logger.critical("Unable to get auth key after 10 tries, last status_code: %s" % r.status_code)
            sys.exit(1)
        data = r.json()
        logger.debug("json return from auth key url: %s" % (data))
        if "access_token" in data:
            return data['access_token']
        else:
            logger.critical("Unable to obtain auth key, json return: %s" % data)
            sys.exit(1)
            #should probably print a meaningful error FIXME
            return None

    def refresh_token(self):
        """Get a new auth token using cliendid and clientsecret"""
        self._authid = self.__api_get_auth_key(self._endpoint, self._clientid, self._clientsecret)
        self.session.headers.update({"Authorization": self._authid})
    def export_vcf(self, dp_id, output_file="temp.vcf"):
        print dp_id
        url = "%s/export/%s" % (self.endpoint, urllib.quote_plus(dp_id))
        logger.info("Export url: %s" % url)
        params = {}
        self.refresh_token()
        params['access_token']= self._authid
        r = self.session.get(url, params=params, stream=True,headers={"Authorization":self._authid})
        logger.info("Export status code: %s" % r.status_code)
        return_data = ""
        with open(output_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    return_data += chunk
                    f.flush()
        if return_data.find("unpaid") > -1:
            return None
        return output_file
    def submit_one_zipfile(self, zip_file_path, extra_api_params={}):
        """
        Uploads a data package directory using authid,
        and returns the URI to the data package
        FIXME: check authid validity and refresh if necessary
        """
        global logger
        logger.debug("Package archive: %s" % (zip_file_path))
        files = {'file':open(zip_file_path, 'rb')}
        url = "%sdatapackages/?useJavaPipeline=true" % (self.endpoint)
        params = extra_api_params
        params['access_token']= self._authid
        headers = dict()
        headers['Authorization']=self._authid
        logger.debug("Start POSTing package to %s" % (url))
        # my_config = {'verbose' : sys.stderr}
        # "config" kwarg has been disabled for new requests
        s = self.session
        r = s.post(url, files=files, data=params,headers=headers)
        logger.debug("post url: %s headers: %s" % (r.url, headers))
        logger.debug("Post Result: %s"% r.status_code)
        if r.status_code != 201 and r.status_code!=200:
            for x in range(10):
                time.sleep(.5)
                r = s.post(url, files=files, data=params)
                logger.debug("Post Result: %s"% r.status_code)
                if r.status_code == 201 or r.status_code == 200:
                    break;
        if r.status_code !=201 and r.status_code !=200:
            logger.critical("Unable to get post file after 10 tries, last status_code: %s" % r.status_code)
            return (None, r.text) 
        data = r.json()
        logger.debug("Finished POSTing package to %s" % (url))
        logger.debug("Json Package submission return:%s" % (json.dumps(r.json(), sort_keys = True, indent=2)))
        resource_uri = data['status-url']
        return (resource_uri, None)

    def get_package_status(self, package_uri, extra_api_params={}):
        """ Thin wrapper for the REST call to retrieve status object
        FIXME: check authid validity and refresh if necessary
        FIXME: check HTTP return codes
        """
        params = {}
        self.refresh_token()
#alternate ways to get the package status if your ssl version is causing problems

        url = "".join([package_uri, "?", "authid=%s" % self._authid])
#WGET SEEMS TO WORK 100% OF TIME REGARDLESS OF OPENSSL CONFIG/VERSION #######
#     cmd = ["wget", "--no-check-certificate", "-O - ", "--secure-protocol=TLSv1", url]
#### CURL IS PROBLEMATIC MORE OFTEN ANECDOTALLY####
#       curl_params='-d "authid=%s" ' % self._authid
#       cmd = ["curl", curl_params, package_uri]
#       output = subprocess.Popen(" ".join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
#       result = output.communicate()[0]
#       logger.debug("Curl/Wget return code: %s" % curl.returncode)
#       logger.debug("Json package status return:\n%s"% (json.dumps(result, sort_keys=True, indent=2)))
#        logger.debug(" ".join(cmd))
        try:
            logger.debug("status url: %s" % url)
            result = self.session.get(url)
        except requests.ConnectionError as e:
            logger.error("connection error on status get: %s" % e)
            sys.exit(1)
        return result.json()
       
    def configure_logging(self,level):
        global logger, logger_results 
        log_format_details = '%s(asctime)-15s %(name)-5s %(levelname)-8s %(message)s'
        log_format_summary = '%(asctime)-15s   %(levelname)-8s    %(message)s'
        logger = logging.getLogger('datastream')
        logger.setLevel(level)

        logger_results = logging.getLogger('datastream.results')
        logger_results.setLevel(level)
        
        ch=logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter(log_format_summary)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        datetimestamp = str(datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S"))
        if(level == "DEBUG"):
            filelog = logging.FileHandler('details=%s.log' % (datetimestamp))
            formatter = logging.Formatter(log_format_details)
            filelog.setLevel(logging.DEBUG)
            logger.addHandler(filelog)
            filelog = logging.FileHandler('summary-%s.log' % (datetimestamp))
            formatter = logging.Formatter(log_format_summary)
            filelog.setFormatter(formatter)
            logger_results.addHandler(filelog)

