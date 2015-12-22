""" Config.py: Simple Config file reader. """

__author__ = "Santiago Ruiz"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

import ConfigParser

class Config:
    #init
    def __init__(self, uri):
        self.uri = uri
        self.conf = ConfigParser.ConfigParser()
        try:
            self.conf.read(self.uri)
        except:
            print "Error reading conf file"

    #get config param
    def get(self, section, name):
        try:
            return self.conf.get(section, name)
        except:
            print "Error getting atribute"
            return None

    #get section list
    def get_sections(self):
        try:
            return self.conf.sections()
        except:
            print "Error reading sections"
            return None
