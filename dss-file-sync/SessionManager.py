__author__ = "Santiago Ruiz", "Mohammad Valipoor"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz", "Mohammad Valipoor"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz", "Mohammad Valipoor"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

import libtorrent as lt
import logging
from Config import *

class SessionManager:

    def __init__(self):
        self.session = None
        self.torrent_handle_list = []
	conf = Config()
        self.log=logging.getLogger(conf.get('log', 'name'))
	self.start_session()

    def start_session(self):
        self.session = lt.session()
        self.session.listen_on(6881, 6891)

    # Keeps one session_proxy to the session when destructing it.
    # The destructor will not block, but start to close down the session,
    # The destructor of the proxy will then synchronize the threads
    def stop_session(self):
        proxy = self.session.abort()
        return proxy

    # Gets a torrent name and returns the handler of that torrent
    def find_torrent(self, file_name):
        for item in self.torrent_handle_list:
            if item.name() == file_name:
                return item
        return None

    # Not available ATM
    def update_torrents(self, torrent_list):
        pass

    # Gets a torrent name and adds it to the session and the torrent_handle_list
    def add_torrent(self, torrent_name):
        try:
	    self.log.debug("Adding torrent " + torrent_name + " to BitTorrent session")
            handler = self.session.add_torrent({'ti': lt.torrent_info(torrent_name), 'save_path': '.', 'seed_mode': True, 'auto_managed': True})
            self.log.debug('Torrent handler created: '+ str(handler.name()) )
            self.torrent_handle_list.append(handler)
	    self.log.debug('Torrent handler list is: ' + str(self.torrent_handle_list))
            return True
        except:
	    self.log.debug("Adding torrent " + torrent_name + " to BitTorrent FAILED!")
            return False

    # Gets a torrent name and removes it from the session and the torrent_handle_list
    # Remember: It's not happening immediately and you can not add the same torrent while one is deleting
    # Therefore, add_torrent is written in a way that returns False in case of exception.
    # In case you are deleting and adding the same torrent:
    #   Keep trying till you get True as return value from add_torrent
    def remove_torrent(self, torrent_name):
        if self.session is not None:
            target_handler = self.find_torrent(torrent_name.split('.')[0]+'.webm')
            self.session.remove_torrent(target_handler)
            self.torrent_handle_list.remove(target_handler)
            return True
        else:
            return None

    # Gets a torrent name and retrieves its status
    # Given that variable s is the return value, sample interpretation of it would be:
    # state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
    # print('\r%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, state_str[s.state]))
    def get_torrent_stat(self, file_name):
        target_handler = self.find_torrent(file_name)
        if target_handler is not None:
            return target_handler.status()
        return None

    def get_torrent_stat_str(self, file_name):
	s = self.get_torrent_stat(file_name)
	if s is not None:
            state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
	    self.log.debug('\r%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, state_str[s.state]))

