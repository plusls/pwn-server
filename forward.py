import logging
import threading
import socket

PKT_BUFF_SIZE = 4096


# 单向流数据传递
def tcp_mapping_worker(conn_receiver, conn_sender, log_name):
    logger = logging.getLogger(log_name)
    while True:
        try:
            data = conn_receiver.recv(PKT_BUFF_SIZE)
        except Exception:
            logger.info('Connection closed.')
            break
        if not data:
            logger.info('No more data is received.')
            break
        try:
            conn_sender.sendall(data)
        except Exception:
            logger.error('Failed sending data.')
            break
        logger.info('local:{}\n{} -> {}:{}\n'.format(conn_sender.getsockname(), conn_receiver.getpeername(), conn_sender.getpeername(), repr(data)))
    try:
        conn_receiver.shutdown(socket.SHUT_RDWR)
        conn_sender.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    conn_receiver.close()
    conn_sender.close()
    return

# 端口映射请求处理
def tcp_mapping_request(local_conn, remote_ip, remote_port, log_name):
    logger = logging.getLogger(log_name)
    remote_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        remote_conn.connect((remote_ip, remote_port))
    except Exception:
        local_conn.close()
        logger.error('Unable to connect to the remote server.')
        return
    threading.Thread(target=tcp_mapping_worker, args=(local_conn, remote_conn, log_name)).start()
    threading.Thread(target=tcp_mapping_worker, args=(remote_conn, local_conn, log_name)).start()
    return