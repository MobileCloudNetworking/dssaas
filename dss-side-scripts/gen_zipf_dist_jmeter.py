import numpy as np
import os
from subprocess import call

maxfilename = 200
maxnumfiles = 200 # num files tbc
param = 1.1
s = np.random.zipf(param, maxnumfiles*3)

call(["touch", "filenames.txt"])
f = open('filenames.txt', 'w')
created = 0
i=0
while created < maxnumfiles:
        if (int(s[i])<=maxfilename):
                f.write(str(s[i])+"\n")
                created = created + 1
                if (i % 10 == 0):
                        print "Working: " +str(int((float(created)/float(maxnumfiles))*100.0)) + "% completed"
        i = i + 1
print "done"
f.close()