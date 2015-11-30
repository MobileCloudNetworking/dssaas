import numpy as np
from subprocess import call
import os

shape, scale = 7.5, 2. # mean and dispersion
totalsize = 3000000 # 3GB
s = np.random.gamma(shape, scale, 5000)


size = 0
i = 0
call(["rm", "-r", "./data"])
call(["mkdir", "data"])
while size < totalsize:
        os.system("dd if=/dev/zero bs=" + str(int(s[i]*1024*1024)) + " count=1 of=data/" + str(i) + ".webm")
        size += int(s[i]*1024)
        i = i+1
        if (i % 10 == 0):
                print "Working: " +str(int((float(size)/float(totalsize))*100.0)) + "% completed"
print "done"