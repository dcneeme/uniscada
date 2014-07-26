#!/usr/bin/python
# OOP ja tornado kasutusel udp sonumite vastuvotuks. vahenda sync osa , vt loppu
# neeme 20.07.2014 alustatud monitor_multi4.py alusel

import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc
import sys
sys.path.append('/root/tornado-3.2/')
sys.path.append('/root/backports.ssl_match_hostname-3.4.0.2/src')
#import tornado

import traceback
#import subprocess

#from socket import *
import string

import tornado.ioloop
import functools

from udpreader import *
from sdpbuffer import *

# Set the socket parameters for communication with the site controllers
SQLDIR='/srv/scada/uniscada/sqlite/' #  "/data/scada/sqlite" # testimiseks itvilla serveris
tables=['state','newstate','controller','service_*'] # to be added
addr='0.0.0.0'
port = 44445 # testimiseks 44444, pane parast 44445

if len(sys.argv)>1: # ilmselt ka port antud siis
    port=int(sys.argv[1]) # muidu jaab default value 44445
    print 'udp port set to',port
    sys.stdout.flush()
    time.sleep(1)

    
class MonitorUniscada:
    def __init__(self, port, SQLDIR, tables):
        self.port=port
        self.SQLDIR=SQLDIR
        self.tables=tables # tuple
        self.b=SDPBuffer(SQLDIR,tables)
        self.u=UDPReader(addr,port,b.udp2state) # addr, port, handler
        ioloop = tornado.ioloop.IOLoop.instance()
        
    
    def sync_tasks(self,delay): # regular checks or tasks
        print("executing sync tasks...")
        # puit here tasks to be executed in 1 s interval
        
        print("UPD processing until next sync...")
        ioloop.add_timeout(datetime.timedelta(seconds=delay), sync_tasks)

        
    def start(self):
        ioloop.start()
    
    
# ###############################################################

if __name__ == '__main__':
    
    m=MonitorUniscada( , , )
    m.start()
    
    