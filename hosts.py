# host.py - an instance for site controller ip, port, statistics
import time

class Hosts:
    ''' Keeps account about hosts talkinfg to the udpcommm instance '''
    def __init__(self):
        self.hostcount = 0
        self.host_dict = {}
        self.h = [] # host instances


    def getcount():
        return self.hostcount


    def addhost(self, id, addr = []):
        if not h[host_dict[id]]:
            nextnum = self.hostcount +1 # max(host_dict) + 1
            host_dict.update({ id : nextnum })
            self.h[nextnum] = Host(id, addr) # h[0] unused



class Host(Hosts):
    ''' Keeps account about one site controller ip, port and incoming msg count '''

    def __init__(self, id, addr = []):
        self.id = id
        self.addr = addr
        self.socket_ts = time.time()
        self.getload_ts = self.socket_ts
        self.zerocount() # message counter


    def setaddr(self,addr):
        if addr != self.addr:
            self.addr = addr
            self.socket_ts = time.time()


    def getaddr(self):
        return self.addr


    def getcount(self):
        return self.count


    def zerocount(self):
        self.count = 0



# #############################################

if __name__ == '__main__':
    Hosts()
