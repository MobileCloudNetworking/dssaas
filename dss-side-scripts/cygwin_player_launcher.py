import os
import time
import sys

total = len(sys.argv)
if (total < 2):
    print ("Usage: python cygwin_player_launcher.py <ICN_ENDPOINT> [MACHINE_USERNAME default: ccnx] [PLAYER_ID default: 1]")
    sys.exit(1)

icn_endpoint = ""
try:
    icn_endpoint = sys.argv[1]# Param 1
    print "ICN endpoint set to: " + icn_endpoint
except:
    print "ICN endpoint is mandatory."
    sys.exit(1)

username = ""
try:
    username = sys.argv[2]# Param 2
    print "Username set to: " + username
except:
    username = "ccnx"
    print "Username set to: " + username

home_dir = '/home/' + username
http_dir = '/var/www/'

dss_cms_dashboard_domain = "dashboard.dssaas.mcn.com"
dss_cms_port = "8080"
dss_cms_display_domain = "cms.dssaas.mcn.com"

dss_player_id = ""
try:
    dss_player_id = sys.argv[3]# Param 3
    print "Player id set to: " + dss_player_id
except:
    dss_player_id = "1"
    print "Player id set to: " + dss_player_id

path_to_chrome_exe = home_dir + "/GoogleChrome/Chrome.exe"

# Preparing simple webserver to serve ICN downloaded files on localhost
print "Running command: rm -rf " + http_dir
ret_code = os.system('rm -rf /var/www/')
print "return code: " + str(ret_code)

print "Running command: mkdir " + http_dir
ret_code = os.system('mkdir /var/www/')
print "return code: " + str(ret_code)

print "Changing directory to " + http_dir
os.chdir(http_dir)

print "Running command: echo \"<h1>It works!</h1>\" > index.html"
ret_code = os.system('echo "<h1>It works!</h1>" > index.html')
print "return code: " + str(ret_code)

print "Running command: python -m SimpleHTTPServer 80 &> /dev/null &"
ret_code = os.system('python -m SimpleHTTPServer 80 &> /dev/null &')
print "return code: " + str(ret_code)

print "Changing directory to " + home_dir
os.chdir(home_dir)
# Webserver preparation done

# Running service CCNX
print "Running command: " + home_dir + "/ccnxdir/bin/ccndstart &> /dev/null &"
ret_code = os.system(home_dir + '/ccnxdir/bin/ccndstart &> /dev/null &')
print "return code: " + str(ret_code)
# Service CCNX ready

# Give CCNX some time to start
time.sleep(3)

# Run get content python script
print "Running command: python " + home_dir + "/icn_getcontents.py http://" + dss_cms_dashboard_domain + ":" + dss_cms_port + "/WebAppDSS/display/listContents?id=" + dss_player_id + " " + icn_endpoint + " " + username + " &> /dev/null &"
ret_code = os.system("python " + home_dir + "/icn_getcontents.py http://" + dss_cms_dashboard_domain + ":" + dss_cms_port + "/WebAppDSS/display/listContents?id=" + dss_player_id + " " + icn_endpoint + " " + username + " &> /dev/null &")
print "return code: " + str(ret_code)
# get content script is running

# Open chrome and display the data
print "Running command: " + path_to_chrome_exe + " --kiosk http://" + dss_cms_display_domain + "/WebAppDSS/display/playAll?id=" + dss_player_id + " &> /dev/null &"
ret_code = os.system(path_to_chrome_exe + " --kiosk http://" + dss_cms_display_domain + "/WebAppDSS/display/playAll?id=" + dss_player_id + " &> /dev/null &")
print "return code: " + str(ret_code)
# Data is being displayed

# Happy days