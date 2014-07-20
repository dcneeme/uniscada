#!/usr/bin/python

#paaris ja paaritu sekundil saabunud datagramid kirjutatakse erinevatesse nagiosele baasidesse!

# yldiselt uuendatakse siin sqlite monitor state tabelit ja saadetakse vastus sissetulevale paketile, lisades vastusele ka voimalik ootel info newstate tabelis. 
# viimane muudatus vt allpool logis

# 17.10.2011 edasiarendus monitor25c alusel, kasutusele mitu graafikut yhele teenusele, multiperf ja multidata lisada tabelisse 
# selle mote on extended info edastamine, lisagraafikute tegemiseks naiteks pumbarikete selgituseks.
# lisasin val_reg saatmise tabelisse nagiosele, enne seda polnud aha xxW puhul on vaja multiperf avastamiseks (kuigi kyllap saaks ka value formaadi alusel aru)	
# 17.10.2011 nagiosele vaja saata ka multiperf ja multivalue, isegi siis kui neid mones teenusetabelis ei ole (tyhjana)
# monitor31.py 08.11.2011 -arvestame erinevate service tabelitega, ei tohi teha select * kusagil! oli line 95. ka max_val valja jaetud service tabelist lugemisest.
# monitor32.py 15.11.2011 - seoses lootsi pumplatega, kus BRS alusel vaja teha KLS ja KUS (kaevuluugid ja kilbiuks), kasutame service_alias tabelit ka...
#   konverteerigem statemodify osas, et state registrisse jaaks arusaadav service_xxx xtabeli kirje. siis tundub, et juba kontroller saadab aliast.
# 07.11.2011 monitor33.py - miks 10 x cmd saadetakse? setup muutujad voetakse esimese korraga vastu. LISADA vaja key:? vastamine mac voi aliasmac state hiliseima sisuga.
# 08.11.2011 eelmise reaga seoses - oleks vaja vastust ka siis kui newstate vaartus on sama kui state. milleks erinevuse noue, vahendamaks saadetavat? pane siis piirang B W S
# vastus lahebki alati neile mis commands tabelis loetletud
# 22.12.2011 millegiparast ei kannatanud tyhjust val_reg sees, tyhjuse korral asendus tyhikuga. print "tyhjuse asendus tyhikuga registri",register,"jaoks"
# str(step) et cmd vigu ei annaks nii tihti
# 31.07.2012 logime liiklusmahtusid (valitud mac jaoks voi koikidel)? eraldi baas? kas suudab? socket salvestugu controllers, maht aga sellega seotult mac - maht
# see salvestab controller tabelisse socketi ja selle viimase muutmise aja. mujale (ntx traffic tabelitesse) see ei kirjuta, selleks vt monitor35.py 
# neeme 28.12.2012 in: lisamine
# 21.01.2013 nyyd UDPSock.settimeout(0.3) ja voiks vist veelgi vahendada?
# 10.02.2013 hype multi3 peale seoses kohese vastuse saatmisega.....
# 14.02.2013 kohene saatmine (# fast ...) ei suurendanud newstate tabelis retrycount!! saatis mitu korda jarjest. aga transactioni taastamine aitas, nyyd 1 x ja retrycount kasvab!
# 23.04.2013 baasi monitor transaktsioon sisse viidud, st controller lugemine ja update, state lugemine ja update. parameetriks udp port, kui tahad testida mujal kui 44445.
# 23.04.2013 kuu, nadala, paeva, tunni tarbimised kumulatiivsest. lisatabel inc_svc. lisaprotsess cron abil salvestab state seisud naidatud teenuse kohta. monitor/svacadd tabel.
#      kui tekib kumul tagasilangus? lisaprotsess ei muuda midagi, aga uute teenuste genereerimisel siseneva teenuse taktis midagi teha 
#      (negatiivset juurdekasvu mitte saata jne). 
# 24.04.2013 nimeks monitor_multi4.py. kumul alusel lisatud teenused korralikult toole, y m w d h saehambad. muudetud file4nagiosele - aga seal on veel parandamist kyll...
# 01.05.2013 ei ole vaja saata in:0 koos fast teatega, see pole vastus vaid cmd
# 11.05.2013 - naidu vahenemisel peab normaalne kasv jatkuma kuu lopuni (max kehtestatud ajavahemikuni). salvestada parandus eraldi teenusesse?
# 18.05.2013 ECW (kumul nait) taastamine
# 27.05.2013 kui algseisu pole, salvestatagu sinna praegune kumul! siis ei pea ootama kuupaeva voi kuu vahetuseni, et midagi graafikus naga...
# 15.06.2013 newstate sisse pole motet panna koiki setup muutujaid korraga, kuid see on hoopis bn3setup teema. 
# 20.8.2013 puuduva algvaartuse tekitamine state tabelisse svcadd_calc() poolt. test ok, 60BE ei funka??
# 16.09.2013 svcadd tabelis esinemise kontroll sissekirjutatud koodide asemel
# 26.10.2013 service_alias teisends ei toimi!!! tundub et laks kaduma koos svc_add tegemisega, saehammastega. nyyd korras!
# 07.02.2013 svcadd_calc ajas jama... tootlused teha PEALE teenuse tootlemisvajaduse avastamist , float problem
# 27.03.2014 nagiosele peaks tegema ilma vahetabelita. ja samas stiilis ka mobiilstetele klientidele websocketserveri.

# !!! esineb seni lahendamata probleem - leitud 09.02.2014. kui statusreg sisu rikkuda, naiteks 0 asemel kirj sisse 0DCV, siis seda yle ei kirjutata ja file2nagiosed 
#  selle registriga seotud teenusele edaspidi ebaonnestuvad!!! monitooringus unknown, kuigi kontroller saadab korrektselt. siis vaata bnstate abil, mida state sisaldab!


# VAJA korrata vana vaartust enne uue binaarsete teenuste (1s step) uue oleku saatmist. uue oleku viivitamine due_time abil? 
#  sest rrdtool oletab millegiparast, et uus olek kestis juba eelmisest olekust alates!!!

# aliase kaudu ringisuunamine ei toimi? hvv kp30. asenda id nagiosele/  alias alusel. 


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
import subprocess

from socket import *
import string

# Set the socket parameters
host = "46.183.73.35"  #  "212.47.221.86" # "195.222.15.51"
SQLDIR="/data/scada/sqlite"
port = 44445 # testimiseks 44444, pane parast 44445
if len(sys.argv)>1: # ilmselt ka port antud siis
    port=int(sys.argv[1]) # muidu jaab default value 44445
    print 'udp port set to',port
    sys.stdout.flush()
    time.sleep(1)

buf=8192 # proovime kas vastuste kadu soltub sellest  - EI SOLTU! # buf = 1024
addr = (host,port)
registration = { } # Registration dictionary
array0 = { } # CMD0 jaoks masiiv
array1 = { } # CMD1 jaoks masiiv
registers = { } # registrid jm parameetrid shelli scriptide kirjutamiseks peale update transaktsiooni
DESC = { } # descriptionid iga staatuse kohta
reg=[] #asendusarray register_alias jaoks
 
VALUE="" # TEEME GLOBAALSE MUUTUJA
MONSVCTABLE=""
STATUS=0
#OLD_STATUS=0 # statemodify sisemine
msd=""
mst=""
chg=""

DUE_TIME=0 # tahtaeg

#mitu datagrammi on tulnud
input_lines = 0

# Create socket and bind to address
UDPSock = socket(AF_INET,SOCK_DGRAM)
UDPSock.settimeout(0.3) # enne oli 3! see maarab ka seelle, kui tihti ja kas yldse paaseb ootel asju saatma. 
#mida vaiksem ooteaeg siin, seda suurem toenaosus et saab varem saata midagi. mujal viiteid ei ole!
UDPSock.bind(addr)

#create sqlite connections
try:
    conn = sqlite3.connect(SQLDIR+'/monitor',1) # tabelid state, controller, newstate. timeout 1 s (default on 5)
    conn2 = sqlite3.connect(SQLDIR+'/servicelog',1) # oli id_log jaoks, nyyd viimanetehing jms
    conn3 = sqlite3.connect(SQLDIR+'/alias',1) # tabel alias
    conn30 = sqlite3.connect(SQLDIR+'/nagiosele0',1) # tabel nagiosele, paaris sekunditel
    conn31 = sqlite3.connect(SQLDIR+'/nagiosele1',1) # tabel nagiosele, paaritud sekundid
    conn.text_factory = str # tapitahtede karjumise vastu, baasis muide iso8850-1
    
except:
    traceback.print_exc()


#conn.execute("PRAGMA journal_mode=wal")  # et kiirem oleks , wal mode 06.08.2012  / KAS TOIMIB? EI, pythoni sqlite on vana!
conn.execute("PRAGMA synchronous=OFF")  # et kiirem oleks ja kogu aeg ei kirjutaks kettale
#conn2.execute("PRAGMA journal_mode=wal")  # et kiirem oleks , wal mode 06.08.2012
conn2.execute("PRAGMA synchronous=OFF")  # et kiirem oleks ja kogu aeg ei kirjutaks kettale
#conn3.execute("PRAGMA journal_mode=wal")  # et kiirem oleks , wal mode 06.08.2012
conn3.execute("PRAGMA synchronous=OFF")  # et kiirem oleks ja kogu aeg ei kirjutaks kettale
cursor=conn.cursor()
cursor2=conn2.cursor() # lisatud 07.12.2011, keegi ei kasuta veel
cursor3=conn3.cursor() # lisatud 07.12.2011 . kasutame aliase lugemise jaoks
#cursor30 ja 31 pole vaja, neid ainult kirjutame


# ### protseduuuride defineerimine ######################


# salvestame nagiosele tabelisse yhe registri korraga (aga transaktsiooni sees!)
def insert2nagiosele(locregister): # siin ainult register ette, vaartuse jm omadused otsib ise. 
    #print "*** insert2nagiosele",locregister # ajutine debug
    SVC_NAME="" 
    STA_REG=""
    VAL_REG=""
    UNIT=""
    DIV=""
    DESC[0]=""
    DESC[1]=""
    DESC[2]=""
    DESCR=""
    STATUS=0
    VALUE=""
    DUE_TIME=0  # nagiosele saatmise tahtaeg lisatud 13.09.2009 (pikendame impulsside tagafronte vastavalt teenuse min_len parameetrile)
    MIN_LEN=0  # minimaalne impulsi pikkus peale viimast kinnitust voi esifronti

    
    #   (svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step,min_len,max_val,grp_value,multiperf,multivalue)# uus variant, lopus 2 lisaks
    #Cmd="SELECT svc_name,sta_reg,val_reg,out_unit,conv_coef,desc0,desc1,desc2,step from "+MONSVCTABLE+" where \
    try:
        Cmd="SELECT svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step,multiperf,multivalue from "+MONSVCTABLE+" where \
        sta_reg='"+locregister+"' OR val_reg='"+locregister+"'"    # me ei tea kas selles tabelis on multi liikmed sees
        cursor.execute(Cmd) 
        
    except:
        #(svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step,min_len,max_val,grp_value,multiperf,multivalue)
        Cmd="SELECT svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step from "+MONSVCTABLE+" where \
        sta_reg='"+locregister+"' OR val_reg='"+locregister+"'"    # me ei tea kas selles tabelis on multi liikmed sees
        cursor.execute(Cmd)  
        
    for teenuseinfo in cursor:
        #print locregister,"alusel teenusetabelist",MONSVCTABLE,teenuseinfo
        #print teenuseinfo # ajutine abi
        SVC_NAME=teenuseinfo[0]
        STA_REG=teenuseinfo[1]
        VAL_REG=teenuseinfo[2]
        # siin vahel in_unit mida me ei vaja
        UNIT=teenuseinfo[4] # out_unit
        DIV=teenuseinfo[5] # conv_coef
        DESC[0]=teenuseinfo[6]
        DESC[1]=teenuseinfo[7]
        DESC[2]=teenuseinfo[8]
        step=str(teenuseinfo[9]) # selle alusel rra step, kui puudub siis default step
        # MIN_LEN=int(str(teenuseinfo[9])) # tegelikult siin enam ei kasuta! ainult state juures! valja vottis neeme 13.02.2010
        DESCR="" # algseisuks
        VALUE=""
        MULTIPERF=""
        MULTIVALUE="" # need MULTI asjad voivad puududa soltuvalt teenusetabelist!
        try:
            MULTIPERF=teenuseinfo[10] # graafikute nimed
            MULTIVALUE=teenuseinfo[11] # value liikmed desc kooloni taga naitamiseks
            #print 'multivalue',MULTIVALUE
            # siin voiks None muutmine tyhjaks olla?
            if MULTIPERF == None:  # siis ei teki jama service tabelis multiperf ja multivalue NULL korral
                MULTIPERF=''
            if MULTIVALUE == None:
                MULTIVALUE='0'
            
        except:
            MULTIPERF=""
            MULTIVALUE=""
            #print 'monovalue'

        if (SVC_NAME == ""):
            print "tabelis",MONSVCTABLE,"puudub teenuse nimetus registrile",locregister 
            # valju funktsioonist, kuidas? kuidas mitte midagi teha (except puhul vahel vaja)  -  omista mingile dumb muutujale mingi vartus...
            #return 1 # me ei taha funtsioonist valjuda vaid ainult selle registriga lopetada ja mitte nagiosele saata
            
        else: # teenuse nimetus olems, asi tundub normaalne
            #print "saadud teenuse kohta name",SVC_NAME,'sta_reg',STA_REG,'val_reg',VAL_REG,'unit',UNIT # ajutine    
            if (STA_REG<>""): # staatus on olemas  
                Cmd="SELECT value,timestamp,due_time from state where (mac='"+id+"' and register='"+STA_REG+"')"
                #print Cmd
                cursor.execute(Cmd) # saame yhe rea
            
                for teenuseinfo in cursor:
                    STATUS=int(teenuseinfo[0]) # kui puudub sta_reg siis peaKS STATUS=0 OLEMA...
                    STA_TS=teenuseinfo[1]
                    if (STATUS == 0 and teenuseinfo[2] != None and register == STA_REG):
                        DUE_TIME=int(float(teenuseinfo[2])) # saatmise tahtaeg
                        #if DUE_TIME>0:
                        #    print STA_REG,"...state",STATUS,"due time not null",DUE_TIME
                        
                    else:
                        DUE_TIME=0  # pole vaja midagi venitada
                        
                    
                # leiame DESCR vastavalt STATUS vaartusele  
                DESCR=DESC[STATUS] # olekule vastav teenusekirjeldus
                #print "statuse osa leitud",STATUS,DESCR # ajutine abi
            
            if (VAL_REG<>""): # value on olemas
                Cmd="SELECT value,timestamp from state where (mac='"+id+"' and register='"+VAL_REG+"')"
                #print Cmd
                cursor.execute(Cmd)
            
                for teenuseinfo in cursor:
                    VALUE=teenuseinfo[0] # peab olema string! kas on alati?
                    VAL_TS=teenuseinfo[1]

                #DUE_TIME = 0 # value korral ei otsi ega muuda - ei maksa varem leitut rikkuda!
                
                #print "VALUE",VALUE # ajutine abi
                
            #ehk peaks vordlema timestampe STA_TS ja VAL_TS, et erinevus ei oleks liiga suur...
            
            # vana value tuleks tegelikult ka lugeda... aga ehk polegi kordamist vaja, kui step 1? 
            #nyyd aga on vana vaartus teada, ehk saadame varasema timestambiga? HMM...
            
            #print 'hakkame nagiosele tabelisse salvestama' # ajutine
            
            Cmd="insert into nagiosele(mac,nagios_ip,svc_name,status,value,desc,timestamp,conv_coef,out_unit,location,step,due_time,val_reg,multiperf,multivalue) \
            values('"+id+"','"+MONIP+"','"+SVC_NAME+"','"+str(STATUS)+"','"+VALUE+"','"+DESCR+"','"+str(MONTS)+"','"+str(DIV)\
            +"','"+UNIT+"','"+MONLOC+"','"+str(step)+"','"+str(DUE_TIME)+"','"+VAL_REG+"','"+str(MULTIPERF)+"','"+str(MULTIVALUE)+"')" # None puhul ebaonnestub Cmd koostamine kui str() ei kasuta
            #print Cmd # ajutine abi ####
       
                
            if bnum == 0:    
                try:
                    conn30.execute(Cmd) # nagiosele, KUI EI SAA, siis allpool update, muidu hilineb hiljem saabunud paarilise nagiossse saatmine 
                    print locregister,bnum,"->",SVC_NAME,str(STATUS),VALUE+"/"+str(DIV),UNIT,DESCR
                    # nyyd voib lisada teatud teenuseid logisse eraldi tabelitesse
                    if SVC_NAME == "ViimaneTehing": # servicelog faili tabelisse ViimaneTehing
                        Cmd="insert into "+SVC_NAME+"(mac,nagios_ip,status,value,timestamp,location) \
                        values('"+id+"','"+MONIP+"','"+str(STATUS)+"','"+VALUE+"','"+str(MONTS)+"','"+MONLOC+"')"
                        #print Cmd
                        conn2.execute(Cmd) # see peab onnestuma sama moodi kui nagiosele
                        
                except:
                    #print "see rida on juba nagiosele tabelis olemas, teenus ",SVC_NAME,", teeme update" # ajutine abi
                    Cmd="update nagiosele set status='"+str(STATUS)+"', value='"+VALUE+"' where svc_name='"+SVC_NAME+"' and mac='"+id+"'"
                    #print Cmd # ajutine abi
                    try:
                        conn30.execute(Cmd) # uuendame andmeid hiljem saabunud paarilisega, olgu siis status voi value
                        print locregister,bnum,"->>",SVC_NAME,str(STATUS),VALUE+"/"+str(DIV),UNIT,DESCR   # update onnestus
                        # samad teenused mis insert korral proovitud nyyd ka siin update teha
                        if SVC_NAME == "ViimaneTehing": # parkpay 
                            Cmd="update "+SVC_NAME+" set status='"+str(STATUS)+"', value='"+VALUE+"' where mac='"+id+"' and timestamp='"+str(MONTS)+"'"
                            # ainult viimane kirje muuta, timestamp alusel! eeldame, et TRS ja TRV saabuvad yhe datagammi sees ja TRS esimesena!
                            #print Cmd
                            conn2.execute(Cmd) # see peab onnestuma kui nagiosele update onnestus
                        
                    except:
                        traceback.print_exc()
            
            else: # teine bnum
                try:
                    conn31.execute(Cmd) # nagiosele, KUI EI SAA, siis allpool update, muidu hilineb hiljem saabunud paarilise nagiossse saatmine 
                    print locregister,bnum,"->",SVC_NAME,str(STATUS),VALUE+"/"+str(DIV),UNIT,DESCR
                    # nyyd voib lisada teatud teenuseid logisse eraldi tabelitesse
                    if SVC_NAME == "ViimaneTehing": # servicelog faili tabelisse ViimaneTehing
                        Cmd="insert into "+SVC_NAME+"(mac,nagios_ip,status,value,timestamp,location) \
                        values('"+id+"','"+MONIP+"','"+str(STATUS)+"','"+VALUE+"','"+str(MONTS)+"','"+MONLOC+"')"
                        #print Cmd
                        conn2.execute(Cmd) # see peab onnestuma sama moodi kui nagiosele
                        
                except:
                    #print "see rida on juba nagiosele tabelis olemas, teenus ",SVC_NAME,", teeme update" # ajutine abi
                    Cmd="update nagiosele set status='"+str(STATUS)+"', value='"+VALUE+"' where svc_name='"+SVC_NAME+"' and mac='"+id+"'"
                    #print Cmd # ajutine abi
                    try:
                        conn31.execute(Cmd) # uuendame andmeid hiljem saabunud paarilisega, olgu siis status voi value
                        print locregister,bnum,"->>",SVC_NAME,str(STATUS),VALUE+"/"+str(DIV),UNIT,DESCR   # update onnestus
                        # samad teenused mis insert korral proovitud nyyd ka siin update teha
                        if SVC_NAME == "ViimaneTehing": # parkpay 
                            Cmd="update "+SVC_NAME+" set status='"+str(STATUS)+"', value='"+VALUE+"' where mac='"+id+"' and timestamp='"+str(MONTS)+"'"
                            # ainult viimane kirje muuta, timestamp alusel! eeldame, et TRS ja TRV saabuvad yhe datagammi sees ja TRS esimesena!
                            #print Cmd
                            conn2.execute(Cmd) # see peab onnestuma kui nagiosele update onnestus
                        
                    except:
                        traceback.print_exc()

                        
            #nagiosele tabelisse kirjutamine tehtud. 
            
            
    return 0
    
    
                        
#tekitame kirjeid eraldi sqlite tabelisse nagiosele, kasutades massiivina ette antud registrinimesid. UUS! ei vaata enam datagrammi uuesti labi!
def file4nagios(locreg):  # registrite massiiv parameetriks
    print 'file4nagios, parameetriks registrinimede massiiv locreg =',locreg # ajutine debug
    Cmd="BEGIN IMMEDIATE TRANSACTION" # iga datagrami jaoks oma transaction database nagiosele jaoks!
    if bnum == 0:
        conn31.execute(Cmd)  # alustame transaktsiooni nagiosele baasiga
    else:
        conn31.execute(Cmd)  # alustame transaktsiooni nagiosele baasiga

    
    for i in range(len(locreg)): # kui siia on saadetud, siis paneme ta ka nagiosele tabelisse, rohkem kontrollimata.
        register = locreg[i] # 
        #value leiab insert2nagiosele ise
        insert2nagiosele(register) 
                            
                            
    conn3.commit() # trans lopp - millise?nagiosele... seda ju ei kasuta?
    conn2.commit() # ViimaneTehing jm log. ilma selleta db locked. teeme alati, kuigi vaid siis vaja kui logitav teenus oli...
    if bnum == 0:
        conn30.commit()  # lopetame transaktsiooni sel korral taidetud nagiosele baasiga 0
    else:
        conn31.commit()  # lopetame transaktsiooni sel korral taidetud nagiosele baasiga 1

    
    return 0  # file4nagios lopp
        
        
    
#insert voi update state. teeb ka controller locationi update kui see muutunud.
def statemodify(locregister,locvalue): #kasutame ka globaalseid muutujaid id ja ts tabeli state muutmiseks
    #if locregister == 'DCS' or locregister == 'TCS':  # debug, probleemsed parkpay teenused
    #    print "statemodify() arguments (2):",locregister,locvalue," global args",id,ts
    
    MIN_LEN=0 # algseis min kestusele - vist pole aga siin seda vajagi?
    DUE_TIME=0 # tahtaja agseis
    OLD_STATUS=0
    
    # teeme kindlaks mis on sellele sta_reg jaoks vajalik minimaalne haire kestus
    #omab tahtsust vaid siis kui locvalue==0
    
    if locvalue == "0": # kontrolli stringi suhtes 
        #print "###registri",locregister,"olek nullistumas"
        Cmd="SELECT min_len from "+MONSVCTABLE+" where sta_reg='"+locregister+"'"  # val_reg ei huvita 
        #print Cmd
        try:
            cursor.execute(Cmd) # saame yhe rea vastuseks kui sedagi - val korral ei saa!
        except:
            print locregister," pole sta_reg vist, min_len lugemine ei onnestu"
            traceback.print_exc()

        for locrow in cursor:
            if MIN_LEN == None:
                MIN_LEN=0 
            else:
                try:
                    MIN_LEN=int(locrow[0]) # loodame et see mis siin on konverteerub kuidagi numbriks
                except:
                    MIN_LEN=0 # ja kui ei konverteeru olgu 0
                
        if MIN_LEN>0:
            #print locregister," uurimise algus, min viide",MIN_LEN
        
            #siin ON tegu diskreetse olekuga. kontrollime selle eelmist vaartust ja update aega state tabeli alusel
            Cmd="SELECT value,timestamp from state where register='"+locregister+"' and mac='"+id+"'" # saame eelmise oleku ja ajamargi 
            #print Cmd
            try:
                cursor.execute(Cmd) # saame yhe rea vastuseks kui sedagi
            except:
                traceback.print_exc()
                
            for locrow in cursor:
                #print "locrow",locrow
                if locrow[0]<>'': 
                    OLD_STATUS=int(locrow[0])
                    OLD_TS=float(locrow[1]) # ehk kaotame punkti int() abil ara? ah las olla...

            #print locregister,"min viide",MIN_LEN,"OLD_STATUS",OLD_STATUS,"OLD_TS",OLD_TS,"now",ts,"vanus s",str(ts-OLD_TS)
            
            if (OLD_STATUS>0 and OLD_TS + MIN_LEN > ts): # kestus (eelmisest updatest) olnud lyhem, kui MIN_LEN  
                print "###",locregister,"haire lopetamise pikendamine",OLD_TS+MIN_LEN-ts,"s vorra"
                DUE_TIME=OLD_TS + MIN_LEN
                #print locregister,locvalue,"paneme tahtaja",DUE_TIME
            else:
                DUE_TIME=0 # edastage viivituseta

    try:
        Cmd="INSERT INTO STATE (register,mac,value,timestamp,due_time) VALUES \
        ('"+locregister+"','"+id+"','"+str(locvalue)+"','"+str(ts)+"','"+str(DUE_TIME)+"')"
        #print Cmd
        conn.execute(Cmd) # insert, kursorit pole vaja
                
    except:   # UPDATE state
        Cmd="UPDATE STATE SET value='"+str(locvalue)+"',timestamp='"+str(ts)+"',due_time='"+str(DUE_TIME)+"' \
        WHERE mac='"+id+"' AND register='"+locregister+"'"
        #print Cmd
        
        try:
            conn.execute(Cmd) # update, kursorit pole vaja
            #print 'state update done for mac',id,'register',locregister # ajutine
            
        except:
            traceback.print_exc()
            return 1 # kui see ka ei onnestu, on mingi jama


    return 0 # DUE_TIME  state_modify lopp
    
    

    
    
def kontrollerile(id,inn,addr): # uurime vastuse voimalikkust ja tekitame newstate sisu teadaoleva mac aadressiga kontrolleri jaoks
    global t # aga id,inn ja addr on siin lokaalsed! inn olgu string! in:0 pole vaja saata!
    Cmd="BEGIN TRANSACTION" # tagasi 14.02.2013 n
    conn.execute(Cmd) # tagasi -"-
    
    # selleks, et ka erinevuste puudumisel voi state registris mitteesinemisel saadetaks newstate vaartus, on vaja register commands tabelisse panna!
    
    Cmd="select newstate.register,newstate.value from newstate LEFT join state on newstate.mac = state.mac and \
    newstate.register=state.register where ( state.value <> newstate.value or newstate.register in \
    (select register from commands where commands.register = newstate.register)) and  \
    (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10"

    # tom 10.6.9 retrycount on null voi vaiksem kolmest, seega pole veel nii palju retryisid tehtud.
    # kui on kolm korda saadetud, siis enam ei proovita, samas kui tehakse uued vaartused setupi poolt,
    # tuleb kindlasti ka retry count 1-ks panna voi jatta nulliks. Samas voib ka triger need ara tappa kui
    # monel on retrycount >= 9

    # saatmine on juhitav commands tabeli kaudu! siis ei kontrollita erinevust state tabelis olevast sisust
    
    #tuleb saata vaid need, mis erinevad state tabelis olevatest, siis saab yhe flash kirjutamisega hakkama 5 asemel
    #korraga ei tohi saata yle 10 muutuja, ei mahu kontrolleris input stringi!
    #saadetud kaovad newstate tabelist triggeri abil ara (kontrollerist saadetakse nende kohta vastus state tabelisse) 
    #ja siis saab jargmise portsu saata kui vaja. jargmine muutujate listing antakse peale salvestamist vist??
    
    #print Cmd
    cursor.execute(Cmd)  # read from newstate (mailbox) table
    # # conn.commit() #valja 14.2 
    
    
    
    
    #SAADAME TEATEID KONTROLLERILE NEWSTATE TABELI SISU ALUSEL
    #sdata = "id:" + id + "\n" # alustame vastust id-ga
    if inn == "":
        sdata = "id:" + id + "\n" # alustame vastust id-ga
    else:
        sdata = "id:" + id + "\nin:" + inn + "\n" # saadame ka in tagasi
    
    answerlines = 0
    for row in cursor:
        #print "select for sending to controller newstate left join state row",row
        register=row[0]
        value=row[1]
        sdata=sdata + str(register) + ":" + str(value) + "\n"
        answerlines = answerlines + 1
    
    
    #edasi pole vaja minna kui midagi saata pole
    if answerlines > 0:
        # retrycount in newstate ########
        # kui on ridasid mida saata, siis incremendime nendes ridades retrycount atribuuti newstate
        # tabelis. Retrycounti  ei tohi uuendada kui side on maas, onneks saadetakse vastused
        # ainult juhul, kui midagi on kontrolleri poolt just tulnud, seega mailbox pohimottel.
    
        # neeme feb 2013 siiski nyyd saadetakse ka ilma kontrolleripoolse poordumiseta! ja tekkiski probleem, et saatis korduvalt emme kui retrycount uuenes. transaction appi? 
        
        # retrycounti pole vaja uuendada, kui midagi ei saadeta.
        Cmd ="update newstate \
        SET retrycount = ( \
        select CASE WHEN  ( select max(retrycount) from newstate where mac='" + str(id) + "' \
        and  mac||register in ( \
        select newstate.mac||newstate.register from newstate LEFT join state on newstate.mac = state.mac and \
        newstate.register=state.register where ( state.value <> newstate.value or newstate.register in \
        (select register from commands where commands.register = newstate.register)) and \
        (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10 \
        ) \
        ) is null  THEN 1 ELSE \
        ( select max(retrycount)+1 from newstate where mac='" + str(id) + "' \
        and mac||register in ( \
        select newstate.mac||newstate.register from newstate LEFT join state on newstate.mac = state.mac and \
        newstate.register=state.register where ( state.value <> newstate.value or newstate.register in \
        (select register from commands where commands.register = newstate.register)) and \
        (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10 \
        ) \
        )  END \
        ) \
        where mac||register in ( \
        select newstate.mac||newstate.register from newstate LEFT join state on newstate.mac = state.mac and \
        newstate.register=state.register where ( state.value <> newstate.value or newstate.register in \
        (select register from commands where commands.register = newstate.register)) and  \
        (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10 \
        ) ;"

        conn.execute(Cmd)  
        
    conn.commit() # end transaction


    t = datetime.datetime.now() # votame vastamise aja
    if id<>"XXX00204ACC6195": # ajutine blokeering
        print "---answer or command to the controller ",id,addr,t #
        print sdata
        UDPSock.sendto(sdata,addr)  # ID SAADAME KA SIIS KUI MUUD SAATA POLE
    #print "---answer to the controller ",id,t # 
    #print sdata
    #UDPSock.sendto(sdata,addr)  # ID SAADAME KA SIIS KUI MUUD SAATA POLE

# kontrollerile() lopp


                
def svcadd_calc(register,value,mac): # arvutame kumulatiivse alusel loodud lisateenustele juurdekasvud alates salvestatud algvaartusest
    #perioodi algseisud asuvad kumul teenuse algusega teenustes, mille lopus on number vahemikust 0..4 (y,m,w,d,h)
    #NB - lisanduvate teenuste jaoks peab status olemas olema, muidu ei saadeta nagiosele. praegu salvestab crontab_svcadd.py koikjale 0 kuhu algseisu paneb.
    #ei hakka jamama kui ei ole tegu sellise teenusega mida tootlema peaks!
    outsvcnames=['','','','',''] # 5 stringi y m w d h - see voidakse asendada
    outsvcvalues=['','','','',''] # 5 stringi y m w d h
    endvalue=[0,0,0,0,0,0,0,0] # kuni 8 liiget esialgu arvestatud. E ja W algusega teised teenused ronivad ka siia sisse...
    svcfound=0 # any added services found?
    found=0 # liikmete leidmine?
    
    #valcount=len(value.split(' ')) # liikmete arv kindlaks teha, korrata sama arvu igas vastuses. 1 voi 2 enamasti
    #print 'svcadd_calc: valcount',valcount,'endvalues', # debug
    #for valnum in range(valcount): # leime yksikvaartused kumulatiivsest
    #    endvalue[valnum]=int(float(value.split(' ')[valnum])) # teeme numbrid stringijupist
    
    Cmd="select * from svcadd where svc_c='"+register+"'" # saame katte sisendteenusele vastavad juurdegenereeritavad. tyhjus, mida vaja pole.
    #print Cmd # debug
    cursor.execute(Cmd)
    for row in cursor: # yks rida vastuseks kui yldse vastust tuli. row[6] ei kasuta, liikmete arvu saame sisendi alusel
        svcfound=1 # midagi on
        outsvcnames=[row[1],row[2],row[3],row[4],row[5]] # vaid siis asendab esialgsed tyhikud, kui tabelist midagi leiti. siin ei ole esialgset (row[0])
        outsvcvalues=['','','','',''] # algseis
        
        #### jargmine loik espolt siia @@@@@
        valcount=len(value.split(' ')) # liikmete arv kindlaks teha, korrata sama arvu igas vastuses. 1 voi 2 enamasti
        #print 'svcadd_calc: valcount',valcount,'endvalues', # debug
        for valnum in range(valcount): # leime yksikvaartused kumulatiivsest
            endvalue[valnum]=int(float(value.split(' ')[valnum])) # teeme numbrid stringijupist, viimased vaartused
        #####
        
        #print 'processing beginvalues for services',outsvcnames # debug
        for addnum in range(5): # erinevad algseisud selle teenuse ja mac jaoks, 0=y, 1=m, 2=w, 3=d, 4=h. koiki ei pruugi olla, siis tee. voivad olla mitme liikmega. 
            if outsvcnames[addnum]<>'': # on vaja arvutada
                found=0 # need to know if there was any begin value(s), replace with valcount zeroes if not
                beginvalue=[0,0,0,0,0,0,0,0] # yksikud liikmed max 8... voiks ka append kasutada.
                outvalue=[0,0,0,0,0,0,0,0] # need valjastame. arvestame kuni 8 liikmega esialgu1
                outvalues='' # string
                Cmd="select value from state where register='"+register[:-1]+str(addnum)+"' and mac='"+mac+"'" # saame katte xyN algseisu selle perioodi jaoks
                #print Cmd # debug
                try:
                    cursor.execute(Cmd) # otsime algseisu lisateenusele
                    for row in cursor: # tuleb 1 vastus kui yldse. kui ei tule, ei ole algseisu olemas! crontab_svcadd peaks tekitama perioodi vahetusel!
                        found=1 # algseis outsvcnames[addnum] jaoks leitud state tabelist
                    if found == 1: # PERIOODI ALGREGISTER ON STATE TABELIS OLEMAS
                        if row[0] <>'' and row[0] <>' ' and valcount>0: # ei ole tyhi sisu, see beginvalue on olemas
                            print '##register, value,valcount',register,value,valcount # debug
                            for valnum in range(valcount): # leiame koik beginvalue liikmed oma vaartustega
                                try:
                                    beginvalue[valnum]=int(float(row[0].split(' ')[valnum])) # teeme numbri stringijupist, muidu jaab 0 perioodi algusvaartus
                                    print 'svcadd valnum beginvalue, endvalue',valnum,beginvalue[valnum],endvalue[valnum] # debug
                                except:
                                    print 'beginvalue failure, valnum,valcount',valnum,valcount
                                    traceback.print_exc()
                                    
                                if endvalue[valnum] >= beginvalue[valnum]: # on juurdekasv. kui ei ole, saadame liikme vaartuse 0
                                    outvalue[valnum]=endvalue[valnum]-beginvalue[valnum] # lahutame perioodi algseisu. kui beginvalue puudub, on ta 0.
                                    #print outvalue,
                                else: # kumul alla algvaartuse. vordsustame algvaartuse kumulatiivsega, kuigi tegelikult tuleks vist hoopis kumulatiivset suurendada...
                                    msg='beginvalue in register '+register[:-1]+str(addnum)+' less than cumulative value! setting all members to cumulative '+value
                                    Cmd="update state set value='"+value+"' where register='"+register[:-1]+str(addnum)+"' and mac='"+mac+"'"
                                    print Cmd
                                    conn.execute(Cmd)
                                
                                if valnum>0: # lisa tyhik  
                                    outvalues=outvalues+' '
                                outvalues=outvalues+str(int(outvalue[valnum])) # teeme stringi lisateenuse vaartuseks, voib mitut numbrit sisaldada
                            outsvcvalues[addnum]=outvalues # asendame need vaartused mis ei ole tyhjad, ylejaanud jaavad tyhjaks nagu nad tsykli alguseski olid
                        
                        else: # algvaartuse register on olemas, aga sisu tyhi - vordsustame kumulatiivsega ja salvestame state registrisse
                            print 'svcadd algvaartust '+register[:-1]+str(addnum)+' pole, salvestame'
                            try:
                                Cmd="insert into state(mac,register,value) values('"+mac+"','"+register[:-1]+str(addnum)+"','"+value+"')" # salvesta loppvaartus
                                conn.execute(Cmd)
                            except:
                                Cmd="update state set value='"+value+"' where register='"+register[:-1]+str(addnum)+"' and mac='"+mac+"'"
                                conn.execute(Cmd)
                            print Cmd # debug
                        
                    else: # algolek selle teenuse jaoks puudus, TEKITAME! 
                        msg='no beginvalue in state for service '+register[:-1]+str(addnum)+', will be inserted'
                        print(msg)
                        Cmd="insert into state(mac,register,value) values('"+mac+"','"+register[:-1]+str(addnum)+"','"+value+"')" # value on string, voib olla mitme liikmega
                        print Cmd # debug
                        try:
                            conn.execute(Cmd)
                            print 'beginvalue ',value,'of a addsvc period inserted into state for mac',mac,'svc',register[:-1]+str(addnum)
                        except:
                            traceback.print_exc()
                        sys.stdout.flush()
                        
                    #outsvcvalues[addnum]=outvalues # jama eoi saada, jargmisega teatega peaks juba korda minema
                    
                except:
                    print 'svcadd_calc() problem for register',register
                    traceback.print_exc()
                    sys.stdout.flush()
                    outsvcvalues=['','','','',''] # error indication
                    #time.sleep(1)
                    
    #print 'svcadd:',id,register,outsvcnames,outsvcvalues # debug
    return outsvcnames,outsvcvalues # osa vaartusi asendati, ylejaanud ''
    
# svcadd_calc lopp, perioodi kohta juurdekasvude genereerimine yhe kumulatiivse teenuse alusel
    
    
# ### protseduuuride defineerimise lopp ############################################ 
 




 
 
# #############################################################
# #################### MAIN ###################################
# #############################################################

        
#conn.create_function("SendToNagios",5,SendToNagios)
#conn.create_function("SendToNagios",4,SendToNagios)
# allpool seda ei kasutata, vt sqlite3 trigerit .schema abil


# Receive messages
while 1:
    MONLOC="???" # algseis, kirjutatakse yle kui juba esineb controller tabelis
    NEWSOCKET=""    
    inn=""
    try: # kas on infot udp sisendpuhvris, ootame timeout vorra mis alguses defineeritud. kui ei ole, saatma!
        data,addr = UDPSock.recvfrom(buf) # siin nyyde viide 0,1 s varasema 3 asemel. kui midagi ple tulnud, uuri kas on midagi saata vaja...
        input_lines=input_lines+1
        #print "got message from addr: ",addr
        t= datetime.datetime.now()  #  datagrami saabumise aeg. allpool teeme sekunditeks
        ts= time.mktime(t.timetuple()) #sekundid praegu
        MONTS=str(int(ts)) # punktita
        bnum=int(ts)%2 # o voi 1 soltuvalt jooksvast sekundist, paaris voi paaritu
        
        if (addr[1] < 1 or addr[1] > 65536):
            print "illegal source port " + str(addr[1]) + " in the message received from " + addr[0]

        if "id:" in data:
            lines=data[data.find("id:")+3:].splitlines()   # vaikesed tahed

            # mac aadress
            id=lines[0] # mac
            #print "id",id   # seda korratakse allpool nagunii

            if "in:" in data:
                lines=data[data.find("in:")+3:].splitlines()   # vaikesed tahed
                inn=lines[0]  # paketi jrk tunnus

            NEWSOCKET=addr[0]+","+str(addr[1]) # ip,port kust tuli
            #print "newsocket ",NEWSOCKET  # salvestamiseks controller tabelis vaja
            
            print "\nfrom controller",id, t, NEWSOCKET,"to buffer",bnum  #addr   # got the data, start printing lines content
            print data # naita saabunud registrite sisu
            #registration[id] = addr
            
            #print "registration dict=",registration[id]
            
            
            MONLOC=""
            SOCKET=""
            #korjame kokku locationi, kaivitatava sh scripti jm vajaliku    
            
            Cmd="BEGIN IMMEDIATE TRANSACTION" # iga datagrami jaoks oma transaction monitor andmebaasi jaoks! tabelis controller, state, newstate, svcadd...
            conn.execute(Cmd)
            Cmd="SELECT servicetable,nagios_ip,location,socket FROM controller WHERE mac='"+id+"'"
            cursor.execute(Cmd)
            for row in cursor: # peab tulema 1 rida
                #MONEXE=row[0]
                #MONEXE="/srv/scada/scripts/pumplad/haapsalu19"  # seda enam ei kasuta
                MONSVCTABLE=row[0] # see maarab teenuste nimed ja keele
                MONIP=row[1] # millisele nagiosele saata
                MONLOC=row[2] # kus asub controller tabeli info alusel
                SOCKET=row[3] # mis port ja aadress selle mac jaoks saadab
                
            cursor.close() # voib ka mitte teha
            
            if (MONLOC<>""):  # asukoht controller tabelis olemas
                print "\n processing data from",id,MONLOC,NEWSOCKET,str(t) # str(datetime.datetime.now()) # alustame logis uut portsu
            else:
                print "non-registered controller mac",id
                
            if (SOCKET<>NEWSOCKET):  # kust tuli viimane info on ka controller tabelis olemas, sh ka timestamp
                print "updating controller registration data for mac",id,SOCKET,"->",NEWSOCKET
                Cmd="UPDATE controller SET socket='"+NEWSOCKET+"',socket_ts='"+MONTS+"' WHERE mac='"+id+"'"
                try:
                    #print Cmd #cursor.execute(Cmd) # saame yhe rea vastuseks kui sedagi
                    conn.execute(Cmd)
                    #conn.commit() # see alles teeb tegelikult, ilma ei salvestu
                except:
                    traceback.print_exc()
                
            #cursor.close() 
            
            
            
            #SISENDINFO TOOTLUS KEY:VALUE PAARIDE HAAVAL
     
            lines=data.splitlines()
            reg=[] # tyhjaks, et teenuste registrinimed sisse panna
            for i in range(len(lines)):
                if ":" in lines[i]: # eraldaja peab olema
                    #print "   "+lines[i]
                    line = lines[i].split(':')
                    register = line[0]
                    
                    value = line[1]
                    if value == '':
                        value = ' ' # tyhikuga kaitub paremine kui tyhjusega...
                        print "tyhjuse asendus tyhikuga registri",register,"jaoks"
                        
                    #print "  got reg val reg[i]", register, str(value) ,str(reg[i]),"for mac",id # ajutine ####
                    
                    
                    #backwards compatibility with older controller software using MSX compound string
                    if register == "MSX": # korjame siit hex jorust olulisemad baidid valja ja eraldame neist 8bit numbri voi olekubitid
                        #print "received MSX:",value
                        hexvalue=value # jatame meelde
                        for register in "LVV,LHS:28,BRS:30,PWS:31".split(','):  # bit values in first 4 bytes, level/20 in 5th!
                            #print "..MSX-based register ",register
                            if register == "LVV":
                                value=int(hexvalue[8]+hexvalue[9],16)*20 # veetase mm - stringist cut ja hex2int ongi tehtud...
                                #print "...MSX based LVV ",value
                                
                            else:
                                bit=int(register.split(':')[1])   # see tuleb enne teha kuni register muutumatu
                                #siin tuleks vaartus leida eraldi tabelist, sest 1 ei ole alati oige.... tegelikult antud juhul alati 1=2!
                                bitval=pow(2,bit)
                                register=register.split(':')[0]
                                value=2*(int(hexvalue[0]+hexvalue[1]+hexvalue[2]+hexvalue[3]+hexvalue[4]+hexvalue[5]+hexvalue[6]+hexvalue[7],16) & bitval)/bitval # result 0 or 1 - tegelikult 0 voi 2!
                                #print "...MSX-based register value bit ",register,value,bit
                                
                            try:
                                statemodify(register,value)
                                #print  " MSX-based statemodify" ,register,value,DUE_TIME
                                if DUE_TIME>0:
                                    print "  MSX-based statemodify for ",register,value,"with added delay of",DUE_TIME-ts,"s"
                                else:
                                    print "  MSX-based statemodify for ",register,value
                                    
                                
                            except:
                                traceback.print_exc()
                            
                            
                    else:  #  ei ole MSX
                        #print "ei ole msx, register",register   # ajutine - POV siiani jouab
                        if (register <> "id" and register <> "in" and register <> "chg" and register <> "frag" and value[0] <> "?"): # loetletud variantide korral state uuendamist ei toimu
                            #print "ei ole msx ega id ega frag, register",register   # ajutine 
                            #kontrollime aliast ja muudame register nime kui vaja, ykshaaval nii sta kui val jaoks. aliase tabelis neil vahet ei tehta!
                            #lisatud 15.11.2011 neeme
                            Cmd="SELECT outregister from service_alias where (mac='"+id+"' and inregister='"+register+"')"
                            #print Cmd # ajutine
                            #try:
                            cursor.execute(Cmd)
                                #conn.commit() # ei saa oodata kuni allpool commit tehakse, infot kohe vaja - LOLLUS! 
                                #kasuta transaktsiooni! EHK ON SIISKI VAJA / ei ole toiminud see asendus 14.6.2013 alates!
                            for row in cursor: # peab tulema 1 rida kui yldse tuleb
                                newregister=row[0]
                                if newregister<>'':
                                    print "replacing register and reg[i]",register,"with service alias",newregister,value,"for mac ",id   # service alias only!
                                    register=newregister
                                    
                            cursor.close()
                            #15.11.2011 lisamise lopp
                            
                            
                            # siia vahele tsykkel addsvc abil uute teenuste lisamiseks 23.04.2013. peab algama W voi E-ga
                            # statemodify tuleb labi teha nii jooksva teenusega kui ka voimalike lisadega
                            addregister=['','','','',''] # registrid ja nende vaartused y m w d h 
                            addvalue=['','','','','']
                            addrange=1 # see tekitab vaid svcnum 0, mis ei muuda midagi


                            
                            #if register[0] == 'W' or register[0] == 'E' or register[0] == 'U' or register[0] == 'T': # voimalik on lisateenuste juurdetegemine, vesi ja elekter
                            if register[-1] == 'V' or register[-1] == 'W': # lisateenuste juurdetegemine kumulatiivse sisendi alusel, vaid perfdata olemasolul
                                #vesi, elekter, side kumul. aga UTW, TCW? kontrolli parem tabelist svcadd tabelist...
                                #print 'possible service addition based on register,value',register,value  # avoid those not in addsvc table!
                                # proovime nyyd alati kas on teenuseid paljundada vaja kumulatiivsete mingi ajavahemiku kohta
                                #print 'trying svcadd_calc() with register',register,value,id # debug
                                
                                try:
                                    addkompott=svcadd_calc(register,value,id) # params strings. returns added registers,values ([],[])
                                    addregister=addkompott[0] # esimene osa vastusest, lisanduvad registrid
                                    addvalue=addkompott[1] # teine osa vastusest, vaartused nende registrite jaoks (voivad olla multivalue)
                                    if addregister<>['','','','','']:
                                        addrange=6 # esimene on originaal ja sinna otsa 5 lisa
                                        print 'svcadd_calc() returned',addkompott,'for mac',id,'register',register #,addregister,addvalue

                                        #print 'going to execute statemodify in loop for range',addrange # debug
                                    
                                        aregister=''
                                        avalue='' #added register value to be used below
                                        for svcnum in range(addrange): # 0 voi 0..6. liige 0 on alati olemas, originaalteenus!! 1..5 vastab aga added 0..4
                                            #print 'svcnum',svcnum
                                            if svcnum>0: # registri ja value asendus - ei ole enam originaalteenus, see saadetakse esimesena muutmata kujul 0 puhul
                                                aregister=addregister[svcnum-1] # register statemodify jaoks 
                                                if aregister<>'': # tyhjus tahendab, et ei ole vaja seda varianti saata y m w d h hulgast num 0 1 2 3 4 
                                                    avalue=addvalue[svcnum-1] # voib olla multivalue siin
                                                    print 'svcadd produced added register,value',aregister,avalue #,'based on addvalue',addvalue ###########################################
                                                    statemodify(aregister,avalue) # seda voib teha ainult siis, kui reg tyhi ei ole.
                                                    reg.append(aregister) # file4nagiose jaoks moeldud arraysse, registrinimede massiiv
                                                    print " --- statemodify done for",id,aregister,avalue,DUE_TIME # lisatud teenused
                                    #else:
                                        #print 'svcadd_calc() FAILED for mac',id,'register',register # there was nothing to add
                                        
                                except:
                                    print 'failed svcadd_calc() for register',register
                                    traceback.print_exc()
                                    sys.stdout.flush() # et kohe logis naha oleks
                                    
                            #else:
                                #print 'no need for svcadd_calc for id,register',id,register # debug

                                    
                            if register<>'': # see siin on algne register, mis samuti uuendamist vajab
                                #print " --- going to execute statemodify for",id,register,value,DUE_TIME # POV ei joudnud siia kui val oli tyhi??? ####
                                try:
                                    result=statemodify(register,value) # seda voib teha ainult siis, kui reg tyhi ei ole.
                                #if result == 0: # edukas
                                    print " --- statemodify done for",id,register,value, # DUE_TIME # ei joudnud siia kui val oli tyhi??? ####
                                    reg.append(register) # file4nagiose jaoks moeldud arraysse, registrinimede massiiv
                                    print " -reg.append done for",id,register,value, # DUE_TIME # ei joudnud siia kui val oli tyhi??? ####
                                    if DUE_TIME>0:
                                        print ", added delay",DUE_TIME-ts,"s"
                                    else:
                                        print
                                except:
                                    print "statemodify failed for",id,register,value
                                    traceback.print_exc()    
                                        
                        else: # state uuendamisele mittekuuluvad registrid voi vaartused - lisame siia dec 2011 ka aliasmac alusel info! ###LASTCHG below! ####
                            #print "state uuendamisele mittekuuluv register",register,"sest reg value on ",value[0] # ajutine
                            if value[0] == "?": # saadame tagasi selle registri viimase vaartuse, mis ei tohi olla vanem kui kysimargi taga olev sek vaartus
                                # kui on vanem, saadame tagasi tyhjuse! kui nr ? taga  puudub, saadame ykskoik kui vana vaartuse.
                                if len(value)>1:
                                    maxage=int(float(value[1:])) # sellest vanemaid vaartusi ei taha, siis tulgu vastuseks tyhjus
                                else:
                                    maxage=315360000 # 10 aastat sekundites
                                    
                                Cmd="SELECT mac from alias where (aliasmac='"+id+"')" # kas on mac ringisuunamisi olnud aliasmac peale, mis on jooksev id. 
                                #print "cmd for alias search",Cmd # ajutine
                                
                                #neid ringisuunamisi voib ka palju olla, siis vota alati varskeim otsitava registri value!
                                try:
                                    cursor3.execute(Cmd) # leitud koik aliased
                                    conn3.commit() # tegelikult voiks ka see monitor baasis olla, yhes transaktsioonis

                                except:
                                    traceback.print_exc()
                                    sys.stdout.flush() # et kohe logis naha oleks
                                    time.sleep(1)
                                
                                

                                Cmd="SELECT max(timestamp) from state where register='"+register+"' and (mac='"+id+"'" # cmd algus
                                for row in cursor3: # peab tulema 1 rida kui yldse mac asenduseks
                                    if len(row[0]) == 12 : # mac pikkus yle-eelmise cms alusel
                                        Cmd=Cmd+" or mac='"+row[0]+"'" #lisame jarjekordse aliase mac mis sellesse punti voib kuuluda
                                        
                                cursor3.close
                                Cmd=Cmd+") and value not like '?%'" # lopetame Cmd  - kysimargiga value ei huvita, see on kysimus
                                
                                print "cmd for state value over aliases: ",Cmd # ajutine
                                cursor.execute(Cmd) # state tabeli kallal kaidud
                                
                                for row in cursor: # peab tulema 1 rida yhe timestambiga
                                    latestvalueTS=row[0] # see on string!
                                    
                                Cmd="select value from state where register='"+register+"' and timestamp='"+latestvalueTS+"'" #leiame viimase vaartuse yle mitme maci
                                #print "cmd for value select over aliases:",Cmd # ajutine    
                                try:
                                    cursor.execute(Cmd) # state tabeli kallal kaidud, saadud yks varskeim value
                                    
                                    for row in cursor: # peab tulema ainult 1 rida
                                        value=row[0] # see on varskeim vaartus mis saada on
                                        print "got value",value," over aliases for register",register,"with timestamp",latestvalueTS,"to send back"
                                    
                                except:
                                    print 'failed cursor.execute(Cmd) for register',register
                                
                                cursor.close()
                                
                                print "still got the value",value," over aliases for register",register,"with timestamp",latestvalueTS,"to send back, maxage",maxage,"now ts",ts
                                
                                if (int(float(latestvalueTS))+maxage > ts): # kas on piisavalt varske see viimane leitud timestamp (string!)
                                    #value=str(int(float(value))+1) # ei saa liita, hakkabki kasvama! cmd puhul ei pea olema erinev value. 8.12.2011
                                    print "value fresh enough, sending back as",register,":",value
                                    
                                else:
                                    value='' # liiga vana vaartuse korral saadame tagasi tyhjuse
                                    print "too old value (more than maxage",maxage,", sending back empty register ",register,"value",value
                                    
                                print "inserting state value into newstate, id",id,"register",register,"value",value
                                
                                Cmd="insert into newstate(mac,register,value) values('"+id+"','"+register+"','"+value+"')"								
                                print Cmd # debug. kuid newstate sisu ei saadeta, kui see on sama mis state!?!
                                #lisame 1, et ei oleks sama...
                                try:
                                    conn.execute(Cmd)
                                    #conn.commit()
                                except:
                                    Cmd="update newstate set value='"+value+"', retrycount='7' where mac='"+id+"' and register='"+register+"'"	 # 10.12.2011
                                    # kui retrycount on 7 siis saadab 2 x enne kui 9 saab... lisaks peab saadetav register commands tabelis olema!
                                    print Cmd #lubame nyyd ootel olevate newstate vaartuste muutmist! siis ei pea kindlasti vastama vana vaartusega enne kui uue saab 
                                    conn.execute(Cmd)
                                    #conn.commit()
                                    #traceback.print_exc() 
                            								
                    # oleme state tabelis registrid ara muutnud!            
                    
            try:
                conn.commit()  # monitor transaktsiooni lopp
                #print "oleme state tabelis registrid ara muutnud! statemodify osa on edukalt loppenud"
            except:
                print "mingi commit jama enne??"
                traceback.print_exc()
                sys.stdout.flush() # et kohe logis naha oleks
                time.sleep(1)
                                
                    

                    

            if (MONLOC==""):
                print "mac "+id+" (location) puudub tabelist controller!!" # ei saada nagiosele
                
            else:
                #print 'kaivitame file4nagios parameetrimassiiviga reg ',reg # ajutine. anname registrinimede masiivi kaasa!
                file4nagios(reg) # kirjutame eraldi tabelisse nagiose teadete tegemiseks vt conn3 / oli 2 sammu eespool!!!
                # see lammutab datagrammi otsast peale laiali, seega kaovad registrinimed, mis enne msx seest eraldati. see on jama, taasta!
                
          
            
            
            #nyyd saadame vastuse newstate sisu alusel ####################################
            if "frag:" in data:   # see oli fragment, ei vasta seekord
                print "no answer to this datagram with frag:, more is coming"

            else:    # ei ole fragment, voib vastata, kui on midagi saata...
                
                kontrollerile(id,inn,addr) # teeme ja saadame vastuse, mida selle kontrolleri jaoks saata saab. 
                #lisaks uurime sama asja kasutades vastuste voimalusi ka siis, kui midagi muud teha pole parajasti!
                
        else:
            # printing data
            print t, " \nillegal message (no colon) from ", str(addr)
            print repr(data),"'\n"

            
    except: # kuna midagi vastu votta polnud, siis saadame ootel asju YHE KORRA enne kui kontroller ise neid kysib...

        print ".", # idle oleku margiks
        
        Cmd="BEGIN TRANSACTION" # newstate transaction start
        conn.execute(Cmd)
        Cmd="select newstate.mac, controller.socket, newstate.register, newstate.value, newstate.retrycount from newstate LEFT join controller on newstate.mac = controller.mac where controller.socket_ts > 10000 \
        and controller.socket <> '' and newstate.retrycount is null group by newstate.mac limit 10" # saame mac ja socketi, millega saatma hakata 
        #print Cmd
        cursor.execute(Cmd)  # read from newstate (mailbox) table
        #conn.commit()
        
        for row in cursor:
            print '\n# fast delivery for id',row[0],' socket',(row[1].split(',')[0],int(float(row[1].split(',')[1]))),'to send',row[2],row[3],'retrycount',row[4],datetime.datetime.now()
            #kontrollerile(row[0],'0',(row[1].split(',')[0],int(float(row[1].split(',')[1])))) # saime mac, inn=0, addr tuple (str,int)
            kontrollerile(row[0],'',(row[1].split(',')[0],int(float(row[1].split(',')[1])))) # see ei ole ju vastus, seega inn pole vaja saata? inn on string. 01.05.2013
            # inn=0 kontroller ei saada, seega sealt saatmata puhvrist midagi ei kustuta!
            #aga retrycount tuleks kohe suurendada!
            Cmd="update newstate set retrycount='1' where mac='"+row[0]+"' and register='"+row[2]+"'"	 # 01.05.2013
            print Cmd # debuf
            conn.execute(Cmd)
            
        conn.commit() # newstate transaction end
        sys.stdout.flush() # et kohe logis naha oleks kiired saatmised    
            
            
            
        
        #traceback.print_exc()
        #if input_lines > 20000:  # tegelikult datagrams
        #    print "program restarted after 20000 datagrams received" 
        #UDPSock.close()
        #    sys.exit()   #  et malulekked ei segaks
	


# Close socket
#UDPSock.close()
