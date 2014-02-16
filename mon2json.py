#!/usr/bin/python
# -*- coding: UTF-8 -*-# 
# outputs key:values from sql database as simple json. required parameters are mac (object id) and key_list (array of services

# Import modules for CGI handling 
import cgi, cgitb ,re
cgitb.enable() # neeme lisas 21.01.2012

from sqlite3 import dbapi2 as sqlite3 
#import sqlite3 # ? 

import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc
import traceback
import os

#aeg sekundites
tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu
today=time.strftime("%d.%m.%Y",time.localtime(float(tsnow)))


#macs=['00204AE98FF3','00204ADEA9DA'] # 
mac=''
macnum=0

last=0 # viimase saatmise ts

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac = form.getvalue('mac')
tout = int(float(form.getvalue('tout'))) # max allowed value age in seconds. if value is older, return N/A. if tout=0, no age based filtering occurs.
keylist = form.getlist('key') # can be a list of multiple keys!
keys = ",".join(keylist)  # service keys to be used in response

maxlast=0
#env muutuja HTTP_COOKIE sisaldab kasulikku infot kui paring labi nagiose serveri teha. 
USER=os.environ['HTTP_COOKIE'].split('=')[1].split(':')[0] # kasutaja eraldamine jargmisest infost
#'itvilla_com=neeme:27:f64d55b0f00b13446324e4e2af901fa8; CookieAuth_Redirect=; CookieAuth_Reason='



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
print "<style media='screen' type='text/css'> body {background-color:#ffffff; font-family: arial; font-size: 75%; } table { font-family: arial;} </style>" 
# kui fffff nagu nagiosel siis firefox ei vilgu. chrome ja ie vilguvad ikka, ajax vaja vist...
print "<title>Value Data</title>\n"
print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'/>\n" # <meta http-equiv="refresh" content="1" />
print "<meta http-equiv='refresh' content='3'/>\n"  # 3s tagant automaatne reload #####
	
print "</head>\n<body>"

if USER == '':
    print 'Error: no username supplied! </body></html>'
    exit()
    
    
print "<h2> Signaalid objektilt "+mac+", key = "+key+"</h2>\n" 


print "<table border='5'>\n"  # paneeli algus
print "<tr bgcolor='#aaaaaa'><td colspan='4'>Kasutaja "+USER+"</td></tr>" # esimene rida
print "<tr><th>Teenus</th><th>Kood </th><th>Sisu</th><th>Vanus s</th></tr>" # teine rida

print "[ { "name": "  # begin with json 

cursor=conn.cursor()
conn.execute('BEGIN IMMEDIATE TRANSACTION') # alustame transaktsiooni, peaks parem olema...

for key in keys:
    if tout <= 0:
        Cmd="select value,timestamp from state where mac = '"+str(mac)+"' and register="+key # otsitav info 
    else:
        Cmd="select value,timestamp from state where mac = '"+str(mac)+"' and register="+key+"' and timestamp+0>"+str(tsnow)+"-"+str(tout) # otsitav info 
            
    cursor.execute(Cmd)
    for row in cursor: # koikide saadud key:val hulgast
        if row[0]<>'' and row[2]<>None:
            value = row[0] # should be string
            #last=int(float(row[1])) # leiame maksimumi koikide loetute hulgast
    
    print "<tr><td>"+key+"</td><td>"+value+"</td></tr>\n"
    # voiks ka service infot lugeda ja naidata
            
conn.commit() # transaktsiooni lopp

    
print "\n</table>\n<br>\n"  # lopetame tabeli

print "</body></html>\n"

