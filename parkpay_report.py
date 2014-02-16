#!/usr/bin/python
#REPORT TEHINGUTE KOHTA
#CREATE TABLE ViimaneTehing(mac,nagios_ip,status,value,timestamp, location);
#CREATE UNIQUE INDEX mac_ts on 'ViimaneTehing'(mac,timestamp);
# basen serveri tz on imelik, lisa 2h raporti aegadesse!

# Import modules for CGI handling
import cgi, cgitb, re, sys, traceback
#import pysqlite2
#from pysqlite2 import dbapi2 as sqlite3
import os
import sqlite3
import time
import datetime
#from pytz import timezone
import pytz
utc = pytz.utc
#aeg sekundites
#tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu


conn = sqlite3.connect('/srv/scada/sqlite/servicelog')
conn.text_factory = str # tapitahtede jama vastu

cursor=conn.cursor()

#http://212.47.221.86/conf/parkpay_report.py?date1=26.06.2011&date2=26.06.2011&mac=00204AB6503F&host=park1&status=9
#testimiseks anna ylaltoodud parameetrid
TEST='0' # 1 voi 0 normaalseks tooks

asuk='asuk_puudub'
location='loc_puudub'
host='host_puudub'
mac='00204AB6503F' # esimene proto
asukoht='teadmata' # proov
time1=0 # valikuaken alates s
time2=0 # valikuaken kuni s
status="" # edu lipp = TRS
tr_ts=0 # tehingu aeg s
tr_time="" # tehingu kellaaeg stringina
jama=0 # kuupaeva kontroll
summa=0 # tehingu summa
SUM=0 # raporti summa
autmnums='' # string!
eelmine_autnums=''

if TEST == '0': # normaalne too
    # Create instance of FieldStorage
    form = cgi.FieldStorage()

    # Get data from fields
    mac = form.getvalue('mac') # voiks olla ka raport yle koikide parkpay hostide? see filtreerib vaid yhe
    date1 = form.getvalue('date1') #sellest teha antud kuupaeva esimene sekund
    date2 = form.getvalue('date2')  # sellest teha antud kuupaeva viimane sekund
    status = form.getvalue('status') # tehingu staatuse alusel filter, 0 voi 2. koik annab tyhi status?
    host = form.getvalue('host') # displayname. las olla raportis nahtav
    #mon =  form.getvalue('mon')
else:
    date1='25.06.2011'  # testimiseks
    date2='25.06.2011'
    mac='00204AB6503F'
    host='park1'
    status='9'

#print "date1",date1,"date2",date2 # debug

# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print

os.environ['TZ'] ='Europe/Tallinn' # et tagada vastavus kohaliku ajaga
time.tzset()

try:
    time1=int(time.mktime(time.strptime(date1+' 00:00:00', '%d.%m.%Y %H:%M:%S')))
except:
    jama=1

try:
    time2=int(time.mktime(time.strptime(date2+' 23:59:60', '%d.%m.%Y %H:%M:%S')))
except:
    jama=1

#print "time1",time1,"time2",time2 # debug jaoks
if (time1 > time2 or date1 == None or date2 == None or jama>0):
    print "<h3>Valed kuup&auml;evad! </h3>"
    if date1 is None:
        date1='01.09.2013' # europark algus vana-viru 15 
        # date1=''
    if date2 is None:
        date2=''
    sys.exit()
if host is None:
    host='???'

print "<html><head></head><body>\n"
print "<h3> Parkimisautomaadi " +str(mac)+ " (" +str(host)+ ") tehingute raport </h3>\n"
print "<h4> Ajavahemik: " +date1+ " - " +date2+ ",   filter: "

if (status == '9' or status is None):
    print "k&otilde;ik tehingud detailselt"
else:
    if status == '0':
        print "edukad tehingud l&uuml;hidalt"
    else:
        print "tundmatu filter!"
        sys.exit()


if host != '???':
    Cmd="select timestamp,status,value from ViimaneTehing where mac = '"+str(mac)+"' and timestamp+0 >= "+str(time1)+" and timestamp+0 < "+str(time2)+" and location='"+host+"'"
else:
    Cmd="select timestamp,status,value from ViimaneTehing where mac = '"+str(mac)+"' and timestamp+0 >= "+str(time1)+" and timestamp+0 < "+str(time2)
    
# cmd olgu kogu aeg sama, sest salvestusnud status pole usaldusavaarne


print "</h4>\n" # , ajavahemik s "+str(time1)+" kuni "+str(time2)+"

cursor=conn.cursor()


try:
    cursor.execute(Cmd)
except:
    traceback.print_exc()  # ei naita midagi?
    print "<tr><td colspan='3'>debug cmd select ei onnestunud "+Cmd+"</td></tr>"

print "<table border='1'>\n<tr bgcolor='#cccccc'><th >Aeg</th><th>Autoriseerimisnumber</th>"
if status == '0':
    print "<th align='center'>Summa EUR</th></tr>"
else:
    print "<th align='center'>Tehingu sisu</th></tr>"
    
#print "<tr><td colspan='3'>debug cmd "+Cmd+"</td></tr>"

found=0
for row in cursor:
    #print "<tr><td colspan='3'> debug "+repr(row)+"</td></tr>" #debug
    found=1
    #andmete uurimine
    try:
        tr_time=time.strftime("%d.%m.%Y %H:%M:%S",time.localtime(float(row[0])))
        #actual_status=str(row[1]) # seda ei saa usaldada! leia parem stringi 'tehing teostatud' alusel!
        #print "<tr><td>debug "+tr_time+"</td><td colspan='2' align='center'>Aeg leitud: "+row[0]+" cmd "+Cmd+"</td></tr>" #debug
    except:
        traceback.print_exc()  # ei naita midagi?
        print "<tr><td>"+tr_time+"</td><td colspan='2' align='center'><b>Selle tehingu kohta puudub aeg! "+row[0]+"</b></td></tr>"
    else:
        if '|TEHING TEOSTATUD|' in row[2]: # edukas, summa leitav
            actual_status=0
            try:
                summa=float(row[2].split('|')[8].split('= ')[1].split(' ')[0]) # eraldada |Summa= 1.78| seest
                autnums=str(row[2].split('|')[6].split('= ')[1]) # |Autoris. nr= 949599 T1| STRING!
                SUM=SUM+summa
                #print "<tr><td>debug "+tr_time+"</td><td colspan='2' align='center'><b>summa ja autnum leitud: "+str(summa)+" "+autnums+"</b></td></tr>" #debug
            except:
                print "<tr><td>debug "+tr_time+"</td><td colspan='2' align='center'><b> ebaonnestuds summa voi autnums leidmine! "+str(summa)+" "+autnums+"</b></td></tr>" #debug
        else:
            actual_status=1 # midagi on viltu!
            autnums=''
            #print "<tr><td>debug "+tr_time+"</td><td colspan='2' align='center'><b>ebaonnestunud tehing: </b>"+row[2]+"</td></tr>" #debug

        # naitamine

        if status == '0': # naidata ainult onnestunud, lyhiformaadis
            if (autnums != '' and autnums != eelmine_autnums):
                print "<tr><td> "+tr_time+" </td><td align='center'>"+autnums+"</td><td align='right'>"+format("%0.2f" % summa)+"</td></tr>\n" # ainult summa

        else: # koik tehingud, summa naitame kui autnum olemas
            if (autnums != ''): # olemas autoriseerimine
                if autnums != eelmine_autnums:
                    print "<tr><td> "+tr_time+" </td><td align='center'>"+autnums+"</td><td align='center'>"+str(row[2])+"</td></tr>\n"

            else: 
                print "<tr><td>"+tr_time+"</td><td> &nbsp; </td><td align='center'>"+str(row[2])+"</td></tr>\n" # siin voib kordusi naidata kui erineval ajal!

        eelmine_autums=autnums # meelde

if found == 0:
    print "<tr><td colspan='3' align='center' bgcolor='#EEAAAA'>  Selles kuup&auml;evade vahemikus valitud filtri tingimusele vastavaid tehinguid ei leitud  </td></tr>"
else:
    print "<tr bgcolor='#dddddd'><td colspan='2' align='right'><b>Edukate tehingute summa</b></td><td align='right'><b>"+format("%0.2f" % SUM)+"</b></td></tr>"


print "</table><hr>"
print "</body></html>\n"

