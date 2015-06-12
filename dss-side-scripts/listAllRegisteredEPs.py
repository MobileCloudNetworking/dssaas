# A piece of code to get the list of registered services on keystone
# Execution example: python listAllRegisteredEPs.py <USERNAME> <PASSWORD> <TENANT_NAME> <AUTH_URL> <SERVICE_ID>

__author__ = 'Mohammad'

import sys
from keystoneclient.v2_0 import client

if len(sys.argv) > 1 and sys.argv[1] == '-h':
	print 'Usage: python listAllRegisteredEPs.py [USERNAME] [PASSWORD] [TENANT_NAME] [AUTH_URL] [SERVICE_ID]'
	exit(0)

try:
	user_name = sys.argv[1]
except:
	user_name = 'dummy'

try:
	passwd = sys.argv[2]
except:
	passwd = 'dummy'

try:
	tenant_Name = sys.argv[3]
except:
	tenant_Name = 'dummy'

try:
	auth_Url = sys.argv[4]
except:
	auth_Url = 'http://dummy:5000/v2.0'

try:
	s_id = sys.argv[5]
except:
	s_id = None

keystone = client.Client(username=user_name, password=passwd, tenant_name=tenant_Name, auth_url=auth_Url)

ep_list = keystone.endpoints.list()

if s_id is None:
	for item in ep_list:
		print "Service ID: \"" + item._info['service_id'] + "\" Region: \"" + item._info['region'] + "\" Public URL: \"" + item._info['publicurl'] + "\"\n"
else:
    for item in ep_list:
        if item._info['service_id'] == s_id:
            print "Service ID: \"" + item._info['service_id'] + "\" Region: \"" + item._info['region'] + "\" Public URL: \"" + item._info['publicurl'] + "\"\n"

exit(1)
