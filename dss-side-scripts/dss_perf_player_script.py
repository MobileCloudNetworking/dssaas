__author__ = 'Santi'

import pycurl
import cStringIO
import json
import time
import httplib as http
import threading
import datetime

class RequestManager:

    def __init__(self):
        self.dl_time = 0.0

    def doCurlRequest(self, target_url):
        response_status = 0
        if (response_status < 200 or response_status >= 400):
            curl = pycurl.Curl()
            buff = cStringIO.StringIO()
            curl.setopt(pycurl.URL, target_url)
            curl.setopt(pycurl.WRITEFUNCTION, buff.write)
            try:
                    start = time.time()
                    curl.perform()
                    end = time.time()
                    response_status = int(curl.getinfo(pycurl.HTTP_CODE))
            except Exception as e:
                    response_status = -1
                    end = time.time()
            curl.close()
            if (response_status < 200 or response_status >= 400):
                return target_url, response_status, end - start

        return target_url, response_status, (end - start)

class playerThread(threading.Thread):

    def __init__(self, id, url_to_poll, rps, max, lock):
        threading.Thread.__init__(self)
        self.thread_rps = rps
        self.url_to_poll = url_to_poll
        self.max = max
        self.id = id
        self.lock = lock
        if self.max > 0:
            self.max = self.max + 1

    def run(self):
        cntManager = RequestManager()
        time_between_calls = 1.0/float(self.thread_rps)
        while self.max > 1 or self.max == 0:
            if self.max > 1:
                self.max = self.max - 1
            targeturl, result, rqtime = cntManager.doCurlRequest(self.url_to_poll)
            lock.acquire()
            print (str(datetime.datetime.now()) + ",Player" + str(self.id) + "," + str(targeturl) + "," + str(result) + "," + str(rqtime))
            lock.release()
            tts = time_between_calls - rqtime
            if tts < 0:
                tts = 0
            time.sleep(tts)

if __name__ == "__main__":
    threads = 30
    rps = 15 # per thread
    url = "http://160.85.4.39/WebAppDSS/display/playAll?id=1&type_request=refresh"
    max = 0 # 0 unlimted
    ramptime = 10 # s

    lock = threading.Lock()
    for i in range (0, threads):
        playerThread(i, url, rps, max, lock).start()
        time.sleep(ramptime)

    #Making app wait till someone actually kill the process
    while True:
        time.sleep(1)