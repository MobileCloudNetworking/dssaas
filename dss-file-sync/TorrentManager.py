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
from Config import *
import time
import threading

def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper


class TorrentManager():
    def __init__(self, file_manager, session_manager, tracker_manager):
        self.conf = Config()
        self.log = logging.getLogger(self.conf.get('log', 'name'))
        self.fm = file_manager
        self.sm = session_manager
        self.tm = tracker_manager
        self.path = self.conf.get('main', 'path')
        self.torrent_list = self.fm.list_files('.', ['.torrent'])[1]
        self.removed_torrents_timeout = int(self.conf.get('main', 'removed_torrents_timeout'))

    @threaded
    def check_files_status(self):
        self.log.debug("Starting File Monitoring Thread")
        while True:
            result, file_list = self.fm.new_file_exists(self.path, ['.webm'])
            if result:
                self.log.debug("New files detected: " + str(file_list))
                for file_name in file_list:
                    self.log.debug("Generating torrent file for: " + str(file_name))
                    self.create_torrent(file_name, file_name.split('.')[0] + '.torrent')
                    self.add_torrent_to_session(file_name.split('.')[0] + '.torrent', 'check_new_files')
            time.sleep(1)
            removed_, removed_file_list = self.fm.removed_file_exists(self.path, ['.webm'])
            if removed_:
                self.log.debug("Removed files detected: " + str(removed_file_list))
                for file_name in removed_file_list:
                    self.log.debug("Deleting torrent file of : " + str(file_name))
                    self.delete_torrent(file_name.split('.')[0] + '.torrent')
            time.sleep(1)
        self.log.debug("Exiting File Monitoring Thread")\

    @threaded
    def cleanup_deleted_files(self):
        self.log.debug("Starting Deleted Files Monitoring Thread")
        while True:
            removed_torrent_list = self.fm.list_files(self.path, ['.removed'])[1]
            for removed_file in removed_torrent_list:
                current_time = int(time.time())
                file_removed_at = int(removed_file.split('.')[1])
                self.log.debug("File " + removed_file + " is " + str(current_time - file_removed_at) + " seconds old.")
                if (current_time - file_removed_at) >= self.removed_torrents_timeout:
                    self.fm.remove_file(self.path, removed_file)
            self.log.debug("Performed clean up")
            time.sleep(60)
        self.log.debug("Exiting Deleted Files Monitoring Thread")

    def add_torrent_to_session(self, torrent_name, called_from):
        if called_from == 'check_new_files' or called_from == 'save_torrent':
            self.sm.add_torrent(torrent_name)
        elif called_from == 'recreate_all_torrents':
            added = False
            while not added:
                time.sleep(5)
                added = self.sm.add_torrent(torrent_name)

    def create_torrent(self, filename, torrentname, comment='test', path=None):
        if path is None:
            path = self.path
        #Create torrent
        fs = lt.file_storage()
        lt.add_files(fs, path + filename)
        t = lt.create_torrent(fs)
        for tracker in self.tm.tracker_list:
            t.add_tracker(tracker['url'], 0)
        t.set_creator('libtorrent %s' % lt.version)
        t.set_comment(comment)
        lt.set_piece_hashes(t, path)
        torrent = t.generate()
        #let's move this to fm class
        self.fm.create_file(path, torrentname, lt.bencode(torrent))
        #f = open(path + torrentname, "wb")
        #f.write(lt.bencode(torrent))
        #f.close()

    def get_torrent_list(self): #latest, files in HD
        self.torrent_list = self.fm.list_files(self.path, ['.torrent'])[1]
        return self.torrent_list

    def get_removed_torrent_list(self): #latest, files in HD
        self.removed_torrent_list = self.fm.list_files(self.path, ['.removed'])[1]
        return self.removed_torrent_list

    def get_torrent_content(self, torrent_name):
        #retrieve the content and encode base64
        encoded_string = base64.b64encode(self.fm.read_file(self.path,torrent_name))
        #self.log.debug(str(encoded_string))
        return encoded_string

    #self.tm.recreate_all_torrents()
    def recreate_all_torrents(self):
        for filename in self.fm.list_files(self.path, ['.webm'])[1]:
            #first remove from session, and from fs, then recreate and add to session
            self.sm.remove_torrent(filename.split('.')[0] + '.torrent')
            self.fm.remove_file(self.path, filename.split('.')[0] + '.torrent')
            self.create_torrent(filename, filename.split('.')[0] + '.torrent')
            self.add_torrent_to_session(filename.split('.')[0] + '.torrent', 'recreate_all_torrents')

    #self.tm.save_torrent(torrent_name,torrent_content)
    def save_torrent(self, torrent_name, torrent_content):
        if (torrent_name not in self.get_torrent_list()):
            self.fm.create_file(self.path, torrent_name, base64.b64decode(torrent_content))
            self.add_torrent_to_session(torrent_name, 'save_torrent')
            #now I might add it to the session to start downloading

    def already_removed(self, torrent_name):
        for filename in self.fm.list_files(self.path, ['.removed'])[1]:
            decoupled_name = filename.split('.')
            if torrent_name == decoupled_name[0] + '.torrent':
                return True
        return False

    def delete_torrent(self, torrent_name):
        self.log.debug("Trying to delete: " + torrent_name)
        if not self.already_removed(torrent_name):
            self.sm.remove_torrent(torrent_name)
            self.fm.rename_file(self.path, torrent_name, torrent_name.split('.')[0] + '.' + str(int(time.time())) + '.removed')
            self.fm.remove_file(self.path, torrent_name.split('.')[0] + '.webm')
        else:
            self.log.debug("File " + torrent_name + " is already deleted")

