# listen and forward UDP messages
import traceback
from host import *
import socket
import tornado.ioloop
import functools # from functools import partial

class UDPComm(object): # object on millegiparast vajalik
    def __init__(self, addr, port, handler):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.bind((addr, port))

        self.addr=addr
        self.port=port
        self.handler=handler

        self._io_loop = tornado.ioloop.IOLoop.instance()
        self._io_loop.add_handler(self._sock.fileno(), functools.partial(self._callback, self._sock), self._io_loop.READ)


    def _callback(self, sock, fd, events):  # fd is some file descriptor... (?)
        if events & self._io_loop.READ:
            self._callback_read(sock, fd)
        if events & self._io_loop.ERROR:
            print("IOLoop error")
            sys.exit(1)

    def _callback_read(self, sock, fd):
        (data, addr) = sock.recvfrom(4096)
        #debugdata = { "from": { "ip": addr[0], "port": addr[1] }, "msg": str(data) }
        debugdata = { "from": addr, "msg": str(data) }
        print("got UDP " + str(debugdata))
        h=Host(self, addr)
        self.handler(h, data)


    def send(self, addr, sendstring = ''): # actual udp sending. give message as parameter
        ''' Sends UDP data immediately, adding self.inum if >0. '''
        if sendstring == '': # nothing to send
            print('send(): nothing to send!')
            return 1
        print('send going to send to', addr, sendstring) # debug
        try:
            sendlen=self._sock.sendto(sendstring.encode('utf-8'), addr) # tagastab saadetud baitide arvu
            msg='sent ack to '+str(repr(addr))+' '+sendstring.replace('\n',' ')   # debug show as one line
            print(msg)
            return sendlen
        except:
            traceback.print_exc() # debug
            return None

# #############################################

if __name__ == '__main__':
    UDPComm(self.addr, self.port, self.handler)
