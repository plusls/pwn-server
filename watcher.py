"""
Big Brother Is Watching you
"""
import threading
import time
import ctypes
import os
import fanotify
from misc import get_ppid

IsRootProcess = lambda pid: os.stat('/proc/{}'.format(pid)).st_uid == 0

class Watcher(object):
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.watch_dict = {}
        self.fan_fd = fanotify.Init(fanotify.FAN_CLASS_PRE_CONTENT, os.O_RDONLY)
        self.thread = threading.Thread(target=self._fa_worker)
        self.thread.start()

    def _get_token(self, path):
        return path  # To-Do

    def _get_path(self, token):
        return '{}/{}/flag'.format(self.data_dir, token)

    def add_watch_file(self, token):
        self.watch_dict[token] = {'last_access': 0, 'pid': 0}
        fanotify.Mark(self.fan_fd,
                      fanotify.FAN_MARK_ADD,
                      fanotify.FAN_OPEN_PERM,
                      -1, self._get_path(token))

    def rmv_watch_file(self, token):
        fanotify.Mark(self.fan_fd,
                      fanotify.FAN_MARK_REMOVE,
                      fanotify.FAN_OPEN_PERM,
                      -1, self._get_path(token))
        del self.watch_dict[token]

    def get_last_access(self, token):
        try:
            return (self.watch_dict[token]['pid'], self.watch_dict[token]['last_access'])
        except Exception:
            print("Error: wrong token.")
            return None

    def _fa_worker(self):
        while True:
            buf = os.read(self.fan_fd, 4096)
            assert buf
            response = fanotify.FAN_ALLOW # ALL ALLOW
            while fanotify.EventOk(buf):
                buf, event = fanotify.EventNext(buf)
                print(get_ppid(event.pid))

                if event.mask & fanotify.FAN_Q_OVERFLOW:
                    print('Queue overflow !')
                    continue
                fdpath = '/proc/self/fd/{:d}'.format(event.fd)
                full_path = os.path.abspath(os.readlink(fdpath))
                token = self._get_token(full_path)
                print(token)
                if token in self.watch_dict:
                    self.watch_dict[token]['last_access'] = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime())
                    self.watch_dict[token]['pid'] = event.pid
                    print(self.watch_dict[token]['last_access'],
                          full_path, self.watch_dict[token]['pid'])  # DEBUG
                os.write(self.fan_fd, fanotify.Response(event.fd, response))
                os.close(event.fd)
            assert not buf

