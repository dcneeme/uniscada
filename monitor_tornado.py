#!/usr/bin/python
# OOP ja tornado kasutusel udp sonumite vastuvotuks. vahenda sync osa , vt loppu
# neeme 20.07.2014 alustatud monitor_multi4.py alusel

import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc

import sqlite3
import sys
sys.path.append('/root/tornado-3.2/')
sys.path.append('/root/backports.ssl_match_hostname-3.4.0.2/src')
#import tornado

import traceback
#import subprocess

from socket import *
import string

# Set the socket parameters
SQLDIR='/srv/scada/uniscada/sqlite/' #  "/data/scada/sqlite" # testimiseks itvilla serveris
port = 44445 # testimiseks 44444, pane parast 44445
if len(sys.argv)>1: # ilmselt ka port antud siis
    port=int(sys.argv[1]) # muidu jaab default value 44445
    print 'udp port set to',port
    sys.stdout.flush()
    time.sleep(1)

 

class UDPReader(object): # incoming udp to events
    def __init__(self, addr, port):
        import socket
        import tornado.ioloop
        import functools

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.bind((addr, port))
        self._sock.settimeout(0.1) # to get more than 1 key:value
        self._io_loop = tornado.ioloop.IOLoop.instance()
        self._io_loop.add_handler(self._sock.fileno(), functools.partial(self._callback, self._sock), self._io_loop.READ)

        
    def _callback(self, sock, fd, events):
        if events & self._io_loop.READ:
            self._callback_read(sock, fd)
        if events & self._io_loop.ERROR:
            print("IOLoop error")
            sys.exit(1)
            

    def _callback_read(self, sock, fd):
        (data, addr) = sock.recvfrom(4096)
        self.ts=time.time()
        print("got UDP data: " + str(data))
        self.udp2state(data) # store to state in here as well
        # add more event based functions here
        
        
    def udp2state(self,data):
        ress=0
        res=0
        if "id:" in data: # first check based on host id existence in the received message, must exist to be valid message!
            lines=data.splitlines()
            #print('received lines count',len(lines)) # debug
            id=data[data.find("id:")+3:].splitlines()[0]
            for i in range(len(lines)): # looking into every member (line) of incoming message
                #print('line',i,lines[i]) # debug
                if ":" in lines[i] and not 'id:' in lines[i]:
                    line = lines[i].split(':') # tuple
                    register = line[0] # setup reg name
                    value = line[1] # setup reg value
                    #print('received from controller',id,'key:value',register,value) # debug
                    res=self.statemodify(id,register,value)
                    if res == 0:
                        print('statemodify done for',id,register,value)
                    else:
                        print('statemodify FAILED for',id,register,value)
                ress+=res
        else:
            print('invalid datagram, no id found in',data)
            ress+=1
        return ress
        
    def statemodify(self, id, register, value): # received key:value to state table
        ''' received key:value to state table '''
        DUE_TIME=self.ts+5 # min pikkus enne kordusi, tegelikult pole vist vaja
        try: # new state for this id
            Cmd="INSERT INTO STATE (register,mac,value,timestamp,due_time) VALUES \
            ('"+register+"','"+id+"','"+str(value)+"','"+str(self.ts)+"','"+str(DUE_TIME)+"')"
            #print Cmd
            conn.execute(Cmd) # insert, kursorit pole vaja
                    
        except:   # UPDATE the existing state for id
            Cmd="UPDATE STATE SET value='"+str(value)+"',timestamp='"+str(self.ts)+"',due_time='"+str(DUE_TIME)+"' \
            WHERE mac='"+id+"' AND register='"+register+"'"
            #print Cmd
            
            try:
                conn.execute(Cmd) # update, kursorit pole vaja
                #print 'state update done for mac',id,'register',locregister # ajutine
                
            except:
                traceback.print_exc()
                return 1 # kui see ka ei onnestu, on mingi jama

        return 0 # DUE_TIME  state_modify lopp




 
 
# #############################################################
# #################### MAIN ###################################
# #############################################################

        


if __name__ == '__main__':
    import time
    import datetime
    import tornado.ioloop

    from sqlgeneral import *
    s=SQLgeneral('/srv/scada/uniscada/sqlite/',['state','newstate','controller','service_*.sql']) # sql files to read 
    

    def sync_tasks(): # regular checks, sends here
        print("executing sync tasks...")
        
        print("UPD processing until next sync...")
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.add_timeout(datetime.timedelta(seconds=1), sync_tasks)

    UDPReader("0.0.0.0", port)

    sync_tasks()
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()
