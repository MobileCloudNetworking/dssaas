__author__ = 'Santiago Ruiz'
__copyright__ = "Copyright 2014, SoftTelecom"

import getopt
import pycurl
import cStringIO
from subprocess import call
import sys
import time
import logging

def config_logger(log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    hdlr = logging.FileHandler('aaa_apache_log.txt')
    formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger

LOG = config_logger()

def perform_check(timeout):
        curl = pycurl.Curl()
        buff = cStringIO.StringIO()
        curl.setopt(pycurl.URL, 'http://aaa-openam-instance.mcn.com:8080/openam')
        curl.setopt(pycurl.WRITEFUNCTION, buff.write)
        curl.setopt(pycurl.CONNECTTIMEOUT, timeout)
        curl.setopt(pycurl.TIMEOUT, timeout)
        try:
                curl.perform()
                retcode =  curl.getinfo(pycurl.HTTP_CODE)
                LOG.debug("status code: %s" + str(retcode))
        except:
                LOG.debug("Exception in performing curl call")
                retcode = -1
        curl.close()
        return int(retcode)

def main(argv):
        try:
                opts, args = getopt.getopt(argv,"ht:r:",["time=","retry="])
        except getopt.GetoptError:
                print ("Usage: python icn_dss_dns_load_test.py -t timeout -r num_retries")
                sys.exit(0)

        ctime = None
        retries = None

        for opt, arg in opts:
                if opt == '-h':
                        print ("Usage: python icn_dss_dns_load_test.py -t timeout -r num_retries")
                        sys.exit(0)
                elif opt in ("-t", "--time"):
                        ctime = int(arg)
                elif opt in ("-r", "--retry"):
                        retries = int(arg)

        if ctime is None:
                LOG.debug('Default timeout is set to 10')
                ctime = 10

        if retries is None:
                LOG.debug('Default retries are set to 50')
                retries = 50

        for i in range(retries):
                res = perform_check(ctime)
                if(res > 200) and (res < 400):
                        call (["service", "apache2", "restart"])
                        sys.exit (0)
                time.sleep(1)

if __name__ == "__main__":
    main(sys.argv[1:])