#!/usr/bin/python
# extra host commands abil juhtimisnupud kontrollerile, cgi param cmd1...cmd4, kas toimib ka selgitus desc1..desc4?
# descX voib ka siin defineerida, aga see ei oleks hea

# Import modules for CGI handling 
import cgi, cgitb ,re
from pysqlite2 import dbapi2 as sqlite3
import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc
#aeg sekundites
tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu

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

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac = form.getvalue('mac')
filename = form.getvalue('file')

cmd[0] =  form.getvalue('cmd1')
cmd[1] =  form.getvalue('cmd2')
cmd[2] =  form.getvalue('cmd3')
cmd[3] =  form.getvalue('cmd4')
cmd[4] =  form.getvalue('cmd5')

host = form.getvalue('host') # displayname
mon =  form.getvalue('mon')

# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print 

#print cmd, mon # ajutine proov

conn = sqlite3.connect('monitor')
cursor=conn.cursor()


print "<h3> Kontrolleri " +mac+ " (" +host+ ") kaugjuhtimine </h3>" 

#if mon == "sadam":
#    print "<h4>Sadam: "+sadam+" &nbsp;&nbsp; Asukoht: "+asukoht+"</h4>"

cursor=conn.cursor()
cursor.execute('select MAX(timestamp) from state where mac = '+"'"+str(mac)+"'")
for row in cursor:
    last=int(float(row[0]))

if last < tsnow - 1800:
    print "<span style=color:red><b>Monitooringuside kontrolleriga on katkenud, hetkel ei saa sellele kontrollerile korraldusi saata!</b> Kontakteeru ITvillaga support@itvilla.ee</span>"

else:
    print "<span style=color:green>Monitooringuside kontrolleriga korras. Jargnevad valikud aktiveeruvad kuni 5 minuti jooksul nupu klikkimisest.</span>"

print "<br><br>"



for i in range(len(cmd)):
    if cmd[i] <> None:
        print " <input type='button' style='height:25px; width:100px' value="+cmd[i]+" onclick=location.href='http://46.183.73.35/conf/cmd2controller.py?mac="+mac+"&cmd="+cmd[i]+"' >"

        if cmd[i] == 'REBOOT':
            print "  kontrolleri restart"

        if cmd[i] == 'VARLIST':
            print "  uuendame muutujate nimekirja"

        if cmd[i] == 'PERIPH':
            print "  terminaali perifeeriaseadmete restart"

        if cmd[i] == 'IT_TEST1':
            print "  testread infotabloole, jooksev rida 2"

        if cmd[i] == 'IT_TEST2':
            print "  testread infotabloole, jooksev rida 1"

        if cmd[i] == 'WLAN_RESET':
            print "  PDA raadioyhenduse restart"

        if cmd[i] == 'SW_RESET':
            print "  optilise switchi restart"

        if cmd[i] == 'SIGN1TEST':
            print "  keelumark rajale 1 (serveri kaudu)"

        if cmd[i] == 'SIGN2TEST':
            print "  keelumark rajale 3 (serveri kaudu)"

        if cmd[i] == 'SIGN3TEST':
            print "  keelumark rajale 3 (serveri kaudu)"

        if cmd[i] == 'NT_TEST':
            print "  numbritabloo test 0..8"

        if cmd[i] == 'REGIST':
            print "  registreerumine rajale (serveris)"



        print "<br> "  #reavahetus


print "<br><br>Kontrolleri <A HREF=http://46.183.73.35/conf/bn3setup.py?mac="+mac+"&file="+filename+" > seadistusparameetrid </A>"
print " - vajaduseta mitte muuta! <br>"

