'''
misc
'''
import ctypes
import re


class TCPData(object):
    def __init__(self, s):
        s = s.strip()
        while True:
            tmp = s.replace('  ', '')
            if s == tmp:
                break
            s = tmp
        # sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
        # 0: 0B00007F:9F95 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 183745 1 0000000000000000 100 0 0 10 0
        result = re.match(r"(\S+): (\S+):(\S+) (\S+):(\S+) (\S+) (\S+):(\S+) (\S+):(\S+) (\S+) (\S+) (\S+)",s).groups()
        self.local_address = (self._hex_to_ip(result[1]), int(result[2], 16))
        self.rem_address = (self._hex_to_ip(result[3]), int(result[4], 16))
        self.inode = int(result[12])
        #print(self.local_address, self.rem_address, self.inode)

    def _hex_to_ip(self, hex_str):
        # a.b.c.d
        d = int(hex_str[0:2], 16)
        c = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        a = int(hex_str[6:8], 16)
        return '{}.{}.{}.{}'.format(a, b, c, d)


def parse_tcp_data(tcp_data_str):
    ret = []
    tcp_data_list = tcp_data_str.split('\n')[1:]
    for s in tcp_data_list:
        if ':' not in s:
            continue
        tcp_data = TCPData(s)
        ret.append(tcp_data)
    return ret


def get_ppid(pid):
    fp = open('/proc/{}/stat'.format(pid), 'rb')
    stat = fp.read()
    fp.close()
    idx = stat.rfind(b')')
    ppid = int(stat[idx + 2:].split(b' ')[1])
    return ppid

def get_cmdline(pid):
    fp = open('/proc/{}/cmdline'.format(pid), 'rb')
    cmdline = fp.read()
    fp.close()
    return cmdline    

def get_filename(pid):
    fp = open('/proc/{}/stat'.format(pid), 'rb')
    stat = fp.read()
    fp.close()
    idx1 = stat.lfind(b'(')
    idx2 = stat.rfind(b')')
    filename = stat[idx1 + 1: idx2]
    return filename