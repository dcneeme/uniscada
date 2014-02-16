#!/usr/bin/python
# -*- coding: UTF-8 -*-
# pumplate versioon, tagastab json info io_muutujad.html asemel
# viimati muudetud 20.10.2013


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
tsnow = int(time.mktime(datetime.datetime.now().timetuple())) #sekundid praegu
today=time.strftime("%d.%m.%Y",time.localtime(float(tsnow)))


mac=''
macnum=0
regval={} # siia key:value paarid
#teha lisaks muutuja, mis sisaldab hiliseimat timestampi. kui see muutub, voib beebilehel uuenduse lambike vilgatada. 
last=0 # viimase key:value serverisse saabumise ts

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac =  form.getvalue('mac')



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

#koigepealt peaks koik varsked selle mac muutujad sisse lugema key:value masiivina {}
# siis peaks template sisu asendama, nime asemele vaartus. templates tuleb anda muutuja jrk multivalue puhul, komaga eraldada

# multiline comment '''
'''
[ { "name": "&LBAS(1,"%fs",NAME$);", 
    "id": "&LBAS(1,"%fs",mac$);", 
    "state": "&LBAS(1,"%fs",STATE$);", 
    "substate": "&LBAS(1,"%fs",SUBST$);", 
    "pump1state": "&LBAS(1,"%u",psta(1));", 
    "pump2state": "&LBAS(1,"%u",psta(2));", 
    "pump1failure": "&LBAS(1,"%u",PFAI(1));", 
    "pump2failure": "&LBAS(1,"%u",PFAI(2));", 
    "level1": "&LIO(1,"%u",877);", 
    "level2": "&LIO(1,"%u",878);",
    "level3": "&LIO(1,"%u",879);",
    "levelXY": "&LIO(1,"%u",875);",
    "depth": "&LIO(1,"%u",881);",
    "alertdepth": "&LIO(1,"%u",880);",
    "heat_level": "&LIO(1,"%u",870);",
    "norm_level": "&LIO(1,"%u",871);",
    "leak_level": "&LIO(1,"%u",872);",
    "fb2_level": "&LIO(1,"%u",873);",
    "fb2_code": "&LIO(1,"%u",874);",
    "loadAVG": "&LBAS(1,"%u",PLOAD(0));",
    "load1AVG": "&LBAS(1,"%u",PLOAD(1));",
    "load2AVG": "&LBAS(1,"%u",PLOAD(2));",
    "count1": "&LBAS(1,"%lu",count(0));",
    "count2": "&LBAS(1,"%lu",count(1));",
    "tootlikkus": "&LBAS(1,"%u",Psec(6)); l/s",
    "kogus": "&LBAS(1,"%lu",Psec(5)); m3",
    "kulukogus": "&LBAS(1,"%fs",mbd$);",
    "uptime": "&LBAS(1,"%u",UP(3));d &LBAS(1,"%u",UP(2));h &LBAS(1,"%u",UP(1));min",
    "bin_in5": "&LIO(1,"%u",205);",
    "R1S": "&LIO(1,"%u",922);",
    "F1S": "&LIO(1,"%u",905);",
    "F1V" : "&LBAS(1,"%s",F1V$); ",
    "R2S": "&LIO(1,"%u",923);",
    "F2S": "&LIO(1,"%u",906);",
    "F2V" : "&LBAS(1,"%s",F2V$); "
    } ]
'''        
# 1382281199
#select register,value,timestamp from state where mac = '00204ADEA724' and timestamp+0>1382281199-500;
       
#side andmebaasiga
cursor=conn.cursor()
conn.execute('BEGIN IMMEDIATE TRANSACTION') # alustame transaktsiooni, peaks parem olema...
Cmd="select register,value,timestamp from state where mac = '"+str(mac)+"' and timestamp+0>"+str(tsnow)+"-500" # viimane info kontrollerist
cursor.execute(Cmd) # 
for row in cursor: # koikide saadud key:val hulgast
    if row[0]<>'' and row[2]<>None and last < int(float(row[2])):
        last=int(float(row[2])) # leiame maksimumi koikide loetute hulgast

    #json ridade jarjekord pole oluline, valjastame nii, nagu sql lugemine tulemuse andis
    #aga alustada voiks last infoga
    print "[ { 'last': "+str(last)"
    if row[0] == 'id': # mac
        print " 'id' : "+row[1]
    if row[0] == 'S100': # nimetus
        print " 'name' : "+row[1]
    if row[0] == 'R1W': # pump state multivalue
        print " 'pump1state' : "+row[1].split(':').[0]+"\n 'pump2state' : "+row[1].split(':').[1]
    if row[0] == 'R1S': # pump 1 state
        print " 'pump1state' : "+row[1] 
    if row[0] == 'R2S': # pump 2 state
        print " 'pump2state' : "+row[1]
    if row[0] == 'F1W': # pump failure multivalue
        print " 'pump1failure' : "+row[1].split(':').[0]+"\n 'pump2failure' : "+row[1].split(':').[1]
    if row[0] == 'R1S': # pump 1 failure
        print " 'pump1failure' : "+row[1] 
    if row[0] == 'R2S': # pump 2 failure
        print " 'pump2failure' : "+row[1]
    if row[0] == 'LVW': # water levels multivalue
        print " 'levelXY' : "+row[1].split(':').[0]+"\n 'level1' : "+row[1].split(':').[1]+"\n 'level2' : "+row[1].split(':').[2]
    if row[0] == 'LVV': # single value water level
        print " 'levelXY' : "+row[1]
    if row[0] == 'I1W': # pump current multivalue
        print " 'pump1current' : "+row[1].split(':').[0]+"\n 'pump2current' : "+row[1].split(':').[1]]+"\n 'pumpcurrentlo' : "+row[1].split(':').[2]]+"\n 'pumpcurrenthi' : "+row[1].split(':').[3]
    if row[0] == 'I1V': # pump 1 current single value
        print " 'pump1current' : "+row[1]    
    if row[0] == 'I2V': # pump 2 current single value
        print " 'pump2current' : "+row[1]
    if row[0] == 'BTW': # battery voltage multivalue
        print " 'batt_volt' : "+row[1].split(':').[0]+"\n 'batt_volt_lo' : "+row[1].split(':').[1]]+"\n 'batt_volt_hi' : "+row[1].split(':').[2]]
    if row[0] == 'BTV': # batt voltage single value
        print " 'batt_volt' : "+row[1]        
    
    if row[0] == 'LHS': # flooding signal
        print " 'bin_in5' : "+row[1]
    if row[0] == 'APS': # overvoltage 
        print " 'bin_in6' : "+row[1]
    if row[0] == 'BRS': # door open 
        print " 'bin_in7' : "+row[1]
    if row[0] == 'PWS': # ac power loss
        print " 'bin_in8' : "+row[1]
    
    if row[0] == 'S1W': # pump worktime s multivalue
        print " 'count1' : "+row[1].split(':').[0]+"\n 'count2' : "+row[1].split(':').[1]]
    if row[0] == 'P1W': # pump average load % multivalue
        print " 'load1AVG' : "+row[1].split(':').[0]+"\n 'load2AVG' : "+row[1].split(':').[1]]
        
    #vaja saata ka state ning substate. ei edasta praegu? vahemalt empty signaali on vaja. pumba vool oleks ka hea teada.
    # voi siis msd, et mingit txt saata. 
    if row[0] == 'msd': # description, any text to describe the state
        print " 'desc' : "+row[1]
   

print " } ]"  # lopetame json

conn.commit() # transaktsiooni lopp

print "</body></html>\n"

