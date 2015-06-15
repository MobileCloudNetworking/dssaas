# A piece of code to get the list of registered services on keystone
# Execution example: python listAllRegisteredServices.py -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL] -s [SERVICE_ID]


__author__ = 'Mohammad'

import sys
import getopt

from keystoneclient.v2_0 import client

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hu:p:t:a:s:",["username=","password=","tenant_name=","auth_url=","service_id="])
    except getopt.GetoptError:
        print 'Usage: python listAllRegisteredServices.py -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL] -s [SERVICE_ID]'
        exit(0)

    user_name = None
    passwd = None
    tenant_name = None
    auth_url = None
    s_id = None

    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: python listAllRegisteredServices.py -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL] -s [SERVICE_ID]'
            exit(0)
        elif opt in ("-u", "--username"):
            user_name = arg
        elif opt in ("-p", "--password"):
            passwd = arg
        elif opt in ("-t", "--tenant_name"):
            tenant_name = arg
        elif opt in ("-a", "--auth_url"):
            auth_url = arg
        elif opt in ("-s", "--service_id"):
            s_id = arg

    if user_name is None:
        user_name = 'dummy'

    if passwd is None:
        passwd = 'dummy'

    if tenant_name is None:
        tenant_name = 'dummy'

    if auth_url is None:
        auth_url = 'http://dummy:5000/v2.0'

    if s_id is None:
        s_id = None

    keystone = client.Client(username=user_name, password=passwd, tenant_name=tenant_name, auth_url=auth_url)

    service_list = keystone.services.list()

    if s_id is None:
        for item in service_list:
            print "Service ID: \"" + item._info['id'] + "\" Description: \"" + item._info['description'] + "\" Type: \"" + item._info['type'] + "\"\n"
    else:
        for item in service_list:
            if item._info['id'] == s_id:
                print "Service ID: \"" + item._info['id'] + "\" Description: \"" + item._info['description'] + "\" Type: \"" + item._info['type'] + "\"\n"

if __name__ == "__main__":
    main(sys.argv[1:])
