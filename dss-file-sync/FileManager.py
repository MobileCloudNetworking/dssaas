__author__ = "Santiago Ruiz"
__copyright__ = "Copyright 2015, SoftTelecom"
__credits__ = ["Santiago Ruiz"]
__version__ = "1.0.1"
__maintainer__ = "Santiago Ruiz"
__email__ = "srv@softtelecom.eu"
__status__ = "Alpha"

import os
import logging
import Config

class FileManager:

    def __init__(self):
        self.file_list = []
        self.log = logging.getLogger(Config.get('log','name'))

    # Lists all the file with specified extensions in specified path
    # Note: Needs to be called to snapshot the new list of files after remove or remove_all operations
    # Sample call: list_files(path='./', extensions=['.webm','.torrents'])
    def list_files(self, path, extensions):
        self.file_list = [ f for f in os.listdir(path) if f.endswith(tuple(extensions)) ]
        if len(self.file_list) > 0:
            return True, self.file_list
        else:
            return False, self.file_list

    # Lists the newly added files with specified extensions in specified path
    # Note: When called it buffers the list of files for next call
    # Sample call: new_file_exists(path='./', extensions=['.webm','.torrents'])
    def new_file_exists(self, path, extensions):
        current_file_list = [ f for f in os.listdir(path) if f.endswith(tuple(extensions)) ]
        list_of_new_files = []
        if current_file_list != self.file_list and len(current_file_list) > len(self.file_list):
            i = 0
            while i < len(current_file_list):
                if current_file_list[i] not in self.file_list:
                    list_of_new_files.append(current_file_list[i])
                i += 1
            self.file_list = current_file_list
            return True, list_of_new_files
        else:
            self.file_list = current_file_list
            return False, list_of_new_files

    # Removes the specified file in given path
    # Note: call list_files function to update the file list snapshot after each delete call
    # Sample call: remove_file(path='./', filename='1.webm')
    def remove_file(self, path, filename):
        try:
            os.remove(path + filename)
            #self.list_files(path)
            return True
        except Exception as e:
            self.log.debug("Removal Exception: " + str(e))
            return False

    # Removes all files with specified extensions in given path
    # Note: call list_files function to update the file list snapshot after each delete call
    # Sample call: remove_all(path='./', extensions=['.webm','.torrents'])
    def remove_all(self, path, extensions):
        try:
            file_list = [ f for f in os.listdir(path) if f.endswith(tuple(extensions)) ]
            for f in file_list:
                os.remove(path + f)
            #self.list_files(path)
            return True
        except Exception as e:
            self.log.debug("Removal Exception: " + str(e))
            return False

    # Returns the size of specified file in given path in bytes
    # Sample call: get_size(path='./', filename='1.webm')
    def get_size(self, path, filename):
        try:
            stat_info = os.stat(path + filename)
            return True, stat_info.st_size
        except Exception as e:
            self.log.debug("Get Stat Exception: " + str(e))
            return False, 0

    # Returns True if the specified file in given path exists, otherwise False
    # Sample call: file_exists(path='./', filename='1.webm')
    def file_exists(self, path, filename):
        try:
            return os.path.isfile(path + filename)
        except Exception as e:
            self.log.debug("Check File Exception: " + str(e))
            return False