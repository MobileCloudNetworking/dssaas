__author__ = 'Santi'

import Log
import BroadcastManager
import FileManager
import Config
import SessionManager
import TorrentManager
import TrackerManager

if __name__ == "__main__":
    logger = Log.setup_custom_logger('mylog')
    logger.debug('main message')

    file_manager = FileManager()
    tracker_manager = TrackerManager()
    session_manager = SessionManager()
    torrent_manager = TorrentManager(file_manager, session_manager, tracker_manager)
    broadcast_manager = BroadcastManager(file_manager, torrent_manager)

