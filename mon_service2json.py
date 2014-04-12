#!/usr/bin/python
# -*- coding: UTF-8 -*-# 
# outputs key:servicename(s) from sql database as simple json. required parameters are mac (object id), optional key (multiple keys allowed)
# neeme 11.12.2013

# valid usage   ...py?mac=4642652353
# valid usage   ...py?mac=4642652353&key=
# valid usage   ...py?mac=4642652353&key=*
# valid usage   ...py?mac=4642652353&key=UPV&key=UDW
# valid usage   ...py?mac=4642652353&key=UPV&key=UDW&tout=1000  # older values will not be listed inside json string


# Import modules for CGI handling 
import cgi, cgitb ,re
cgitb.enable() 
from sqlite3 import dbapi2 as sqlite3 
#import sqlite3 # ? 

#import time
#import datetime
#from pytz import timezone
#import pytz
#utc = pytz.utc
import traceback
import os

#aeg sekundites
#tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu
#today=time.strftime("%d.%m.%Y",time.localtime(float(tsnow)))

mac=''
macnum=0
keys=[]
key=''
tout=0

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac = form.getvalue('mac')

try:
    keys = form.getlist('key') # can be a list of multiple keys! always successful, even if empty []
    #keylist = ",".join(keys)  # comma separated list if needed
    if keys[0] == '': # this will fail if no members and then exception will give the needed result
        keys[0] = '*'
except:
    keys=[]
    keys.append('*') # a single member

#env muutuja HTTP_COOKIE sisaldab kasulikku infot kui paring labi nagiose serveri teha. 
try:
    USER=os.environ['HTTP_COOKIE'].split('=')[1].split(':')[0] # kasutaja eraldamine jargmisest infost, et saaks kontrollida kasutaja oigusi kysitud info suhtes
    #'itvilla_com=neeme:27:f64d55b0f00b13446324e4e2af901fa8; CookieAuth_Redirect=; CookieAuth_Reason='
except:
    pass # ajutine luba ! 
    #print 'Error: no username supplied! </body></html>'
    #print(os.environ)
    #exit()


# ###########  MAIN  ##################

# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print 

#print cmd, mon # ajutine proov
#print cmd

conn = sqlite3.connect('/srv/scada/sqlite/monitor')
cursor=conn.cursor()
cursor2=conn.cursor()

print "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd'>\n"
print "<html><head>\n"
print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'/>\n" 
#print "<meta http-equiv='refresh' content='3'/>\n"  # 3s tagant automaatne reload #####
	
print "</head>\n<body>"

  
#print 'keys',repr(keys) # debug

print('[{')  # begin with json 

cursor=conn.cursor()
conn.execute('BEGIN IMMEDIATE TRANSACTION') # alustame transaktsiooni, peaks parem olema...
found = 0

Cmd="select servicetable from controller where mac = '"+str(mac)+"'" # teenusetabel
cursor.execute(Cmd)
for row in cursor: # 
    servicetable=row[0] # servicetable name found
    
for key in keys:
    #print 'key',key  # debug
    value = '' # this will be used if empty or stalled
    if key == '*':
        registerdefine = "" # list everything
    else:
        registerdefine = " where sta_reg = '"+key+"' or val_reg = '"+key+"'" # otsitav info 

    Cmd="select sta_reg,val_reg,svc_name from "+servicetable+registerdefine # 
    #print('Cmd',Cmd) # debug
    cursor.execute(Cmd)
    for row in cursor: # koikide saadud key:val hulgast
        service = ''
        register = ''
        found = found + 1 # number of key:value  pairs found
        service = row[2] 
        if row[1] <>'': # value register exists
            register = row[1] # 
        else:
            register= row[0]
            
        if found>1: # add comma in the end of last
            print(',')
        print('\n "'+register+'" : "'+service+'"')
        
conn.commit() # transaktsiooni lopp

print('\n}]\n</body></html>\n')


