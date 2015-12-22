__author__ = "Santiago Ruiz", "Mohammad Valipoor"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz", "Mohammad Valipoor"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz", "Mohammad Valipoor"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

import Log
import BroadcastManager
import FileManager
import Config
import SessionManager
import TorrentManager
import TrackerManager

if __name__ == "__main__":
    logger = Log.setup_custom_logger(Config.get('log', 'name'))
    logger.debug('main message')

    file_manager = FileManager()
    tracker_manager = TrackerManager()
    session_manager = SessionManager()
    torrent_manager = TorrentManager(file_manager, session_manager, tracker_manager)
    broadcast_manager = BroadcastManager(file_manager, torrent_manager)

