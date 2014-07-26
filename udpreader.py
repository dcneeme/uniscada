# listen and forward UDP messages

class UDPReader(object): # object on millegiparast vajalik
    def __init__(self, addr, port, handler):
        import socket
        import tornado.ioloop
        import functools # from functools import partial
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.bind((addr, port))
        
        self.addr=addr
        self.port=port
        self.handler=handler
        
        self._io_loop = tornado.ioloop.IOLoop.instance()
        self._io_loop.add_handler(self._sock.fileno(), functools.partial(self._callback, self._sock), self._io_loop.READ)

        
    def _callback(self, sock, fd, events):  # ? mis on fd ? 
        if events & self._io_loop.READ:
            self._callback_read(sock, fd)
        if events & self._io_loop.ERROR:
            print("IOLoop error")
            sys.exit(1)

    def _callback_read(self, sock, fd):
        (data, addr) = sock.recvfrom(4096)
        debugdata = { "from": { "ip": addr[0], "port": addr[1] }, "msg": str(data) }
        print("got UDP " + str(debugdata))
        self.handler(data)


# #############################################

if __name__ == '__main__':
    UDPReader(self.addr, self.port, self.handler)
