#!/usr/bin/python
# -*- coding: UTF-8 -*-# testime universaalset sisendinfopaneeli, mis oleks 100x kiirem, kui nagios

# Import modules for CGI handling 
import cgi, cgitb ,re
cgitb.enable() # neeme lisas 21.01.2012

#from pysqlite2 import dbapi2 as sqlite3
from sqlite3 import dbapi2 as sqlite3 

import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc
import traceback

#aeg sekundites
tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu
today=time.strftime("%d.%m.%Y",time.localtime(float(tsnow)))


macs=['00204AE98FF3','00204ADEA9DA'] # metaprint1
mac=''
macnum=0

last=0 # viimase saatmise ts

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
#mac =  form.getvalue('mac')



# ###########  MAIN  ##################

# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print 

#print cmd, mon # ajutine proov
#print cmd

conn = sqlite3.connect('/srv/scada/sqlite/monitor')
cursor=conn.cursor()

print "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd'>\n"
print "<html><head>\n"
print "<style media='screen' type='text/css'> body {background-color:#ffffff; font-family: arial; font-size: 75%; } table { font-family: arial;} </style>" 
# kui fffff nagu nagiosel siis firefox ei vilgu. chrome ja ie vilguvad ikka, ajax vaja vist...
print "<title>OlekuPaneel</title>\n"
print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'/>\n" # <meta http-equiv="refresh" content="1" />
print "<meta http-equiv='refresh' content='3'/>\n"  # 3s tagant automaatne reload #####
	
print "</head>\n<body>"

print "<h2> Tsoonisignaalid Metaprint objektil</h2>\n" 

print "<table border='0'>\n"  # paneeli algus


#side andmebaasiga
cursor=conn.cursor()
conn.execute('BEGIN IMMEDIATE TRANSACTION') # alustame transaktsiooni, peaks parem olema...
for macnum in range(len(macs)): # koikide mac tabelid korvuti
    mac=macs[macnum]
    Cmd="select MAX(timestamp) from state where mac = '"+str(mac)+"'"
    cursor.execute(Cmd) # side korrasoleku kontroll
    for row in cursor:
        if row[0]<>'' and row[0]<>None:
            last=int(float(row[0]))

        if last < tsnow - 500: # 500 s max lubatud vanus hiliseimale infole
            print "<tr><td colspan='3'><span style='color:red'>Side objektiga on katkenud, info on vananenud!</span></td></tr>\n"
            print "<tr><td colspan='3'>Hiliseim info "+str(last)+", praegu aeg "+str(tsnow)+", vanus "+str(tsnow-last)+"<td></tr>\n"
            print "<tr><td colspan='3'>SQL paring "+Cmd+"<td></tr>\n"
        
    else: # info varske

        print "<td>\n<table border='10'>\n"  # mac paneeli algus
        print "<tr><td colspan='3'>Kontroller "+mac+"</td></tr>" # esimene rida
        print "<tr><td>Tsoon </td><td>Olek</td><td>Oleku vanus s</td></tr>" # esimene rida
        #state sisu lugemine ja tabeli joonistamine
        for rownum in range(16): # 16 rida z01s kuni z16s
            rown=rownum+1
            print "<tr><td>"+format("%02d" % rown)+"</td>"
            Cmd="select value,timestamp from state where mac = '"+str(mac)+"' and register = 'Z"+format("%02d" % rown)+"S'"
            #print Cmd
            try:
                cursor.execute(Cmd) # tsoonide Z00-Z15 olek
                for row in cursor: # saame yhe vastuserea kui yldse midagi, sest yks unikaalne olek
                    sisu1=str(row[0]) # olek, voib ka tyhi olla
                    if row[1]<>'':
                        sisu2=str(tsnow-int(float(row[1]))) # oleku vanus
                    else:
                        sisu2=''
                        
                    if sisu1<>0 and sisu1<>'0':
                        print "<td><b>"+sisu1+"</b></td><td>"+sisu2+"</td></tr>\n"
                    else:
                        print "<td>"+sisu1+"</td><td>"+sisu2+"</td></tr>\n"
            except:
                print "<td colspan='2'>"+Cmd+"</td></tr>\n"
                traceback.print_exc()
    print "\n</table>\n<br>\n"  # lopetame osatabeli

conn.commit() # transaktsiooni lopp

    
print "\n</table>\n<br>\n"  # lopetame tabeli

print "</body></html>\n"

