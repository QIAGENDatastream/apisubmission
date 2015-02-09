#/!/usr/bin/env python

import requests, sys, os, logging, datetime, time, json, urllib, re
import ssl
ssl.OP_NO_TLSv1_2=True
ssl.op_NO_TLSv1_1=True
####mods to force tls1#####
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ftplib, getpass
ftplib.FTP_TLS.ssl_version=ssl.PROTOCOL_TLSv1

class tlsHttpAdapter(HTTPAdapter):
    """"Transport adapter" that allows us to force use of TLSv1."""

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)
#####end ssl mod####


class DataStreamAPI(object):
    """Root Datastream API class that gives export, status, auth token generation, and zip submission
       Instantiate with a server such as https://api.ingenuity.com along with OAuth ID/Secret access tokens to utilize """
    def __init__(self, server, clientid, clientsecret, log_level="INFO", ftp_dir=None, ftp_server="ftp2.ingenuity.com"):
        self.server = server
        if self.server:
            #if we just want to use FTP, don't do this
            self._endpoint = server + "/datastream/api/v1/"
            self.session = requests.Session()
            self.logger.info("Server is %s" % self.server)
            self.logger.info("Using %s as endpoint" % self.endpoint)
            self.session.mount(self._endpoint, tlsHttpAdapter())
        self._clientid = clientid
        self._clientsecret = clientsecret
        self._authid = None
        self.ftp_server = ftp_server
        self.ftp_dir = ftp_dir
        self.user_name = None
        self.passwd= None
        self.ftp_conn = None
        self.logger = self.configure_logging(log_level)
        if(self.ftp_dir):
            self.logger.info("FTP server is: %s, dir is: %s" % (self.ftp_server, self.ftp_dir))

    def connect_to_ftp(self):
        if not self.user_name:
            self.user_name = raw_input("Enter your Ingenuity/FTP username:")
        if not self.passwd:
            self.passwd = getpass.getpass("Enter password for %s:" % self.user_name)
        ftps = ftplib.FTP_TLS(self.ftp_server, self.user_name, self.passwd)
        ftps.prot_p()
        self.logger.info("Connected to FTP...changing dir to %s" % self.ftp_dir)
        ftps.cwd(self.ftp_dir)
        return ftps

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
        self.logger.debug("Auth key url:%s" % (url))
        r = self.session.get(url)
        self.logger.debug("request status: %s" % (r.status_code))
        if r.status_code != 200:
            for x in range(10):
                time.sleep(1)
                r = requests.get(url)
                if r.status_code == 200:
                    break;
        if r.status_code !=200:
            self.logger.critical("Unable to get auth key after 10 tries, last status_code: %s" % r.status_code)
            sys.exit(1)
        data = r.json()
        self.logger.debug("json return from auth key url: %s" % (data))
        if "access_token" in data:
            return data['access_token']
        else:
            self.logger.critical("Unable to obtain auth key, json return: %s" % data)
            sys.exit(1)
            #should probably print a meaningful error FIXME
            return None

    def refresh_token(self):
        """Get a new auth token using cliendid and clientsecret"""
        self._authid = self.__api_get_auth_key(self._endpoint, self._clientid, self._clientsecret)
        self.session.headers.update({"Authorization": self._authid})
    def export_vcf(self, dp_id, output_file="temp.vcf"):
        url = "%s/v1/export/%s" % (self.server, urllib.quote_plus(dp_id))
        self.logger.debug("Export url: %s" % url)
        params = {}
        params['access_token']= self._authid
        r = self.session.get(url, params=params, stream=True)
        self.logger.debug("Export status code: %s" % r.status_code)
        return_data = ""
        self.logger.info("Writing VCF out to %s" % output_file)
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
        self.logger.debug("Package archive: %s" % (zip_file_path))
        files = {'file':open(zip_file_path, 'rb')}
        url = "%sdatapackages/" % (self.endpoint)
        params = extra_api_params
        params['access_token']= self._authid
        self.logger.debug("Params: %s" % params)
        headers = dict()
        headers['Authorization']=self._authid
        self.logger.info("Start POSTing package to %s" % (url))
        # my_config = {'verbose' : sys.stderr}
        # "config" kwarg has been disabled for new requests
        s = self.session
        r = s.post(url, files=files, data=params,headers=headers)
        self.logger.debug("post url: %s headers: %s" % (r.url, headers))
        self.logger.debug("Post Result: %s"% r.status_code)
        if r.status_code != 201 and r.status_code!=200:
            self.logger.debug(r.text);
            for x in range(10):
                time.sleep(.5)
                r = s.post(url, files=files, data=params, headers=headers)
                self.logger.debug("Post Result: %s"% r.status_code)
                if r.status_code == 201 or r.status_code == 200:
                    break;
        if r.status_code !=201 and r.status_code !=200:
            self.logger.critical("Unable to get post file after 10 tries, last status_code: %s" % r.status_code)
            return (None, r.text) 
        try:
            data = r.json()
        except:
            self.logger.critical("Return data from post is not Json:")
            self.logger.critical(r.text)
            sys.exit(1)

        self.logger.debug("Finished POSTing package to %s" % (url))
        #self.logger.debug("Json Package submission return:%s" % (json.dumps(r.json(), sort_keys = True, indent=2)))
        resource_uri = data['status-url']
        return (resource_uri, None)

    def ftp_upload(self, file):
        if self.ftp_conn:
            try:
                self.ftp_conn.voidcmd("NOOP")
            except:
                self.ftp_conn = self.connect_to_ftp()
        else:
            self.ftp_conn = self.connect_to_ftp()
        fh = open(file, "rb")
        try:
            self.logger.info("Uploading %s" % file)
            self.ftp_conn.storbinary("STOR %s" % os.path.basename(file), fh)
        except Exception, e:
            self.logger.critical("Error executing STOR command on %s: %s" % (file, e))
            sys.exit(1)
        return 1

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
#       self.logger.debug("Curl/Wget return code: %s" % curl.returncode)
#       self.logger.debug("Json package status return:\n%s"% (json.dumps(result, sort_keys=True, indent=2)))
#        self.logger.debug(" ".join(cmd))
        try:
            self.logger.debug("status url: %s" % url)
            result = self.session.get(url)
        except requests.ConnectionError as e:
            self.logger.error("connection error on status get: %s" % e)
            sys.exit(1)
        return result.json()
       
    def configure_logging(self,level):
        """ Configure log4j style logging module
        FIXME: fix the levels to be settable to more than INFO and DEBUG"""
        if level == "DEBUG":
            level = logging.DEBUG
        else:
            level = logging.INFO
        log_format_details = '%s(asctime)-15s %(name)-5s %(levelname)-8s %(message)s'
        log_format_summary = '%(asctime)-15s   %(levelname)-8s    %(message)s'
        logger = logging.getLogger('datastream')
        logger.setLevel(level)
       
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
        return logger 
