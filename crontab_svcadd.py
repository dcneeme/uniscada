#!/usr/bin/python

# par1 0...4  aasta kuu nadal paev tund
# par2 filter kui koike ei taha, teenuse nimi, ntx UTW


# crontab kaivitab parameetriga 0..4, salvestab perioodide algseisud vastavalt svcadd sisule teenustesse XX0..XX4, y,m,w,d,h 
#ka status on vajalik, muidu ei saadeta vastavat teenust naguiosele., salvestame sinnagi 0, vahemalt esialgu.
# 24.04.2013 timestamp ka vaja salvestada, muidu ei tea millal viimane algseis salvestati.
# 11.05.2013 lisame ka bn jaoks UTW nullistamise newstate kaudu iga kuu alguses, cron seal hasti ei toimi (nullistamine jaab tihti vahele)
# 11.05.2013 algseisude uuendamist pole vaja kui vastava parameetri jaoks uus teenus puudub / naiteks week voi hour jaoks, vt svcadd.sql
# 25.05.2013 algseisude esmane tekitamine ei toimi. kui neid ei tekitata, jaab koikidele kumulatiivne tulemus!
# 01.06 2013 UTW parandus, filter lisamine
# 30.07.2015 lisaparameeter filter juhib ka oo pv gruppe! korraga nii teenust kui grp filtreerida ei saa.

#kaduma
import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc

#import sqlite3
#from pysqlite2 import dbapi2 as sqlite3 # termnet serveris
from sqlite3 import dbapi2 as sqlite3 # basen serveris
import sys
import traceback
#import subprocess

#from socket import *
import string

SQLDIR='/srv/scada/sqlite'

#create sqlite connections
try:
    conn=sqlite3.connect(SQLDIR+'/monitor',2) # tabelid state, controller, newstate. timeout 2 s (default on 5)
    conn.text_factory = str # tapitahtede karjumise vastu, baasis muide iso8850-1
    
except:
    traceback.print_exc()


#conn.execute("PRAGMA journal_mode=wal")  # et kiirem oleks , wal mode 06.08.2012  / KAS TOIMIB? EI, pythoni sqlite on vana!
#conn.execute("PRAGMA synchronous=OFF")  # et kiirem oleks ja kogu aeg ei kirjutaks kettale
cursor=conn.cursor()
cursor1=conn.cursor() # teine kursor veel sama yhenduse otsa
#cursor2=conn.cursor() # kolmas kursor veel sama yhenduse otsa


# ### protseduuuride defineerimine ######################


# voib minna vaja lisaloogikat, mille alusel kadumalainud loendiseisudest ikkagi normaalne juurdekasv tuletada
# aga kas siin on selleks oige koht, vist mitte. algseis tuleb vahendada kohe kui vahe avastatakse, see aga kaivitub harva...
 
 
# #############################################################
# #################### MAIN ###################################
# #############################################################

if len(sys.argv) <2: # vahemalt yks parameeter olgu ka
    print 'parameter 0..4 needed'
    sys.exit()
 
try:
    pernum=int(sys.argv[1]) # period num 0...4, year month week day hour
except:
    print 'illegal parameter',sys.argv[1]
    sys.exit()
    
if pernum>4 or pernum<0: # illegal value
    print 'parameter out of range 0..4'
    sys.exit()

filter=''
t = datetime.datetime.now()
ts = time.mktime(t.timetuple()) #sekundid praegu

print '\ncrontab_svcadd.py run at',t,'with parameter',pernum,
try:
    filter=sys.argv[2]
    print 'processing with filter',filter
except:
    print 'processing everything'
time.sleep(2)
stateregisters = ['Y','M','W','D','H'] # olekuregistri koostamine, ntx WYS. 5 varianti y m w d h. ajutine erand hvv kp8, kus WNS WMS asemel!
# kas see eelmine on ikka adekvaatne, kastusel vaid olekureg tegemiseks, mida ei kasutata?

timeperiods=['yearly','monthly','weekly','daily','hourly']
# pernum        0        1         2        3       4  # kasuta crontabis juhtimiseks neid parameetreid
# lisaparam teenusenimi voi oo voi pv # as filter



if pernum == 1 and filter != 'pv': # kuu liiklusmahud UTW alusel - saadab kontrollerile (barionet) saadetavate LIIKLUSmahtude nullistamise kasu!
    print '\nresetting barionet traffic counters UTW at',t
    try:
        Cmd="BEGIN IMMEDIATE TRANSACTION" # conn
        conn.execute(Cmd)
        register='UTW' # liiklusmahud koigepealt kui just midagi muud ei tehta#Cmd="select mac from state where register='"+register+"'" # nullistame liiklusmahud barionettidest iga kuu alguses  
        Cmd="select mac from state where register='"+register+"' and timestamp+0>"+str(int(ts)-3600) # nullistame liiklusmahud barionettidest mis elus 
        cursor.execute(Cmd)
        for row in cursor: 
            mac=row[0] # kontrolleri id
            Cmd1="insert into newstate(mac,register,value) values('"+mac+"','UTW','0 0 0 0')" # viimast liiget (limit) pole vaja
            # lihtsalt saadame kontrolleritele uue algseisu liiklusmahtude jaoks!
            try:
                conn.execute(Cmd1)
                #print 'UTW zeroing via newstate for controller',mac,'at',t  # ajutine
            except:
                print 'UTW zeroing via newstate (insert) FAILED for controller',mac,'at',t
                traceback.print_exc()
        
        Cmd="select mac from newstate where register='"+register+"'" # kontroll, mida resetime 
        cursor.execute(Cmd)
        print 'hosts with traffic counters to be reset'
        for row in cursor: 
            print row[0] # kontrolleri id
            
        conn.commit()
        
    except:
        print 'failed UTW reset!'
        traceback.print_exc()    
# monthly traffic volume reset end

#exit() # ajutine
time.sleep(5) # igaks juhuks


print '\nsaving cumulative values as',timeperiods[pernum],'beginning values using parameter',pernum,'at',t
# energy and water volumes now for year month week day hour, pernum 0 1 2 3 4         
try:
    Cmd="BEGIN IMMEDIATE TRANSACTION" # conn
    conn.execute(Cmd)
    if filter == 'oo' or filter == 'pv':
        Cmd="select * from svcadd where grp = '"+filter+"'" # teenused, mida on vaja paljundada / konvertida
    else:
        Cmd="select * from svcadd" # loeme kursorisse koik teenused, mida on vaja paljundada / konvertida
    #print Cmd # debug
    cursor.execute(Cmd)
    
    for row in cursor: # koik kumul teenused, mida peab paljundama (ECW, WCV)
        register=row[0] # kumulatiivne teenus, mille alusel myttame
        addregister=row[pernum+1] # selle jaoks on algseisu vaja - kui ta nimi pole tyhi! pernum antakse parameetrina 0...4 
        print 'checking added services based on register',register
        if addregister<>'' and (filter == register or filter == '' or filter == 'oo' or filter == 'pv'): # oo ja pv reserved!
            beginregister=register[:-1]+str(pernum) # sellesse kirjutame algseisu vastavalt state hetkeseisule, reg nimi lopeb 0..4
            stateregister=register[:-2]+stateregisters[pernum]+'S' ## chk this, kes kasutab?
            state='0' # stringina, seda me ei muuda, kirjutame igale juurdetekitatud vaartusele olekuregistrisse ok
            print 'based on register',register,'found addregister',addregister,'beginregister',beginregister # 
            Cmd="select mac,value from state where register='"+register+"'" #
            #print Cmd
            cursor1.execute(Cmd)
            for srow in cursor1: # iga mac jaoks
                beginok=0 # tunnus algseisu olemasolu kohta
                mac=srow[0]
                value=srow[1] # on string
                print 'mac,beginregister',mac,beginregister,'value to become',value # debug
                
                Cmd1="insert into state(mac,register,value,timestamp) values('"+mac+"','"+beginregister+"','"+value+"','"+str(ts)+"')" # proovime lisada (vaid esmakordselt onnestub, index!)
                Cmd2="update state set value='"+value+"', timestamp='"+str(ts)+"' where register='"+beginregister+"' and mac='"+mac+"'"  # update olemasoleva kallal
                
                try: # insert
                    conn.execute(Cmd1) # insert, kui veel ei ole ja update ei onnestunud
                    print 'inserted first beginning value for mac',mac,beginregister,value,'at',t
                except: # update
                    conn.execute(Cmd2) # insert, kui veel ei ole ja update ei onnestunud
                    print 'updated the beginning value for mac',mac,beginregister,value,'at',t
                    

    conn.commit() # transaction end
    print 'periodical values processing based on cumulative service',register,'ended'
except:
    print 'failed beginvalues update commit!'
    traceback.print_exc()
print           
   
