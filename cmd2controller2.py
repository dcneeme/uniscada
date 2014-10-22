#!/usr/bin/python
# neeme 9.2.2013 / cmd2controller alusel newstate tabelisse kirjutamine, paindlikum kui ainult cmd saatmine, saab kasutada reg=&val= endise cmd= asemel!

# reboot controller from within nagios as reaction to button ONCLICK
# seda kaivitab buttons.py, parameetriteks mac ja cmd

# Import modules for CGI handling 

import cgi, cgitb, re
cgitb.enable() # neeme lisas 21.01.2012

#from pysqlite2 import dbapi2 as sqlite3
import sqlite3 
conn = sqlite3.connect('/srv/scada/sqlite/monitor',2)
cursor=conn.cursor()

import sys
import traceback
import subprocess
import string

#esialgsed vaartused cli testimiseks
mac='00204AB81729'
cmd=''
reg='' # siin selline vaartus kui reg ja val ei anta
val='' # siia asemele tegelik cmd kui see antakse
register=''
value='' # kontrollmuutujad

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac = form.getvalue('mac') # kui vaartust ei tule, paneb None!
cmd = form.getvalue('cmd')
reg = form.getvalue('reg')
val = form.getvalue('val')
# olgu universaalne, kas cmd= voi siis reg=& val=


# kui siin kommentaar, naed sorcu
print "Content-type: text/html\n" # siin ei tohi reavahetust unustada
print "<html><head>\n"
print "<script type='text/javascript'> function goBack(){history.go(-1);} </script>\n" # miks ei toimi?
print "</head>\n" # et ise tagasi laheks sinna kust tuli
print "<body onLoad='setTimeout('goBack()', 2000); >\n"


if cmd == 'CLEAR': #kustutme KOIK ootel reg:val teated sellele kontrollerile, reg ja val pole vajalik!
    sqlcmd="delete from newstate where mac='"+mac+"'" # koik maha mis ootel
    conn.execute(sqlcmd) 
    try:
        conn.commit()
        print "<p><span style='color:green; font-size:36px;'><b>Ootel korraldused kustutatud!</b></span> <br><br> <FORM><INPUT TYPE='button' style='font-size:36px;' VALUE='Tagasi' onClick='history.go(-1);return true;'/></FORM> <br>"
    except:
        traceback.print_exc()
        print "<p><span style='color:red; font-size:36px;'><b>Kustutamine eba&otilde;nnestus...</b></span> <br><br> <FORM><INPUT TYPE='button' style='font-size:36px;' VALUE='Tagasi' onClick='history.go(-1);return true;'/></FORM> <br>"
else: # siin vaja reg ja val
    if cmd<>None and reg == None and val== None: # mingi cmd
        register='cmd'
        value=cmd
    if cmd == None and reg<>None and val<>None: # mingi cmd
        register=reg
        value=val.replace('_',' ') # alakriipsude asemel tyhikud, tyhikuid ei saanud url peal edasi anda
        sqlcmd="insert into newstate(mac,register,value) values('"+mac+"','"+register+"','"+value+"')" #  register ja value, ei pea olema cmd
        register=reg
        
        
    if register<>'' and value<>'':  # tundub korras
        #print sqlcmd,"<br><br>"
        #print "<p>saadetav korraldus: ",register,value
        korrnum=0 # ootel korralduste loendi

        try:
            conn.execute(sqlcmd) 
            conn.commit()
            print("<p><span style='font-size: 150%; color:green'><b>Korraldus salvestatud, reaktsioon avaldub m&otilde;ne sekundi p&auml;rast.</b>\n")
            print("<br><br> <FORM><INPUT TYPE='button' style='font-size:36px;' VALUE='Tagasi' onClick='history.go(-1);return true;'/></FORM> <br></span>")

        except:
            traceback.print_exc() # inserti ei onnestunud
            sqlcmd="select register,value from newstate where mac='"+mac+"'"
            cursor.execute(sqlcmd) 
            conn.commit()
            for line in cursor:
                korrnum=korrnum+1
                if korrnum == 1:
                    print "<p>ootel korraldused: "
                print "<p>",line[0],line[1]
                
            if korrnum>0:
                print "<p><span style='color:red; font-size:36px;'><b>Eelmine samalaadne korraldus sellele objektile on juba ootel, saatmine ei &otilde;nnestunud.</b><br></span>"
                print "Proovi hiljem uuesti v&otilde;i kustuta ootel korraldused eelmisel lehel.<br><br>"
            else:
                print "<p><span style='color:red; font-size:36px;'><b>Tekkis korralduse salvestamise viga, informeeri rakenduse hooldajat.</b></span><br><br>"
            print "<br> <FORM><INPUT TYPE='button' style='font-size:36px;' VALUE='Tagasi' onClick='history.go(-1);return true;'/></FORM> <br>"            
            
    else: # ei ole korrektne korraldus
        print "Ebakorrektne korraldus, parameetrid cmd="+str(cmd)+", reg="+str(reg)+", val="+str(val)+", register="+register+", value="+value+"<br><br>"
        print "<br> <FORM><INPUT TYPE='button' style='font-size:36px;' VALUE='Tagasi' onClick='history.go(-1);return true;'/></FORM> <br>"
    
# body jms lopetamised?
print "</body></html>\n"

