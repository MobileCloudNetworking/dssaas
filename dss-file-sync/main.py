__author__ = "Santiago Ruiz", "Mohammad Valipoor"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz", "Mohammad Valipoor"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz", "Mohammad Valipoor"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

import Log 
from BroadcastManager import *
from FileManager import *
from Config import *
from SessionManager import *
from TorrentManager import *
from TrackerManager import *
import time

if __name__ == "__main__":
    conf = Config()
    logger = Log.config_logger(conf.get('log', 'name'))
    logger.debug('main message')

    #init
    file_manager = FileManager()
    tracker_manager = TrackerManager()
    session_manager = SessionManager()
    torrent_manager = TorrentManager(file_manager, session_manager, tracker_manager)
    broadcast_manager = BroadcastManager(file_manager, torrent_manager, tracker_manager)

    #running threads
    broadcast_manager.sendAmazon_broadcast_message()
    broadcast_manager.receive_broadcast_message()
    tracker_manager.expire_tracker()
    torrent_manager.check_new_files()

    for i in range(1,5000):
	#print "Sleeping...\n"
	time.sleep(1)
	for torrent_file in file_manager.list_files('./',['.torrent'])[1]:
	    session_manager.get_torrent_stat_str(torrent_file.split('.')[0]+'.webm')
