# host.py - an instance for site controller ip, port, statistics

class Host():
    ''' Keeps account about one site controller ip, port and incoming msg count '''
    hosts = [] # host instances

    def __init__(self, comm, chdata = {} ): # comm=udpcomm()
        self._addhost(comm, chdata)


    def send(self, sendmessage):
        self.comm.send(self.chdata, sendmessage)


    def _addhost(self, comm, chdata = {} ):
        self.comm = comm
        self.chdata = chdata
        self.__class__.hosts.append({ 'comm': comm, 'chdata': chdata })

    def listhosts():
        return hosts

    #def _delhost(self, ): # remove if timeout

# #############################################

if __name__ == '__main__':
    pass
