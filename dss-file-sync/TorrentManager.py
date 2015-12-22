
import libtorrent as lt
import base64
import logging

class TorrentManager:
    #TODO: checkfile thread
    def __init__(self, file_manager):
        self.log=logging.getLogger('mylog')
        self.fm = file_manager
        self.torrent_list = self.fm.list_files('.',['.torrent'])[1]


    def createTorrent(self,filename,torrentname,comment='test',path='./'):
        #Create torrent
        fs = lt.file_storage()
        lt.add_files(fs, path+filename)
        t = lt.create_torrent(fs)
        for tracker in self.tracker_list:
            t.add_tracker(tracker, 0)
        t.set_creator('libtorrent %s' % lt.version)
        t.set_comment(comment)
        lt.set_piece_hashes(t, ".")
        torrent = t.generate()
        f = open(path+torrentname, "wb")
        f.write(lt.bencode(torrent))
        f.close()

    def setTorrent(self,torrent_name,torrent_base64_enc):
        pass

    def getTorrentList(self): #latest, files in HD
        self.torrent_list = self.fm.list_files('.',['.torrent'])[1]
        return self.torrent_list

    def getTorrentContent(self,torrent_name):
        #retrieve the content and encode base64
        encoded_string=''
        with open(torrent_name, "rb") as torrent_file:
            encoded_string = base64.b64encode(torrent_file.read())
        LOG.debug(str(encoded_string))
        return encoded_string
