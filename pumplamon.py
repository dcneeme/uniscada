#!/usr/bin/python
# -*- coding: UTF-8 -*-# testime universaalset sisendinfopaneeli, mis oleks 100x kiirem, kui nagios
# pumplate versioon
# viimati muudetud 9.10.2013


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
mac =  form.getvalue('mac')
#env muutuja HTTP_COOKIE sisaldab kasulikku infot kui paring labi nagiose serveri teha. 
USER=os.environ['HTTP_COOKIE'].split('=')[1].split(':')[0] # kasutaja eraldamine jargmisest infost
#'itvilla_com=neeme:27:f64d55b0f00b13446324e4e2af901fa8; CookieAuth_Redirect=; CookieAuth_Reason='


#ENV=os.environ['USER'] # koik

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

if USER == '':
    print 'Error: no username supplied! </body></html>'
    exit()
    
    
print "<h2> Tsoonisignaalid pumplaobjektil "+mac+"</h2>\n" 


print "<table border='5'>\n"  # paneeli algus

service=['UDW','LVW','LHS','I1W','F1W','R1W','BRS','PWS','T1W'] # huvipakkuvad key:value vaartused
description=['ajad s, phone proxy usb pyapp','veetase mm, act min max','avariinivoo (aktiivne=2)','pumbavoolud mA, p1 p2 min max','pumbarikked (aktiivne=2), p1 p2','pumba too (aktiivne=1), p1 p2','sissetungimine (aktiivne=2)','toite kadu (aktiivne=2)','temperatuur ddegC, act min max']

#side andmebaasiga
cursor=conn.cursor()
conn.execute('BEGIN IMMEDIATE TRANSACTION') # alustame transaktsiooni, peaks parem olema...
Cmd="select register,value,timestamp from state where mac = '"+str(mac)+"' and timestamp+0>"+str(tsnow)+"-500" # viimane info kontrollerist
cursor.execute(Cmd) # 
for row in cursor: # koikide saadud key:val hulgast
    if row[0]<>'' and row[2]<>None and last < int(float(row[2])):
        last=int(float(row[2])) # leiame maksimumi koikide loetute hulgast
        if maxlast < last:
            maxlast=last

        if maxlast < tsnow - 500: # 500 s max lubatud vanus hiliseimale infole
            print "<tr><td colspan='3'><span style='color:red'>Side objektiga on katkenud, info on vananenud! Kasutaja "+USER+"</span></td></tr>\n"
            print "<tr><td colspan='3'>Hiliseim info "+str(last)+", praegu aeg "+str(tsnow)+", vanus "+str(tsnow-last)+"<td></tr>\n"
            print "<tr><td colspan='3'>SQL paring "+Cmd+"<td></tr>\n"
        
        else: # info varske

            #print "<td>\n<table border='5'>\n"  # mac paneeli algus
            print "<tr bgcolor='#aaaaaa'><td colspan='4'>Kasutaja "+USER+"</td></tr>" # esimene rida
            print "<tr><th>Teenus </th><th>Kood </th><th>Sisu</th><th>Vanus s</th></tr>" # esimene rida
            #state sisu lugemine ja tabeli joonistamine
            for rownum in range(len(service)): # 16 rida z01s kuni z16s
                #rown=rownum+1
                print "<tr><td>"+description[rownum]+"</td><td>"+service[rownum]+"</td>"
                #print "<tr><td>"+format("%02d" % rown)+"</td>"
                Cmd="select value,timestamp from state where mac = '"+str(mac)+"' and register = '"+service[rownum]+"'"
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
                            print "<td>"+sisu1+"</td><td>"+sisu2+"</td></tr>\n"
                        else:
                            print "<td>"+sisu1+"</td><td>"+sisu2+"</td></tr>\n"
                except:
                    print "<td colspan='2'>"+Cmd+"</td></tr>\n"
                    traceback.print_exc()

conn.commit() # transaktsiooni lopp

    
print "\n</table>\n<br>\n"  # lopetame tabeli

print "</body></html>\n"

