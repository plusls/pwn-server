import socket
def myrecv(s, buffersize, flag=0):
    while True:
        try:
            return s.recv(buffersize, flag)
        except socket.timeout as e:
            print('timeout {}'.format(e))
            continue


def recvuntil(connect_socket, s, maxlen=200):
    ret = b''
    while True:
        #tmp = connect_socket.recv(1000, flags=(socket.MSG_PEEK|socket.MSG_DONTWAIT))
        tmp = myrecv(connect_socket, 1000)
        idx = tmp.find(s)
        if idx != -1:
            ret += tmp[:idx + 1]
            return ret
        elif len(ret) > maxlen:
            return ''

def set_keepalive_linux(sock, after_idle_sec=1, interval_sec=3, max_fails=5):
    """Set TCP keepalive on an open socket.
 
    It activates after 1 second (after_idle_sec) of idleness,
    then sends a keepalive ping once every 3 seconds (interval_sec),
    and closes the connection after 5 failed ping (max_fails), or 15 seconds
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)

