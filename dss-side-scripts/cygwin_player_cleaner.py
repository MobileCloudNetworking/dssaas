import os
import time
import sys

username = "ccnx"

home_dir = '/home/' + username

# Stopping service CCNX
print "Running command: " + home_dir + "/ccnxdir/bin/ccndstop &> /dev/null &"
ret_code = os.system(home_dir + '/ccnxdir/bin/ccndstop &> /dev/null &')
print "return code: " + str(ret_code)
# Service CCNX stopped

# Give CCNX some time to die
time.sleep(1)

# Kill all python
print "Running command: killall python"
ret_code = os.system('killall python')
# All python killed

# You died too :-p