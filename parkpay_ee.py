#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# eelmine rida voimaldab printida ka tapitahti pythonist! seda peaks tunnistama ka populaarsed editorid.
    
# viimane muudatus 24.01.2011 neeme
# extra host commands abil juhtimisnupud kontrollerile, cgi param cmd1...cmd4, kas toimib ka selgitus desc1..desc4?
# descX voib ka siin defineerida, aga see ei oleks hea
# hansab parkimise jaoks, samuti reboot ning valvesse ja valvest maha
# eraldi fail parkpay_log, seal sees tabel ViimaneTehing, kuid lisada voiks ka PaevaMyyk, mis peaks korjama viimase summa iga paeva KOHTA.
#  ESIALGU VOIB SINNA KOIK TEHINGUd SISSE PYYDA, HILJEM VAID VIIMANE. KOHE EI TEE!
#sqlite> .schema
#CREATE TABLE ViimaneTehing(mac,nagios_ip,status,value,timestamp, location);
#CREATE UNIQUE INDEX mac_ts on 'ViimaneTehing'(mac,timestamp);

# Import modules for CGI handling 
import cgi, cgitb ,re
from pysqlite2 import dbapi2 as sqlite3
import time
import datetime
#from pytz import timezone
import os
import pytz
utc = pytz.utc
#aeg sekundites
tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu
today=time.strftime("%d.%m.%Y",time.localtime(float(tsnow)))

cmd = [ 'sss', '', '', '', '' ] # cmdX array
desc = [ '', '', '', '' , '' ]  #selgitused cmd juurde

asuk='asuk_puudub'
location='loc_puudub'
host='host_puudub'
mac='mac_puudub'
filename='filename'
sadam="defineerimata" # proov
asukoht='teadmata' # proov
mon='type_puudub'
dis=' ' # dis="disabled='true'" selleks et nupud ei toimiks, kelamine allpool 

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
filename = form.getvalue('file')
mac =  form.getvalue('mac')
host = form.getvalue('host') # displayname
if host == 'park3':
    host='parkpay3' # nimed ei klapi nagioses ja kontrolleris, vajaks parandamist

cmd[0] =  form.getvalue('cmd1')
cmd[1] =  form.getvalue('cmd2')
cmd[2] =  form.getvalue('cmd3')
cmd[3] =  form.getvalue('cmd4')
cmd[4] =  form.getvalue('cmd5')

# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print 

#print cmd, mon # ajutine proov
#print cmd

conn = sqlite3.connect('/srv/scada/sqlite/monitor')
cursor=conn.cursor()

os.environ['TZ'] ='Europe/Tallinn' # et tagada vastavus kohaliku ajaga
time.tzset()

print "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd'>\n"
print "<html><head>\n	<script type='text/javascript' src='/calendar/scripts/jquery_v2.js'></script>\n"
print "<title>ParkPay Reports</title>\n" 

#		<!-- required plugins -->
print "  <script type='text/javascript' src='/calendar/scripts/date.js'></script>\n"
print "	<!--[if IE]><script type='text/javascript' src='/calendar/scripts/jquery.bgiframe.min.js'></script><![endif]-->\n"
print " <script type='text/javascript' src='/calendar/scripts/jquery.datePicker.js'></script>\n"
#		<!-- localisation-->
print " <script type='text/javascript' src='/calendar/scripts/date_et.js'></script>\n"
#		<!-- datePicker required styles -->
print " <link rel='stylesheet' type='text/css' media='screen' href='/calendar/styles/datePicker.css'>\n"
        
#<!-- page specific scripts -->
#print "<script type='text/javascript' charset='utf-8'>\n  $(function()\n    {\n	$('.date-pick').datePicker({autoFocusNextInput: true});\n  });\n"
# eelmine lubab vaid tulevikku valida, jargmine aga ainult minevikku
print "<script type='text/javascript' charset='utf-8'>\n  $(function()\n "
print "   {\n	$('.date-pick').datePicker({autoFocusNextInput: false, startDate: '01/01/2010', endDate: new Date().asString() });\n  });\n"
		
print "</script></head><body>"

print "<h3> Parkimisautomaadi " +str(mac)+ " (" +str(host)+ ") raportid ja kaughaldus </h3>" 

print "<br><hr>\n<h4>Raportid</h4>"  # siia kuupaeva valik lisada

print "<form name='input' action='parkpay_report.py' method='get'>\n" # kuidas mac kaasa panna? hidden input abil, vt allpool!

print "<table>"
print "<tr><td>Tehingud alates </td><td>Tehingud kuni (k.a.)</td><td>&nbsp;</td></tr>\n"
print "<tr><td>\n"
print "<input name='date1' id='date1'  value='01.09.2013' class='date-pick dp-applied'/></td><td><input name='date2' id='date2' value='"+str(today)+"' class='date-pick dp-applied'/></td>\n"
print "<td><input name='mac' value='"+str(mac)+"' id='mac' type='hidden'/><input name='host' value='"+str(host)+"' id='host' type='hidden'/>\n" #  teadaolevate muutujate edasiandmiseks

print "<select name='status'><option value='0'>&Otilde;nnestunud tehingud l&uuml;hidalt</option> <option value='9'>K&otilde;ik tehingud detailselt</option>"
#print "<option value='1'>Panga keeldumised detailselt</option><option value='2'>Eba&otilde;nnestunud piletitr&uuml;kkimised detailselt</option></select>\n"

print "<input type='submit' value='Koosta raport' />\n"	
print "</td></tr></table>\n"

print "</form><br><hr>\n"


cursor=conn.cursor()
cursor.execute('select MAX(timestamp) from state where mac = '+"'"+str(mac)+"'")
for row in cursor:
    last=int(float(row[0]))

if last < tsnow - 900:
    print "<br><br><span style=color:red><b>Side makseautomaadiga on katkenud, hetkel ei saa korraldusi saata!</b> Kontakteeru ITvillaga support@itvilla.ee</span>"
    dis="disabled='true'"
	
else:
    print "<br><span style=color:green><b>Side makseautomaadiga on korras.</b><br>Jargnevad kaugjuhtimistegevused aktiveeruvad minuti jooksul nupu klikkimisest.</span>"

print "<br><br>"


for i in range(len(cmd)):
#for  i in range(0,5): # labi kaib 0..4
    if cmd[i] <> None:
        #print " <input type='button' style='height:25px; width:100px' value="+cmd[i]+" onclick='this.disabled=true; location.href='http://receiver.itvilla.com/conf/cmd2controller.py?mac="+mac+"&cmd="+cmd[i]+"; return true;' >"
        print "<input "+dis+" type='button' style='height:25px; width:100px' value="+cmd[i]+" onclick=location.href='http://receiver.itvilla.com/conf/cmd2controller.py?mac="+mac+"&cmd="+cmd[i]+"' >"
		
        if cmd[i] == 'REBOOT':
            print "  kontrolleri restart"

        if cmd[i] == 'VARLIST':
            print "  uuendame muutujate nimekirja"

        if cmd[i] == 'ARM':
            print "  valvestamine"

        if cmd[i] == 'DISARM':
            print "  valvest maha"

        if cmd[i] == 'SAVE':
            print "  salvesta loendid"



        print "<br> "  #reavahetus


print "<br><br><hr>\n"

print "<br><br>Makseautomaadi juhtkontrolleri <A HREF=http://receiver.itvilla.com/conf/bn3setup.py?mac="+str(mac)+"&file="+filename+" > <b>seadistusparameetrid </b></A>"
print " - vajaduseta mitte muuta! <br>"

print "</body></html>\n"

