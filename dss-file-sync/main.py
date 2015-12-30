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
import signal
import sys
import time


def main_func():
    conf = Config()
    logger = Log.config_logger(conf.get('log', 'name'))
    logger.debug('main message')
    path = conf.get('main', 'path')

    #init
    file_manager = FileManager()
    tracker_manager = TrackerManager()
    session_manager = SessionManager()
    torrent_manager = TorrentManager(file_manager, session_manager, tracker_manager)
    broadcast_manager = BroadcastManager(file_manager, torrent_manager, tracker_manager)

    def clean_up(signal, frame):
        print "Exiting threads gracefully ...\n"
        broadcast_manager.terminated = True
        torrent_manager.terminated = True
        tracker_manager.terminated = True
        print "Bye.\n"
        sys.exit()

    #running threads
    #broadcast_manager.sendAmazon_broadcast_message()
    broadcast_manager.send_broadcast_message()
    broadcast_manager.receive_broadcast_message()
    broadcast_manager.remove_expired_streams()
    tracker_manager.expire_tracker()
    torrent_manager.check_files_status()
    torrent_manager.cleanup_deleted_files()

    signal.signal(signal.SIGINT, clean_up)

    for i in range(1, 5000):
        #print "Sleeping...\n"
        time.sleep(1)
        for torrent_file in file_manager.list_files(path, ['.torrent'])[1]:
            session_manager.get_torrent_stat_str(torrent_file.split('.')[0] + '.webm')

if __name__ == "__main__":
    main_func()