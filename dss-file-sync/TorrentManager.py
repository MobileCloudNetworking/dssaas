__author__ = "Santiago Ruiz", "Mohammad Valipoor"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz", "Mohammad Valipoor"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz", "Mohammad Valipoor"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

import libtorrent as lt
import base64
import logging
import Config
import time
import threading

class TorrentManager(threading.Thread):
    def __init__(self, file_manager, session_manager, tracker_manager):
        threading.Thread.__init__(self)
        self.log = logging.getLogger(Config.get('log', 'name'))
        self.fm = file_manager
        self.sm = session_manager
        self.tm = tracker_manager
        self.path = Config.get('main', 'path')
        self.torrent_list = self.fm.list_files('.', ['.torrent'])[1]

    def run(self):
        self.log.debug("Starting File Monitoring Thread")
        while 1:
            result, file_list = self.fm.new_file_exists(self.path,['.webm'])
            if result:
                self.log.debug("New files detected: " + str(file_list))
                for file_name in file_list:
                    self.log.debug("Generating torrent file for: " + str(file_name))
                    self.create_torrent(file_name, file_name.split('.')[0] + '.torrent')
                    # TODO: Remove torrrents from session and add new torrents to session
            time.sleep(1)
        self.log.debug("Exiting File Monitoring Thread")

    def handle_broadcast_torrent_reception(self):
        # TODO: Remove torrrents from session and add new torrents to session
        pass

    def create_torrent(self, filename, torrentname, comment='test', path=None):
        if path is None:
            path = self.path
        #Create torrent
        fs = lt.file_storage()
        lt.add_files(fs, path + filename)
        t = lt.create_torrent(fs)
        for tracker in self.tm.tracker_list:
            t.add_tracker(tracker, 0)
        t.set_creator('libtorrent %s' % lt.version)
        t.set_comment(comment)
        lt.set_piece_hashes(t, path)
        torrent = t.generate()
        f = open(path + torrentname, "wb")
        f.write(lt.bencode(torrent))
        f.close()

    def get_torrent_list(self): #latest, files in HD
        self.torrent_list = self.fm.list_files(self.path, ['.torrent'])[1]
        return self.torrent_list

    def get_torrent_content(self, torrent_name):
        #retrieve the content and encode base64
        encoded_string = ''
        with open(torrent_name, "rb") as torrent_file:
            encoded_string = base64.b64encode(torrent_file.read())
        self.log.debug(str(encoded_string))
        return encoded_string
