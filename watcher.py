"""
Big Brother Is Watching you
"""
import threading
import time
import ctypes
import os
from pyinotify import WatchManager, Notifier, ProcessEvent
from pyinotify import IN_DELETE, IN_CREATE, IN_MODIFY, IN_ACCESS

class EventHandler(ProcessEvent):
    """process event"""
    def my_init(self, **kargs):
        global big_bros_list
        self.watch_list = big_bros_list

    def process_IN_ACCESS(self, event):
        print "Access file: %s" % os.path.join(event.path,event.name)
        self.watch_list[token]['last_access'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class Watcher(object):
    def __init__(self):
        global big_bros_list = {}
        self.watch_list = big_bros_list
        self.wm = WatchManager()
        self.mask = IN_ACCESS
        self.notifier = Notifier(self.wm, EventHandler())
        
    def add_watch_file(self, token):
        c_path = token
        self.watch_list[token] = {'last_access':0}
        self.wm.add_watch(c_path, self.mask, rec=True)
        
    def rmv_watch_file(self, token):
        # kill it
        del self.watch_list[token]

    def get_last_access(self, token):
        try:
            return self.watch_list[token]['last_access']
        except Exception:
            print("Error: wrong token.")
            return 0

