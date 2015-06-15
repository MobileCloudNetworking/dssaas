# A piece of code to get the list of registered services on keystone
# Execution example: python listAllRegisteredEPs.py <USERNAME> <PASSWORD> <TENANT_NAME> <AUTH_URL> <SERVICE_ID>


__author__ = 'Mohammad'

import sys
import getopt

from keystoneclient.v2_0 import client

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"he:u:p:t:a:",["endpoint_id=","username=","password=","tenant_name=","auth_url="])
    except getopt.GetoptError:
        print 'Usage: python listAllRegisteredEPs.py -e <ENDPOINT_ID> -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL]'
        exit(0)

    user_name = None
    passwd = None
    tenant_name = None
    auth_url = None
    e_id = None

    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: python listAllRegisteredEPs.py -e <ENDPOINT_ID> -u [USERNAME] -p [PASSWORD] -t [TENANT_NAME] -a [AUTH_URL]'
            exit(0)
        elif opt in ("-u", "--username"):
            user_name = arg
        elif opt in ("-p", "--password"):
            passwd = arg
        elif opt in ("-t", "--tenant_name"):
            tenant_name = arg
        elif opt in ("-a", "--auth_url"):
            auth_url = arg
        elif opt in ("-e", "--endpoint_id"):
            e_id = arg

    if user_name is None:
        user_name = 'dummy'

    if passwd is None:
        passwd = 'dummy'

    if tenant_name is None:
        tenant_name = 'dummy'

    if auth_url is None:
        auth_url = 'http://dummy:5000/v2.0'

    if e_id is None:
        print 'Endpoint ID is mandatory!'
        exit(0)

    keystone = client.Client(username=user_name, password=passwd, tenant_name=tenant_name, auth_url=auth_url)

    ep_list = keystone.endpoints.list()

    for item in ep_list:
        if item._info['id'] == e_id:
            res = keystone.endpoints.delete(e_id)
            print res.__repr__()
            return 1

    print "EP not found."

if __name__ == "__main__":
    main(sys.argv[1:])
