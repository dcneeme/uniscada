# listen and forward UDP messages

class UDPReader(object): # object on millegiparast vajalik
    def __init__(self, addr, port, handler):
        import socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.bind((addr, port))
        
        self.addr=addr
        self.port=port
        self.handler=handler
        
        self._io_loop = tornado.ioloop.IOLoop.instance()
        self._io_loop.add_handler(self._sock.fileno(), functools.partial(self._callback, self._sock), self._io_loop.READ)

    def _callback_read(self, sock, fd):
        (data, addr) = sock.recvfrom(4096)
        self.ts=time.time()
        print("got UDP data: " + str(data))
        self._protocolhandler(data, { "source": "UDPReader", "sender": addr })

    
    
if __name__ == '__main__':
    UDPReader(self.addr, self.port, self.handler)
