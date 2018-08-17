'''
misc
'''
import ctypes
libc = ctypes.cdll.LoadLibrary('/lib/x86_64-linux-gnu/libc.so.6')


def get_ppid(pid):
    fp = open('/proc/{}/stat'.format(pid), 'rb')
    stat = fp.read()
    fp.close()
    idx = stat.rfind(b')')
    ppid = int(stat[idx + 2:].split(b' ')[1])
    return ppid
