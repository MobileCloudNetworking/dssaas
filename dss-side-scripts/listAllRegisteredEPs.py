# A piece of code to get the list of registered services on keystone
# Execution example: python listAllRegisteredEPs.py -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL] -s [SERVICE_ID]


__author__ = 'Mohammad'

import sys
import getopt

from keystoneclient.v2_0 import client

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hu:p:t:a:s:",["username=","password=","tenant_name=","auth_url=","service_id="])
    except getopt.GetoptError:
        print 'Usage: python listAllRegisteredEPs.py -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL] -s [SERVICE_ID]'
        exit(0)

    user_name = None
    passwd = None
    tenant_name = None
    auth_url = None
    s_id = None

    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: python listAllRegisteredEPs.py -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL] -s [SERVICE_ID]'
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

    ep_list = keystone.endpoints.list()

    if s_id is None:
        for item in ep_list:
            print "Service ID: \"" + item._info['service_id'] + "\" Region: \"" + item._info['region'] + "\" Public URL: \"" + item._info['publicurl'] + "\" Endpoint ID: \"" + item._info['id'] + "\"\n"
        return 1
    else:
        for item in ep_list:
            if item._info['service_id'] == s_id:
                print "Service ID: \"" + item._info['service_id'] + "\" Region: \"" + item._info['region'] + "\" Public URL: \"" + item._info['publicurl'] + "\" Endpoint ID: \"" + item._info['id'] + "\"\n"
                return 1
    print "Endpoint not found."
    return 0

if __name__ == "__main__":
    main(sys.argv[1:])
