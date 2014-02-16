#!/usr/bin/python
# -*- coding: UTF-8 -*-

# parkpay_ee eeskujul jan2012 neeme
# # raporteid esialgu ei kasuta

# Import modules for CGI handling 
import cgi, cgitb ,re
cgitb.enable() # neeme lisas 21.01.2012

from pysqlite2 import dbapi2 as sqlite3
import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc
#aeg sekundites
tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu
today=time.strftime("%d.%m.%Y",time.localtime(float(tsnow)))

cmd = [ 'sss', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '' , '', '', '', '', '', '' , '', '', '', '', '', '' ] # cmdX array
desc = [ '', '', '', '' , '' , '', '', '', '', '', '', '', '', '', '', '', '', '', '' , '', '', '', '', '', '' , '', '', '', '', '', '' ]  #selgitused cmd juurde

asuk='asuk_puudub'
location='loc_puudub'
host='host_puudub'
mac='mac_puudub'
filename='filename'
mon='type_puudub'
dis=' ' # dis="disabled='true'" selleks et nupud ei toimiks, keelamine allpool 

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
filename1 = form.getvalue('file1')
filename2 = form.getvalue('file2')
mac =  form.getvalue('mac')
host = form.getvalue('host') # displayname
cmd[0] =  form.getvalue('cmd1')
cmd[1] =  form.getvalue('cmd2')
cmd[2] =  form.getvalue('cmd3')
cmd[3] =  form.getvalue('cmd4')
cmd[4] =  form.getvalue('cmd5')
cmd[5] =  form.getvalue('cmd6')
cmd[6] =  form.getvalue('cmd7')
cmd[7] =  form.getvalue('cmd8')
cmd[8] =  form.getvalue('cmd9')
cmd[9] =  form.getvalue('cmd10')
cmd[10] =  form.getvalue('cmd11')
cmd[11] =  form.getvalue('cmd12')
cmd[12] =  form.getvalue('cmd13')
cmd[13] =  form.getvalue('cmd14')
cmd[14] =  form.getvalue('cmd15')
cmd[15] =  form.getvalue('cmd16')
cmd[16] =  form.getvalue('cmd17')
cmd[17] =  form.getvalue('cmd18')
cmd[18] =  form.getvalue('cmd19')
cmd[19] =  form.getvalue('cmd20')
cmd[20] =  form.getvalue('cmd21')
cmd[21] =  form.getvalue('cmd22')
cmd[22] =  form.getvalue('cmd23')
cmd[23] =  form.getvalue('cmd24')
cmd[24] =  form.getvalue('cmd25')
cmd[25] =  form.getvalue('cmd26')

#lisa kui vaheks jaab, ka eespool cmd ja desc masiividele liikmeid!

# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print 

#print cmd, mon # ajutine proov
#print cmd

conn = sqlite3.connect('/srv/scada/sqlite/monitor')
cursor=conn.cursor()

print "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd'>\n"
print "<html><head>\n	<script type='text/javascript' src='/calendar/scripts/jquery_v2.js'></script>\n"
print "<style media='screen' type='text/css'> body {background-color:#dddddd; font-family: arial; font-size: 75%; } table { font-family: arial;} </style>" # font ilusamaks
print "<title>KaughaldusVarpo</title>\n"
print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'>\n" 

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

print "<h2> Hooneautomaatika " +str(mac)+ " (" +str(host)+ ") raportid ja manuaalne kaughaldus </h2>" 

print "<br><hr>\n<h3>Raportid</h3>"  # siin ka kuupaeva valik

print "<form name='input' action='parkpay_report.py' method='get'>\n" # kuidas mac kaasa panna? hidden input abil, vt allpool!

print "<table>"
print "<tr><td>Raport alates </td><td>  kuni (k.a.)</td><td>&nbsp;</td></tr>\n"
print "<tr><td>\n"
print "<input name='date1' id='date1' class='date-pick dp-applied'/></td><td><input name='date2' id='date2' value='"+str(today)+"' class='date-pick dp-applied'/></td>\n"
print "<td><input name='mac' value='"+str(mac)+"' id='mac' type='hidden'/><input name='host' value='"+str(host)+"' id='host' type='hidden'/>\n" #  teadaolevate muutujate edasiandmiseks

print "<select name='report'><option value='1'> variant 1</option><option value='2'> variant 2 </option>"
print "<option value='4'> variant 3</option><option value='4'> variant 4</option></select>\n"

print "<input type='submit' style='background-color:#99ff99;' value='Koosta raport' />\n"	
print "</td></tr></table>\n"

print "</form><br><hr>\n"


cursor=conn.cursor()
cursor.execute('select MAX(timestamp) from state where mac = '+"'"+str(mac)+"'")
for row in cursor:
    last=int(float(row[0]))


print "<br><br>\n"


print "<table>\n"  # nuputabeli algus, nuppude jarjekord soltub parameetrite saatmise jarjekorrast nagiose poolt!
if last < tsnow - 900:
    print "<tr><td colspan='6'><span style='color:red'><b>Side objektiga on katkenud, hetkel ei saa korraldusi saata!</b> Kontakteeru ITvillaga support@itvilla.ee</span></td></tr>\n"
    dis="disabled='true'"
	
else:
    print "<tr><td colspan='6'><span style='color:green'><b>Side objektiga on korras. </span> Allpool loetletud kaugjuhtimistegevused aktiveeruvad minuti jooksul vastava nupu klikkimisest. Tulemust kontrolli monitooringu kaudu.</td></tr>\n"

    
    
for i in range(len(cmd)):
    if (cmd[i] <> None and cmd[i] <> ''):
        if i%2 == 0: # jagub kahega, esimene tulp 
            print "<tr>\n" 
            
        print "<td><input "+dis+" type='button' style='height:25px; width:100px; background-color:yellow;' value="+cmd[i]+" onclick=location.href='http://46.183.73.35/conf/cmd2controller.py?mac="+mac+"&cmd="+cmd[i]+"' ></td>"
        
        print "<td bgcolor='#eeeeee'> " # selgitustekstid
        
        if cmd[i] == 'REBOOT':
            print "  <span style='color:blue'> juhtimis- ja monitooringukontrolleri restart</span>"

        if cmd[i] == 'VARLIST':
            print "  <span style='color:blue'> uuenda seadistuslehe muutujaid (kui osa neist on tühjad)</span>"

        if cmd[i] == 'HPRESET':
            print "  <span style='color:blue'> soojuspumba reset tema kontrolleri toitekatkestuse kaudu</span>"

        if cmd[i] == 'P1OFF':
            print "  <span style='color:red'> soojuspumba väljundis küttetsirkulatsiooni peatamine</span>"

        if cmd[i] == 'P1ON':
            print "  <span style='color:red'> soojuspumba väljundis pidev küttetsirkulatsioon</span>"

        if cmd[i] == 'P2OFF':
            print "  <span style='color:red'> soojuspumba väljundis tarbeveetsirkulatsiooni peatamine</span>"
        
        if cmd[i] == 'P2ON':
            print "  <span style='color:red'> soojuspumba väljundis pidev tarbeveetsirkulatsioon</span>"

        if cmd[i] == 'VENTMAX':
            print "  <span style='color:red'> katuseventilaatorite kiirus pidevalt maksimaalne</span>"
        
        if cmd[i] == 'VENTMIN':
            print "  <span style='color:red'> katuseventilaatorite kiirus pidevalt minimaalne</span>"
        
        if cmd[i] == 'P1AUTO':
            print "  <span style='color:green'> soojuspumba väljundis küttetsirkulatsiooni automaatne juhtimine</span>"

        if cmd[i] == 'P2AUTO':
            print "  <span style='color:green'> soojuspumba väljundis tarbeveetsirkulatsiooni automaatne juhtimine</span>"
        
        if cmd[i] == 'VENTAUTO':
            print "  <span style='color:green'> katuseventilaatorite kiiruse automaatne juhtimine</span>"

        if cmd[i] == 'ALLAUTO':
            print " <span style='color:green'> kõikide juhtimissignaalide automaatne reeglipõhine koostamine</span>"
            
        if cmd[i] == 'HEATOFF':
            print "  <span style='color:red'> kütte väljalülitus (välistemperatuuri anduri kuumutamise kaudu)</span>"
            
        if cmd[i] == 'HEATON':
            print "  <span style='color:green'> kütte automaatjuhtimine välistemperatuuri anduri alusel (ilmaennustust ei kasutata)</span>"
        
        if cmd[i] == 'HEATFORE':
            print "  <span style='color:green'> kütte automaatjuhtimine välistemperatuuri ja <b>ilmaennustuse</b> alusel</span>"
        
        if cmd[i] == 'FORETEST':
            print "  <span style='color:magenta'> ilmaennustuse alusel küttejuhtimise test (saabuva soojalaine simulatsioon)</span>"
        
        if cmd[i] == 'HPOFF':
            print "  <span style='color:red'> soojuspump pidevalt väljas - kasuta ainult vajadusel!</span>"
        
        if cmd[i] == 'HPRUN':
            print "  <span style='color:red'> soojuspump pidevalt sees - kasuta ainult testimiseks!</span>"
        
        if cmd[i] == 'HPAUTO1':
            print "  <span style='color:green'> soojuspumba automaatjuhtimine sekundaarringi temperatuuri alusel</span>"
        
        if cmd[i] == 'HPAUTO2':
            print "  <span style='color:green'> soojuspumba automaatjuhtimine küttevajaduse ja boileri laetuse alusel</span>"
            
        if cmd[i] == 'CLEAR':
            print "  <span style='color:magenta; background-color:#eeeeee;'> kustuta ootel korraldus</span>"
      
        print "</td><td>&nbsp;</td>"  
        
        if i%2 == 1: #ei jagu kahega, teine tulp 
            print "</tr>\n"  # lopetame rea
            
if i%2 == 0: #nupud otsas aga viimase index ei jagunud kahega, seega esimene tulp pooleli 
    print "<td></td><td></td><td>&nbsp;</td>" # puuduv tulp

print "</tr>\n</table>\n<br><hr>\n"  # lopetame tabeli

print "<br><A HREF=http://46.183.73.35/conf/bn3setup1.py?mac="+str(mac)+"&file="+filename1+" > <b>Süsteemi ülesehitust kajastavad seadistusparameetrid </b></A>"
print " juhtkontrolleris - vajaduseta mitte muuta! <b>Seadistusleht ilmub aeglaselt.</b><br>"

print "<br><A HREF=http://46.183.73.35/conf/bn3setup2.py?mac="+str(mac)+"&file="+filename2+" > <b>Automaatjuhtimise reegleid kajastavad seadistusparameetrid </b></A>"
print " juhtkontrolleris  - vajaduseta mitte muuta! <b>Seadistusleht ilmub aeglaselt.</b><br>"

print "</body></html>\n"

