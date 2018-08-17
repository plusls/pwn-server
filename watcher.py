"""
Big Brother Is Watching you
"""
import threading
import time
import ctypes
import os
import fanotify

get_token = lambda path: path # To-Do
get_path = lambda token: token # To-Do

def fa_worker(fan_fd):
    global big_bros_list
    while True:
        buf = os.read(fan_fd, 4096)
        assert buf
        while fanotify.EventOk(buf):
            buf, event = fanotify.EventNext(buf)
            if event.mask & fanotify.FAN_Q_OVERFLOW:
                print('Queue overflow !')
                continue
            fdpath = '/proc/self/fd/{:d}'.format(event.fd)
            full_path = os.readlink(fdpath)
            token = get_token(full_path)
            if token in big_bros_list.keys():
                big_bros_list[token]['last_access'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                big_bros_list[token]['pid'] = event.pid
                print(big_bros_list[token]['last_access'], full_path, big_bros_list[token]['pid']) # DEBUG
            os.close(event.fd)
        assert not buf

class Watcher(object):
    def __init__(self):
        global big_bros_list
        big_bros_list = {}
        self.watch_list = big_bros_list
        self.fan_fd = fanotify.Init(fanotify.FAN_CLASS_CONTENT, os.O_RDONLY)
        fanotify.Mark(self.fan_fd,
                fanotify.FAN_MARK_ADD | fanotify.FAN_MARK_MOUNT,
                fanotify.FAN_OPEN | fanotify.FAN_EVENT_ON_CHILD,
                -1,'/')
        threading.Thread(target=fa_worker, args=(self.fan_fd,)).start()

    def add_watch_file(self, token):
        self.watch_list[token] = {'last_access':0, 'pid':0}
        
    def rmv_watch_file(self, token):
        del self.watch_list[token]

    def get_last_access(self, token):
        try:
            return (self.watch_list[token]['pid'], self.watch_list[token]['last_access'])
        except Exception:
            print("Error: wrong token.")
            return 0
