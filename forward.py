"""
转发流量
"""

import logging
import threading
import socket
import time
import os
from watcher import Watcher
from mysocket import myrecv

PKT_BUFF_SIZE = 4096

# big brother is watching you
big_brother = None


def init_big_brother(data_dir):
    global big_brother
    big_brother = Watcher(data_dir)


# 单向流数据传递
def tcp_mapping_worker(conn_receiver, conn_sender, log_name, token):
    logger = logging.getLogger(log_name)
    while True:
        try:
            data = myrecv(conn_receiver, PKT_BUFF_SIZE)
        except Exception as e:
            logger.info('Exception:{} msg: {} Connection closed.'.format(str(type(e)), str(e)))
            break
        if not data:
            logger.info('No more data is received.')
            break
        try:
            conn_sender.sendall(data)
        except Exception:
            logger.error('Failed sending data.')
            break
        logger.info('{}->{}->{}->{}:\n{}'.format(conn_receiver.getpeername(),
                                                 conn_receiver.getsockname(),
                                                 conn_sender.getsockname(),
                                                 conn_sender.getpeername(),
                                                 repr(data)))
    try:
        conn_receiver.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass

    try:
        conn_sender.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    return

# 端口映射请求处理


def tcp_mapping_request(local_conn, remote_ip, remote_port, log_name, log_dir, token):
    '''流量转发+记录'''
    global big_brother
    logger = logging.getLogger(log_name)
    remote_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        remote_conn.connect((remote_ip, remote_port))
    except Exception:
        local_conn.close()
        logger.error('Unable to connect to the remote server.')
        return

    t1 = threading.Thread(target=tcp_mapping_worker, args=(
        local_conn, remote_conn, log_name, token))
    t2 = threading.Thread(target=tcp_mapping_worker, args=(
        remote_conn, local_conn, log_name, token))
    socket_data = remote_conn.getsockname()
    big_brother.add_watch_file(token, socket_data)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    file_handle = logger.handlers[0]
    logger.info('fd:{} {}'.format(local_conn.fileno(), remote_conn.fileno()))
    logger.removeHandler(file_handle)
    file_handle.close()
    get_flag = big_brother.get_last_access(token, socket_data)
    if get_flag:
        old_log_path = '{}/{}.log'.format(log_dir, log_name)
        new_log_path = '{}/{}-flag.log'.format(log_dir, log_name)
        print('big brother catch you')
        os.rename(old_log_path, new_log_path)
    big_brother.rmv_watch_file(token, socket_data)

    local_conn.close()
    remote_conn.close()
    return
