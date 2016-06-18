#!/usr/bin/python
# neeme 13.4.2016 www/cmd2controller2.py alusel
# kuulab apiserverist tulevat udp infot nagu kontroller ja kui midagi saab, saadab edasi newstate tabelisse.

# Import modules for CGI handling 

import os, sys, time
import logging
try:
    import chromalog # colored
    chromalog.basicConfig(level=logging.INFO, format='%(name)-30s: %(asctime)s %(levelname)s %(message)s')
except ImportError:
    print('warning - chromalog and colorama probably not installed...')
    time.sleep(2)
    ##logging.basicConfig(format='%(name)-30s: %(asctime)s %(levelname)s %(message)s') # FIXME ei funka!
    logging.basicConfig(stream=sys.stderr, level=logging.INFO) # selles ei ole aega ega formaatimist
log = logging.getLogger(__name__)


#import cgi, cgitb, re
#cgitb.enable() # neeme lisas 21.01.2012

import sqlite3 
conn = sqlite3.connect('/srv/scada/sqlite/monitor',2)
cursor=conn.cursor()

import traceback
import subprocess
import string

from uniscada4newstate import UDPchannel
apilisten = UDPchannel(id='000') # milliseid id kuulata, kuulab koiki kus see string esineb
# ip='91.236.222.106', port=44444  vaikimisi

def write_newstate(dict):
    ''' writing into newstate ''' 
    #esialgsed vaartused cli testimiseks
    mac='00204AB81729'
    cmd=''
    reg='' # siin selline vaartus kui reg ja val ei anta
    val='' # siia asemele tegelik cmd kui see antakse
    register=''
    value='' # kontrollmuutujad

    log.info('dict '+str(dict))
    sqlcmd="insert into newstate(mac,register,value) values('"+mac+"','"+register+"','"+value+"')" #  register ja value
        
        
    if register != '' and value != '':  # tundub korras
        try:
            conn.execute(sqlcmd) 
            conn.commit()
            log.info('newstate written')
        except:
            traceback.print_exc() 
            log.warning('newstate write failed')
            



############  MAIN  ##########################
if __name__ == '__main__':
    while True:
        got = apilisten.udpread()
        time.sleep(1)
        if got != None:
            log.info('got '+str(got)) # write_newstate(got)
