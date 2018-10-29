"""
Big Brother Is Watching you
"""
import threading
import time
import ctypes
import os
import fanotify
from misc import get_ppid, parse_tcp_data, get_cmdline
import docker


def IsRootProcess(pid): return os.stat('/proc/{}'.format(pid)).st_uid == 0


class Watcher(object):
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.watch_dict = {}
        self.fan_fd = fanotify.Init(
            fanotify.FAN_CLASS_PRE_CONTENT, os.O_RDONLY)
        self.thread = threading.Thread(target=self._fa_worker)
        
        # 设置为守护线程
        self.thread.setDaemon(True)
        self.thread.start()

    def _get_token(self, path):
        token = path[path.rfind('flag_') + 5:]
        return token  # To-Do

    def _get_path(self, token):
        return '{}/{}/flag'.format(self.data_dir, token)

    def add_watch_file(self, token, socket_data):
        if token not in self.watch_dict:
            self.watch_dict[token] = {}
            fanotify.Mark(self.fan_fd,
                        fanotify.FAN_MARK_ADD,
                        fanotify.FAN_OPEN_PERM,
                        -1, self._get_path(token))
        self.watch_dict[token][socket_data] = False

    def rmv_watch_file(self, token, socket_data):
        del self.watch_dict[token][socket_data]
        if len(self.watch_dict[token]) == 0:
            fanotify.Mark(self.fan_fd,
                          fanotify.FAN_MARK_REMOVE,
                          fanotify.FAN_OPEN_PERM,
                          -1, self._get_path(token))
            del self.watch_dict[token]

    def get_last_access(self, token, socket_data):
        try:
            return self.watch_dict[token][socket_data]
        except Exception:
            print("Error: wrong token.")
            return None

    def _fa_worker(self):
        while True:
            buf = os.read(self.fan_fd, 4096)
            assert buf
            while fanotify.EventOk(buf):
                buf, event = fanotify.EventNext(buf)
                if event.mask & fanotify.FAN_Q_OVERFLOW:
                    print('Queue overflow !')
                    continue
                fdpath = '/proc/self/fd/{:d}'.format(event.fd)
                full_path = os.path.abspath(os.readlink(fdpath))
                token = self._get_token(full_path)
                if token in self.watch_dict:
                    # 获取socket数据
                    socket_data = self._get_socket_data(token, event.pid)
                    if socket_data != None:
                        self.watch_dict[token][socket_data] = True
                        print(socket_data, full_path)  # DEBUG
                os.write(self.fan_fd, fanotify.Response(
                    event.fd, fanotify.FAN_ALLOW))
                os.close(event.fd)
            assert not buf

    def _get_socket_data(self, token, pid):
        '''根据pid确定socket'''
        # 连接docker
        docker_client = docker.from_env()
        pwn_containers = docker_client.containers.get(token)
        tcp_data_str = pwn_containers.exec_run(
            'cat /proc/net/tcp').output.decode()
        docker_client.close()
        # 解析所有tcp连接的数据
        tcp_data_list = parse_tcp_data(tcp_data_str)
        socket_inode_list = []
        now_pid = pid
        # 获取其进程以及父进程的所有socket inode
        while True:
            dir_list = os.listdir('/proc/{}/fd'.format(now_pid))
            for fd in dir_list:
                path = os.readlink('/proc/{}/fd/{}'.format(now_pid, fd))
                if path.startswith('socket:['):
                    idx1 = path.find('[')
                    idx2 = path.rfind(']')
                    socket_inode = int(path[idx1 + 1:idx2])
                    if socket_inode not in socket_inode_list:
                        socket_inode_list.append(socket_inode)
            now_pid = get_ppid(now_pid)
            if now_pid == 0 or b'/bin/sh\x00-c\x00/ctf/pwn/bin/startdocker.sh\x00' == get_cmdline(now_pid):
                break

        for socket_inode in socket_inode_list:
            for tcp_data in tcp_data_list:
                if tcp_data.inode == socket_inode:
                    return tcp_data.rem_address
        return None

