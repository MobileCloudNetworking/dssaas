__author__ = 'Santi'

import libtorrent as lt
import logging

class SessionManager:

    def __init__(self):
        self.session = None
        self.torrent_handle_list = []
        self.log=logging.getLogger('mylog')

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
    def find_torrent(self, torrent_name):
        for item in self.torrent_handle_list:
            if item.name() == torrent_name:
                return item
        return None

    # Not available ATM
    def update_torrents(self, torrent_list):
        pass

    # Gets a torrent name and adds it to the session and the torrent_handle_list
    def add_torrent(self, torrent_name):
        try:
            handler = self.session.add_torrent({'ti': lt.torrent_info(torrent_name), 'save_path': '.', 'seed_mode': True, 'auto_managed': True})
            self.torrent_handle_list.append(handler)
            return True
        except:
            return False

    # Gets a torrent name and removes it from the session and the torrent_handle_list
    # Remember: It's not happening immediately and you can not add the same torrent while one is deleting
    # Therefore, add_torrent is written in a way that returns False in case of exception.
    # In case you are deleting and adding the same torrent:
    #   Keep trying till you get True as return value from add_torrent
    def remove_torrent(self, torrent_name):
        if self.session is not None:
            target_handler = self.find_torrent(torrent_name)
            self.session.remove_torrent(target_handler)
            self.torrent_handle_list.remove(target_handler)
            return True
        else:
            return None

    # Gets a torrent name and retrieves its status
    # Given that variable s is the return value, sample interpretation of it would be:
    # state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
    # print('\r%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, state_str[s.state]))
    def get_torrent_stat(self, torrent_name):
        target_handler = self.find_torrent(torrent_name)
        if target_handler is not None:
            return target_handler.status()
        return None
