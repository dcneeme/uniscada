#!/usr/bin/python3

# apr 2016 lisaks edasisaatmistele apiserverisse kuulata ka vastuseid ja edastada alguparasele saatjale kui seal on rohkem kui id ja in / kui seal esineb ykski in, ara saada!

# !!! esineb seni lahendamata probleem - leitud 09.02.2014. kui statusreg sisu rikkuda, naiteks 0 asemel kirj sisse 0DCV, siis seda yle ei kirjutata ja file2nagiosed
#  selle registriga seotud teenusele edaspidi ebaonnestuvad!!! monitooringus unknown, kuigi kontroller saadab korrektselt. siis vaata bnstate abil, mida state sisaldab!


# VAJA korrata vana vaartust enne uue binaarsete teenuste (1s step) uue oleku saatmist. uue oleku viivitamine due_time abil?
#  sest rrdtool oletab millegiparast, et uus olek kestis juba eelmisest olekust alates!!!

# aliase kaudu ringisuunamine ei toimi? hvv kp30. asenda id nagiosele/  alias alusel.

# 17.6.2016 mybasen saatmise voimaldamiseks kopeerime babup info tabelist monitor.controller tabelisse nagiosele0.nagiosele

import zlib  # neeme feb 2016

import time
import datetime
#from pytz import timezone
#import pytz
#utc = pytz.utc

import sqlite3
import sys
import traceback
import subprocess

from socket import *
import string

# Set the socket parameters
host = "46.183.73.35"  #  "212.47.221.86" # "195.222.15.51"
SQLDIR="/data/scada/sqlite"
port = 44445 # 44440 ## testimiseks 44444, pane parast 44445
if len(sys.argv) > 1: # ilmselt ka port antud siis
    port = int(sys.argv[1]) # muidu jaab default value 44445
    print('udp port set to',port)
    sys.stdout.flush()
    time.sleep(1)

buf = 8192 # proovime kas vastuste kadu soltub sellest  - EI SOLTU! # buf = 1024
addr = (host,port)
registration = { } # Registration dictionary
array0 = { } # CMD0 jaoks masiiv
array1 = { } # CMD1 jaoks masiiv
registers = { } # registrid jm parameetrid shelli scriptide kirjutamiseks peale update transaktsiooni
DESC = { } # descriptionid iga staatuse kohta
reg = [] #asendusarray register_alias jaoks

VALUE = "" # TEEME GLOBAALSE MUUTUJA
MONSVCTABLE = ""
STATUS = 0
#OLD_STATUS=0 # statemodify sisemine
msd = ""
mst = ""
chg = ""

DUE_TIME = 0 # tahtaeg


# Create socket and bind to address
UDPSock = socket(AF_INET,SOCK_DGRAM) # kontrollerite suund
UDPSock.settimeout(0.1) # enne oli 3! see maarab ka seelle, kui tihti ja kas yldse paaseb ootel asju saatma.
#mida vaiksem ooteaeg siin, seda suurem toenaosus et saab varem saata midagi. mujal viiteid ei ole!
UDPSock.bind(addr)

#create sqlite connections
try:
    conn = sqlite3.connect(SQLDIR+'/monitor',1) # tabelid state, controller, newstate. timeout 1 s (default on 5)
    conn2 = sqlite3.connect(SQLDIR+'/servicelog',1) # oli id_log jaoks, nyyd viimanetehing jms
    conn3 = sqlite3.connect(SQLDIR+'/alias',1) # tabel alias
    conn30 = sqlite3.connect(SQLDIR+'/nagiosele0',1) # tabel nagiosele, paaris sekunditel
    #conn31 = sqlite3.connect(SQLDIR+'/nagiosele1',1) # tabel nagiosele, paaritud sekundid
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


#pakitud sonumi testimiseks
#fz="\x1f\x8b\x08\x08=\xc3\xacU\x00\x03test.txt\x00\xa5\x93\xcdn\x1b1\x0c\x84\xefz\n>@\x0b\x88\x94Hiu3\x8c8\xc9m\x91\xd8Z \xe7^r\xc9\xfb\x1f;\xd4:\xfeM\n\xb4\x85\xb1\x908+\x8d\xa9\xd1\xb7\xef\xbfZ\x8c\x91#\x0b\x86\x14\xe9\xfd\xa3\x95\xf2\x83s*)\xd6\x89\x13\xed\xac73\xa5]\xe9-\xa7T\xe9\x89\xe7\xa5E\x8a>y\xc5\xe4I\xd6:`\xe2\xf5\xf3\xcb\xd2\x94\xe2\xe9\xf7\xfc\xe2\xea\xcc\xeb\xa6\x99G%\xc7JF\xb5\xf3\x8a\x89\x8b\xcf\xa1\x84\xd7\xb9\xb7\x9fjS\x16\xda\xc7\xa5I\x14B\x7fx2j\xdf\xb2gW\xa1$W\x0b\xea\xa1\x8a\xabyU\x05\xaa\xdb\x87\xbd\xfabe\xc8F\x8cM\x05\x0f\xc4\xb1C\xb1%OBY\xe5\xe2\xddh\xcb\xa3\xa8\xe7(2\x8c\x1ea$J\xccc\xd5\xe3p0\xb8g\x9d(M\x17\xee\xb6\xba\x9b7\x84f2\xb4\x84\x0e\xd6wkW\xe6f9\x1d\xcdl\x98\x1d\xe0\xa5jHf\xa8\x87\xe1r\x80I*r\x12Gs\xdd\xcf$R\xd5\x82\x88IB@\x92\x8a\x15\xcf)z0e\x0c}8t\x19\x8b'C\x06\x18b\xf2\xc5qDw\xb5x4\xd6\xb5\xa3g\xc9\xa8q\xf5\x12\x8d+\xa6\xe3\xf6+\xc47\xc5q\xf3\x94)s\xf6CeJ0\xa3\xc4\xd5\xf0\xce\xff\xed\xcd\x96f,\x13N]S\xc0}\x18\xe5\\*J\xe0\xf4f\x9f\xd1N\xa7hs!^\x96\xc6\xde\x83'\xc5\x8b\xaf\xd9\x1c\x89\xf1_\xf2\xfe\xc2f\x1cf#7:\x14\xd7\xb73wx\x14\xa9Ha;Ko\n\xf3T\xe8\x81\xb7\xbd\xa1w\xa3\x07\xc1L'\xec\n;\x9c\x92\x19\x8c\\\xf2\xadY\xcb\xb7|\xd3\x91o\xf4^\xe3\xb9\xf7\x1a\xfe\x03\xf8\xaa+\xf04\x80/\xf8\xbc8\\\x03\xafw\xc0\xe3\x0ec\xbd\x02^\xaf\x81\xa7K\xe0\xc3\xd7\xc03\x80\xe7[\xe0\xff\xc0\xb7E\xe7;\xdc\xf0\xedQ\xf09\x8a\xe9\x13x\xfe\x02x\xba\x02>\xfc#\xf0I\n\x10\x17\x8b\x8c\xaf\x1c\x8c\xaa\x84\xef\x81O\x1e\t\x06\x8e6\x80w\xfc\xef\x81\xa7\x13\xf0\xe1\x1ex\xfdk\xe0\xe9\x04|8\x03\x1f~\x03\xa0I=Dg\x05\x00\x00"


def decode(indata):
    if indata[0] == '\x1f'  and indata[1] == '\x8b': # gzip
        out = zlib.decompress(indata, 16+zlib.MAX_WBITS)
        print('== unpacked from b '+str(len(indata))+' to '+str(len(out)))
        return out
    else:
        return indata


def datasplit(data, addr): # split the incoming datagram into in- related pieces
    ''' tykeldab monitor50.py jaoks mitme in keyvaluega datagrammi. igasse juppi ka id!

        >>> data='id:123\nin:1,2\nI1W:1 1\nI1S:0\nin:2,3\nI1W:2 2\nI1S:1\nin:3,4\nI1W:3 3\nI1S:1\n'
        >>> datasplit(data5)
        ['id:123\nin:1,2\nI1W:1 1\nI1S:0\n', 'id:123\nin:2,3\nI1W:2 2\nI1S:1\n', 'id:123\nin:3,4\nI1W:3 3\nI1S:1\n']

        >>> data2='I1W:1 1\nI1S:0\nI1W:2 2\nI1S:1\nid:123\nin:1,2\n'
        >>> datasplit(data2)
        ['I1W:1 1\nI1S:0\nI1W:2 2\nI1S:1\nid:123\nin:1,2\n']

        >>> data3='I1W:1 1\nI1S:0\nI1W:2 2\nI1S:1\nid:123\n'
        >>> datasplit(data3)
        ['I1W:1 1\nI1S:0\nI1W:2 2\nI1S:1\nid:123\n']

    '''

    #data = decode(data) # pakib lahti kui on gzip. kui teine server ka zip toetama hakkab, tosta tahapoole
    localcopy(data) # to apiserver
    data = decode(data) ## pakib lahti kui on gzip. TEISELE SERVERILE KOOPIA ENNE SEDA

    dataout = []
    inns = []
    incount = 0
    if "id:" in data:
        lines = data[data.find("id:")+3:].splitlines()
        id = lines[0]
        incount = len(data.split('in:')) - 1 # 0 if n is missing

        if incount > 1: # with one in do not split
            for i in range(incount):
                inpos = data.find('in:')
                inn = data[inpos + 3:].splitlines()[0]
                inns.append(inn) # multi-in can be
                appdata = 'id:'+id+'\nin:'+data.split('in:')[1]
                print('datasplit',i,appdata)
                dataout.append(appdata)
                data = data[inpos+4+len(inn):] # in tagune osa
            print("got incoming message from controller id",id, 'splitted into',incount,len(dataout),'pieces')
        else:
            dataout.append(data)
            print("got incoming message from controller id",id, 'no splitting due to one or no in' )
            if incount > 0:
                inpos = data.find('in:')
                inn = data[inpos + 3:].splitlines()[0]
                inns.append(inn) # kontrollerile needs inns

        kontrollerile(id, inns, addr) # ack now, possibly w multple in values
        return dataout # list
    else:
        print('invalid data, missing id')
    return dataout # see laheb tootlemisele. vastus aga enne seda juba teele.



# salvestame nagiosele tabelisse yhe registri korraga (aga transaktsiooni sees!)
def insert2nagiosele(locregister): # siin ainult register ette, vaartuse jm omadused otsib ise. samuti ka selle, kas on value voi status.
    global MONTS, INfound, basentuple # viimane ytleb kas timestampi jalgida, kas value ja status yhes datagrammis voi ei. nagiosele saatmiseks peavad molemad olemas olema!
    #print("*** insert2nagiosele start for",locregister ## ajutine debug
    SVC_NAME = ""
    STA_REG = ""
    VAL_REG = ""
    UNIT = ""
    DIV = ""
    DESC[0] = ""
    DESC[1] = ""
    DESC[2] = ""
    DESCR = ""
    STATUS = 0
    VALUE = ""
    DUE_TIME = 0  # nagiosele saatmise tahtaeg lisatud 13.09.2009 (pikendame impulsside tagafronte vastavalt teenuse min_len parameetrile)
    MIN_LEN = 0  # minimaalne impulsi pikkus peale viimast kinnitust voi esifronti


    #   (svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step,min_len,max_val,grp_value,multiperf,multivalue)# uus variant, lopus 2 lisaks
    #Cmd="SELECT svc_name,sta_reg,val_reg,out_unit,conv_coef,desc0,desc1,desc2,step from "+MONSVCTABLE+" where \
    try:
        Cmd = "SELECT svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step,multiperf,multivalue from "+MONSVCTABLE+" where \
            sta_reg='"+locregister+"' OR val_reg='"+locregister+"'"    # oletame on multi liikmed sees
        cursor.execute(Cmd)
        #print('multi',locregister ##
    except:
        Cmd = "SELECT svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step from "+MONSVCTABLE+" where \
            sta_reg='"+locregister+"' OR val_reg='"+locregister+"'"    # me ei tea kas selles tabelis on multi liikmed sees
        cursor.execute(Cmd)
        #print('NOT multi',locregister

    for teenuseinfo in cursor:
        #print locregister,"alusel teenusetabelist",MONSVCTABLE,repr(teenuseinfo) ##
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
            #print('multivalue',MULTIVALUE
            # siin voiks None muutmine tyhjaks olla?
            if MULTIPERF == None:  # siis ei teki jama service tabelis multiperf ja multivalue NULL korral
                MULTIPERF=''
            if MULTIVALUE == None:
                MULTIVALUE='0' # pigem kyll ei saada siis yldse kontroller..

        except:
            MULTIPERF=""
            MULTIVALUE=""
            #print('monovalue'

        if (SVC_NAME == ""):
            print("tabelis",MONSVCTABLE,"puudub teenuse nimetus registrile",locregister)
            # valju funktsioonist, kuidas? kuidas mitte midagi teha (except puhul vahel vaja)  -  omista mingile dumb muutujale mingi vartus...
            #return 1 # me ei taha funktsioonist valjuda, vaid ainult selle registriga lopetada ja mitte nagiosele saata

        else: # teenuse nimetus olemas, asi tundub normaalne
            #print("saadud teenuse kohta name",SVC_NAME,'sta_reg',STA_REG,'val_reg',VAL_REG,'unit',UNIT) # ajutine
            if (STA_REG != ""): # staatus on olemas
                Cmd="SELECT value,timestamp,due_time from state where (mac='"+id+"' and register='"+STA_REG+"')"
                #print(Cmd)
                cursor.execute(Cmd) # saame yhe rea

                for stateinfo in cursor:
                    try:
                        STATUS = int(stateinfo[0]) if stateinfo[0] != '' else 0 # kui puudub sta_reg siis peaKS STATUS=0 OLEMA...
                        STA_TS = stateinfo[1] if stateinfo[1] != '' else None # tegelikult seda ei kasutata!
                    except:
                        print('assuming status=0 due to problem with '+SVC_NAME+' stateinfo: '+str(repr(stateinfo))+', host_id '+id)
                        STATUS = 0
                        #traceback.print_exc()
                        
                    if (STATUS == 0 and stateinfo[2] != None and register == STA_REG):
                        DUE_TIME=int(float(stateinfo[2])) # saatmise tahtaeg
                    else:
                        DUE_TIME=0  # pole vaja midagi venitada


                # leiame DESCR vastavalt STATUS vaartusele
                DESCR=DESC[STATUS] # olekule vastav teenusekirjeldus
                #print("statuse osa leitud",STATUS,DESCR # ajutine abi

            if (VAL_REG != ""): # value on olemas
                Cmd="SELECT value,timestamp from state where (mac='"+id+"' and register='"+VAL_REG+"')"
                #print(Cmd)
                cursor.execute(Cmd)

                for stateinfo in cursor:
                    VALUE=stateinfo[0] # peab olema string! kas on alati?
                    VAL_TS=stateinfo[1]

                #DUE_TIME = 0 # value korral ei otsi ega muuda - ei maksa varem leitut rikkuda!

                #print("VALUE",VALUE # ajutine abi

            #ehk peaks vordlema timestampe STA_TS ja VAL_TS, et erinevus ei oleks liiga suur...

            # vana value tuleks tegelikult ka lugeda... aga ehk polegi kordamist vaja, kui step 1?
            #nyyd aga on vana vaartus teada, ehk saadame varasema timestambiga? HMM...

            #print('hakkame nagiosele tabelisse salvestama' # ajutine
            for jj in range(4):
                if basentuple[jj] == None:
                    basentuple = ('','','','')
                    break

            Cmd = "insert into nagiosele(mac,nagios_ip,svc_name,status,value,desc,timestamp,conv_coef,out_unit,location,step,due_time,val_reg,multiperf,multivalue, \
                sta_reg, basen_url, basen_uid, basen_pass, basen_path) \
                values('"+id+"','"+MONIP+"','"+SVC_NAME+"','"+str(STATUS)+"','"+VALUE+"','"+DESCR+"','"+str(MONTS)+"','"+str(DIV) \
                +"','"+str(UNIT)+"','"+str(MONLOC)+"','"+str(step)+"','"+str(DUE_TIME)+"','"+VAL_REG+"','"+str(MULTIPERF)+"','"+str(MULTIVALUE) \
                +"','"+STA_REG+"','"+basentuple[0]+"','"+basentuple[1]+"','"+basentuple[2]+"','"+basentuple[3]+"')"
            #lisasin sta_reg kirjutamise nagiosele0 tabelisse  4.5.2016
            # basentuple = (babup_server, babup_user, babup_pass, babup_services) # the last one is path in fact! server contains aid!\ # 17.6.2016

            try:
                conn30.execute(Cmd) # nagiosele, KUI EI SAA, siis allpool update, muidu hilineb hiljem saabunud paarilise nagiossse saatmine
                print(locregister,MONTS,"->",SVC_NAME,str(STATUS),VALUE+"/"+str(DIV),UNIT,DESCR,basentuple)
                # nyyd voib lisada teatud teenuseid logisse eraldi tabelitesse
                if SVC_NAME == "ViimaneTehing": # servicelog faili tabelisse ViimaneTehing
                    Cmd="insert into "+SVC_NAME+"(mac,nagios_ip,status,value,timestamp,location) \
                        values('"+id+"','"+MONIP+"','"+str(STATUS)+"','"+VALUE+"','"+str(MONTS)+"','"+MONLOC+"')"
                    print('viimanetehing',Cmd) ##
                    conn2.execute(Cmd) # see peab onnestuma sama moodi kui nagiosele

            except:
                #print("see rida on nagiosele tabelis olemas, teenus ",SVC_NAME,MONTS,", update, INfound ",str(INfound) ## ajutine abi
                if INfound == 0:
                    Cmd="update nagiosele set status='"+str(STATUS)+"', value='"+VALUE+"', desc='"+DESCR+"' where svc_name='"+SVC_NAME+"' and mac='"+id+"'"
                else:
                    Cmd="update nagiosele set status='"+str(STATUS)+"', value='"+VALUE+"', desc='"+DESCR+"' where svc_name='"+SVC_NAME+"' and mac='"+id+"'"+" and timestamp='"+str(MONTS)+"'"

                # viimane nouab, et status ja value saabuksid yhe timestambiga (ja et in:inum,ts oleks kasutusel!)
                # kui timestampi ei jalgi, kirjutab viimane status ja value koik varasemad samanimelised teenused nagiosele tabelis samasugusteks!!!
                # desc update lisatud 17.6.2016

                try:
                    conn30.execute(Cmd) # uuendame andmeid hiljem saabunud paarilisega, olgu siis status voi value
                    print(locregister,MONTS,"->>",SVC_NAME,str(STATUS),VALUE+"/"+str(DIV),UNIT,DESCR)   # update onnestus
                    # samad teenused mis insert korral proovitud nyyd ka siin update teha
                    if SVC_NAME == "ViimaneTehing": # parkpay
                        Cmd="update "+SVC_NAME+" set status='"+str(STATUS)+"', value='"+VALUE+"' where mac='"+id+"' and timestamp='"+str(MONTS)+"'"
                        # ainult viimane kirje muuta, timestamp alusel! eeldame, et TRS ja TRV saabuvad yhe datagammi sees ja TRS esimesena!
                        #print(Cmd)
                        conn2.execute(Cmd) # see peab onnestuma kui nagiosele update onnestus

                except:
                    #error = str(traceback.print_exc())
                    print('!!!nagiosele insert and update error!!! locregister',locregister)
                    traceback.print_exc()
                    return 1

            #nagiosele tabelisse kirjutamine tehtud.


    return 0



#tekitame kirjeid eraldi sqlite tabelisse nagiosele, kasutades massiivina ette antud registrinimesid. UUS! ei vaata enam datagrammi uuesti labi!
def file4nagios(locreg):  # registrite massiiv parameetriks, yhine MONTS olgu
    #global bnum
    print('file4nagios, parameetriks registrinimede massiiv locreg =',locreg) # ajutine debug
    try:
        Cmd="BEGIN IMMEDIATE TRANSACTION" # iga datagrami jaoks oma transaction database nagiosele jaoks!
        conn30.execute(Cmd)  # alustame transaktsiooni nagiosele baasiga

        for i in range(len(locreg)): # kui siia on saadetud, siis paneme ta ka nagiosele tabelisse, rohkem kontrollimata.
            register = locreg[i] #
            #print('starting insert2nagiosele for register',register ##
            #value leiab insert2nagiosele ise
            try:
                insert2nagiosele(register)
                #print('insert2nagiosele done for register',register ##
            except:
                #error=str(traceback.print_exc()) # tagastab None
                print('!!!insert2nagiosele failure!!! register',register)
                traceback.print_exc()

        conn3.commit() # trans lopp - millise?nagiosele... seda ju ei kasuta?
        conn2.commit() # ViimaneTehing jm log. ilma selleta db locked. teeme alati, kuigi vaid siis vaja kui logitav teenus oli...
        conn30.commit()  # lopetame transaktsiooni sel korral taidetud nagiosele baasiga 0
        print('insert2nagiosele success')
        return 0
    except:
        print('file4nagios FAILED!!')
        traceback.print_exc()
        return 1  # file4nagios lopp



#insert voi update state. teeb ka controller locationi update kui see muutunud.
def statemodify(locregister,locvalue): #kasutame ka globaalseid muutujaid id ja ts tabeli state muutmiseks
    global MONTS
    #if locregister == 'DCS' or locregister == 'TCS':  # debug, probleemsed parkpay teenused
    #    print("statemodify() arguments (2):",locregister,locvalue," global args",id,ts

    MIN_LEN=0 # algseis min kestusele - vist pole aga siin seda vajagi?
    DUE_TIME=0 # tahtaja agseis
    OLD_STATUS=0

    # teeme kindlaks mis on sellele sta_reg jaoks vajalik minimaalne haire kestus
    #omab tahtsust vaid siis kui locvalue==0

    if locvalue == "0": # kontrolli stringi suhtes
        #print("###registri",locregister,"olek nullistumas"
        Cmd="SELECT min_len from "+MONSVCTABLE+" where sta_reg='"+locregister+"'"  # val_reg ei huvita
        #print(Cmd)
        try:
            cursor.execute(Cmd) # saame yhe rea vastuseks kui sedagi - val korral ei saa!
            for locrow in cursor:
                if MIN_LEN == None:
                    MIN_LEN = 0
                else:
                    try:
                        MIN_LEN = int(locrow[0]) # loodame et see mis siin on konverteerub kuidagi numbriks
                    except:
                        MIN_LEN = 0 # ja kui ei konverteeru olgu 0

        except:
            MIN_LEN = 0 # print(locregister," pole sta_reg vist, min_len lugemine ei onnestu")
            #traceback.print_exc()


        if MIN_LEN>0:
            #print locregister," uurimise algus, min viide",MIN_LEN

            #siin ON tegu diskreetse olekuga. kontrollime selle eelmist vaartust ja update aega state tabeli alusel
            Cmd="SELECT value,timestamp from state where register='"+locregister+"' and mac='"+id+"'" # saame eelmise oleku ja ajamargi
            #print(Cmd)
            try:
                cursor.execute(Cmd) # saame yhe rea vastuseks kui sedagi
            except:
                traceback.print_exc()

            for locrow in cursor:
                #print("locrow",locrow
                if locrow[0] != '':
                    OLD_STATUS=int(locrow[0])
                    OLD_TS=float(locrow[1]) # ehk kaotame punkti int() abil ara? ah las olla...

            #print locregister,"min viide",MIN_LEN,"OLD_STATUS",OLD_STATUS,"OLD_TS",OLD_TS,"now",ts,"vanus s",str(ts-OLD_TS)

            if (OLD_STATUS>0 and OLD_TS + MIN_LEN > MONTS): # kestus (eelmisest updatest) olnud lyhem, kui MIN_LEN
                print("###",locregister,"haire lopetamise pikendamine",OLD_TS+MIN_LEN-MONTS,"s vorra")
                DUE_TIME=OLD_TS + MIN_LEN
                #print locregister,locvalue,"paneme tahtaja",DUE_TIME
            else:
                DUE_TIME=0 # edastage viivituseta

    try:
        Cmd="INSERT INTO STATE (register,mac,value,timestamp,due_time) VALUES \
        ('"+locregister+"','"+id+"','"+str(locvalue)+"','"+str(MONTS)+"','"+str(DUE_TIME)+"')"
        #print(Cmd)
        conn.execute(Cmd) # insert, kursorit pole vaja

    except:   # UPDATE state
        Cmd="UPDATE STATE SET value='"+str(locvalue)+"',timestamp='"+str(MONTS)+"',due_time='"+str(DUE_TIME)+"' \
        WHERE mac='"+id+"' AND register='"+locregister+"'"
        #print(Cmd)

        try:
            conn.execute(Cmd) # update, kursorit pole vaja
            #print('state update done for mac',id,'register',locregister # ajutine

        except:
            traceback.print_exc()
            return 1 # kui see ka ei onnestu, on mingi jama


    return 0 # DUE_TIME  state_modify lopp





def kontrollerile(id,inn,addr): # uurime vastuse voimalikkust ja tekitame newstate sisu teadaoleva mac aadressiga kontrolleri jaoks
    global t # aga id,inn ja addr on siin lokaalsed! inn olgu string! in:0 pole vaja saata!
    #print('kontrollerile params', id,inn,addr # debug
    Cmd="BEGIN TRANSACTION" # tagasi 14.02.2013 n
    conn.execute(Cmd) # tagasi -"-

    # selleks, et ka erinevuste puudumisel voi state registris mitteesinemisel saadetaks newstate vaartus, on vaja register commands tabelisse panna!

    Cmd="select newstate.register,newstate.value from newstate LEFT join state on newstate.mac = state.mac and \
    newstate.register=state.register where ( state.value  !=  newstate.value or newstate.register in \
    (select register from commands where commands.register = newstate.register)) and  \
    (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10"

    #print(Cmd) ##
    cursor.execute(Cmd)  # read from newstate (mailbox) table

    # tom 10.6.9 retrycount on null voi vaiksem kolmest, seega pole veel nii palju retryisid tehtud.
    # kui on kolm korda saadetud, siis enam ei proovita, samas kui tehakse uued vaartused setupi poolt,
    # tuleb kindlasti ka retry count 1-ks panna voi jatta nulliks. Samas voib ka triger need ara tappa kui
    # monel on retrycount >= 9

    # saatmine on juhitav commands tabeli kaudu! siis ei kontrollita erinevust state tabelis olevast sisust

    #tuleb saata vaid need, mis erinevad state tabelis olevatest, siis saab yhe flash kirjutamisega hakkama 5 asemel
    #korraga ei tohi saata yle 10 muutuja, ei mahu kontrolleris input stringi!
    #saadetud kaovad newstate tabelist triggeri abil ara (kontrollerist saadetakse nende kohta vastus state tabelisse)
    #ja siis saab jargmise portsu saata kui vaja. jargmine muutujate listing antakse peale salvestamist vist??


    #SAADAME TEATEID KONTROLLERILE NEWSTATE TABELI SISU ALUSEL
    #sdata = "id:" + id + "\n" # alustame vastust id-ga

    sdata = "id:" + id + "\n"
    for ins in inn:
        sdata +=  "in:" + ins + "\n" # mitu in yhes sonumis kontrollerile. no ading if no members in inn!
    print('ack kontrollerile', sdata)

    answerlines = 0
    for row in cursor:
        #print("select for sending to controller newstate left join state row",row
        register=row[0]
        value=row[1]
        sdata=sdata + str(register) + ":" + str(value) + "\n"
        answerlines = answerlines + 1


    #kas lisaks veel midagi saata on?
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
        newstate.register=state.register where ( state.value  !=  newstate.value or newstate.register in \
        (select register from commands where commands.register = newstate.register)) and \
        (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10 \
        ) \
        ) is null  THEN 1 ELSE \
        ( select max(retrycount)+1 from newstate where mac='" + str(id) + "' \
        and mac||register in ( \
        select newstate.mac||newstate.register from newstate LEFT join state on newstate.mac = state.mac and \
        newstate.register=state.register where ( state.value  !=  newstate.value or newstate.register in \
        (select register from commands where commands.register = newstate.register)) and \
        (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10 \
        ) \
        )  END \
        ) \
        where mac||register in ( \
        select newstate.mac||newstate.register from newstate LEFT join state on newstate.mac = state.mac and \
        newstate.register=state.register where ( state.value  !=  newstate.value or newstate.register in \
        (select register from commands where commands.register = newstate.register)) and  \
        (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10 \
        ) ;"

        conn.execute(Cmd)

    conn.commit() # end transaction


    t = datetime.datetime.now() # votame vastamise aja
    print("---answer or command to the controller ",id,addr,t) #
    print(sdata)
    UDPSock.sendto(sdata,addr)  # ID SAADAME KA SIIS KUI MUUD SAATA POLE

# kontrollerile() lopp



def svcadd_calc(register,value,mac): # arvutame kumulatiivse alusel loodud lisateenustele juurdekasvud alates salvestatud algvaartusest
    #perioodi algseisud asuvad kumul teenuse algusega teenustes, mille lopus on number vahemikust 0..4 (y,m,w,d,h)
    #NB - lisanduvate teenuste jaoks peab status olemas olema, muidu ei saadeta nagiosele. praegu salvestab crontab_svcadd.py koikjale 0 kuhu algseisu paneb.
    #ei hakka jamama kui ei ole tegu sellise teenusega mida tootlema peaks!
    outsvcnames=['','','','',''] # 5 stringi y m w d h - see voidakse asendada
    outsvcvalues=['','','','',''] # 5 stringi y m w d h
    endvalue=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # kuni 15 liiget esialgu arvestatud. E ja W algusega teised teenused ronivad ka siia sisse... 9 ei mahtunud! tartulv
    svcfound=0 # any added services found?
    found=0 # liikmete leidmine?

    #valcount=len(value.split(' ')) # liikmete arv kindlaks teha, korrata sama arvu igas vastuses. 1 voi 2 enamasti
    #print('svcadd_calc: valcount',valcount,'endvalues', # debug
    #for valnum in range(valcount): # leime yksikvaartused kumulatiivsest
    #    endvalue[valnum]=int(float(value.split(' ')[valnum])) # teeme numbrid stringijupist

    Cmd="select * from svcadd where svc_c='"+register+"'" # saame katte sisendteenusele vastavad juurdegenereeritavad. tyhjus, mida vaja pole.
    #print(Cmd) # debug
    cursor.execute(Cmd)
    for row in cursor: # yks rida vastuseks kui yldse vastust tuli. row[6] ei kasuta, liikmete arvu saame sisendi alusel
        svcfound=1 # midagi on
        outsvcnames=[row[1],row[2],row[3],row[4],row[5]] # vaid siis asendab esialgsed tyhikud, kui tabelist midagi leiti. siin ei ole esialgset (row[0])
        outsvcvalues=['','','','',''] # algseis

        #### jargmine loik espolt siia @@@@@
        valcount=len(value.split(' ')) # liikmete arv kindlaks teha, korrata sama arvu igas vastuses. 1 voi 2 enamasti
        #print('svcadd_calc: valcount',valcount,'endvalues', # debug
        for valnum in range(valcount): # leime yksikvaartused kumulatiivsest
            endvalue[valnum]=int(float(value.split(' ')[valnum])) # teeme numbrid stringijupist, viimased vaartused
        #####

        #print('processing beginvalues for services',outsvcnames # debug
        for addnum in range(5): # erinevad algseisud selle teenuse ja mac jaoks, 0=y, 1=m, 2=w, 3=d, 4=h. koiki ei pruugi olla, siis tee. voivad olla mitme liikmega.
            if outsvcnames[addnum] != '': # on vaja arvutada
                found=0 # need to know if there was any begin value(s), replace with valcount zeroes if not
                beginvalue=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # yksikud liikmed max 8... voiks ka append kasutada.
                outvalue=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # need valjastame. arvestame kuni 8 liikmega esialgu1
                outvalues='' # string
                Cmd="select value from state where register='"+register[:-1]+str(addnum)+"' and mac='"+mac+"'" # saame katte xyN algseisu selle perioodi jaoks
                #print(Cmd) # debug
                try:
                    cursor.execute(Cmd) # otsime algseisu lisateenusele
                    for row in cursor: # tuleb 1 vastus kui yldse. kui ei tule, ei ole algseisu olemas! crontab_svcadd peaks tekitama perioodi vahetusel!
                        found=1 # algseis outsvcnames[addnum] jaoks leitud state tabelist
                    if found == 1: # PERIOODI ALGREGISTER ON STATE TABELIS OLEMAS
                        if row[0]  != '' and row[0]  != ' ' and valcount>0: # ei ole tyhi sisu, see beginvalue on olemas
                            print('##register, value,valcount',register,value,valcount) # debug
                            for valnum in range(valcount): # leiame koik beginvalue liikmed oma vaartustega
                                try:
                                    beginvalue[valnum]=int(float(row[0].split(' ')[valnum])) # teeme numbri stringijupist, muidu jaab 0 perioodi algusvaartus
                                    #print('svcadd valnum beginvalue, endvalue',valnum,beginvalue[valnum],endvalue[valnum] # debug
                                except:
                                    print('beginvalue failure, valnum,valcount',valnum,valcount)
                                    traceback.print_exc()

                                if endvalue[valnum] >= beginvalue[valnum]: # on juurdekasv. kui ei ole, saadame liikme vaartuse 0
                                    outvalue[valnum]=endvalue[valnum]-beginvalue[valnum] # lahutame perioodi algseisu. kui beginvalue puudub, on ta 0.
                                    #print outvalue,
                                else: # kumul alla algvaartuse. vordsustame algvaartuse kumulatiivsega, kuigi tegelikult tuleks vist hoopis kumulatiivset suurendada...
                                    msg='beginvalue in register '+register[:-1]+str(addnum)+' less than cumulative value! setting all members to cumulative '+value
                                    Cmd="update state set value='"+value+"' where register='"+register[:-1]+str(addnum)+"' and mac='"+mac+"'"
                                    print(Cmd)
                                    conn.execute(Cmd)

                                if valnum>0: # lisa tyhik
                                    outvalues=outvalues+' '
                                outvalues=outvalues+str(int(outvalue[valnum])) # teeme stringi lisateenuse vaartuseks, voib mitut numbrit sisaldada
                            outsvcvalues[addnum]=outvalues # asendame need vaartused mis ei ole tyhjad, ylejaanud jaavad tyhjaks nagu nad tsykli alguseski olid

                        else: # algvaartuse register on olemas, aga sisu tyhi - vordsustame kumulatiivsega ja salvestame state registrisse
                            print('svcadd algvaartust '+register[:-1]+str(addnum)+' pole, salvestame')
                            try:
                                Cmd="insert into state(mac,register,value) values('"+mac+"','"+register[:-1]+str(addnum)+"','"+value+"')" # salvesta loppvaartus
                                conn.execute(Cmd)
                            except:
                                Cmd="update state set value='"+value+"' where register='"+register[:-1]+str(addnum)+"' and mac='"+mac+"'"
                                conn.execute(Cmd)
                            print(Cmd) # debug

                    else: # algolek selle teenuse jaoks puudus, TEKITAME!
                        msg='no beginvalue in state for service '+register[:-1]+str(addnum)+', will be inserted'
                        print(msg)
                        Cmd="insert into state(mac,register,value) values('"+mac+"','"+register[:-1]+str(addnum)+"','"+value+"')" # value on string, voib olla mitme liikmega
                        print(Cmd) # debug
                        try:
                            conn.execute(Cmd)
                            print('beginvalue ',value,'of a addsvc period inserted into state for mac',mac,'svc',register[:-1]+str(addnum))
                        except:
                            traceback.print_exc()
                        sys.stdout.flush()

                    #outsvcvalues[addnum]=outvalues # jama eoi saada, jargmisega teatega peaks juba korda minema

                except:
                    print('svcadd_calc() problem for register',register)
                    traceback.print_exc()
                    sys.stdout.flush()
                    outsvcvalues=['','','','',''] # error indication
                    #time.sleep(1)

    #print('svcadd:',id,register,outsvcnames,outsvcvalues # debug
    return outsvcnames,outsvcvalues # osa vaartusi asendati, ylejaanud ''

# svcadd_calc lopp, perioodi kohta juurdekasvude genereerimine yhe kumulatiivse teenuse alusel


def localcopy(data): # testimiseks koopia teise porti
    addr_port=('91.236.222.107', 44444) # apiserver
    localsocket.sendto(data,addr_port)
    print("udp localcopy--> from ",addr,"to",addr_port,data) # will be forwarded to


def apiforward(): # listen to the response from apiserver
    ''' forward the datagrams with id:000* wich contain more than just id and in to newstate '''
    need2fwd = False
    lines = ''
    id = ''
    try:
        loclines = localsocket.recvfrom(buf)[0].splitlines() # addr osa vastuses ei kasuta
        #print('got something from apiserver: '+str(loclines))
    except:
        traceback.print_exc()
        return None

    for locline in loclines:
        key, val = locline.split(':')
        if key == 'id':
            id = val
        elif key == 'in':
            pass
        else: # this localresponse is longer that just id or id+in
            need2fwd = True
            print('from apiserver (key, val) to forward: '+str((key,val))+', id'+id)

    if not need2fwd or (not '0001013000' in id and not '000000000001' in id):  # only forward apiserver responses to karla hosts and testhost
        return None

    # siit edasi vaja edastada. id olemas.
    print('from apiserver filtered response: '+str(loclines))
    Cmd="BEGIN IMMEDIATE TRANSACTION"
    conn.execute(Cmd)
    for locline in loclines:
        if not 'id:' in locline:
            loc = locline.split(':')
            register = loc[0]
            value = loc[1]

            print("inserting apiserver response into newstate, id",id,"register",register,"value",value)
            Cmd="insert into newstate(mac,register,value) values('"+id+"','"+register+"','"+value+"')"
            #print(Cmd) #
            try:
                conn.execute(Cmd)
                #conn.commit()
            except:
                Cmd="update newstate set value='"+value+"', retrycount='7' where mac='"+id+"' and register='"+register+"'"	 # 10.12.2011
                # kui retrycount on 7 siis saadab 2 x enne kui 9 saab... lisaks peab saadetav register commands tabelis olema!
                print(Cmd) #lubame nyyd ootel olevate newstate vaartuste muutmist! siis ei pea kindlasti vastama vana vaartusega enne kui uue saab
                conn.execute(Cmd)

    try:
        conn.commit()  # monitor transaktsiooni lopp
        print('apiserveri vastuse newstate tabelisse panemine OK')
    except:
        print('apiserveri vastuse newstate tabelisse panemise JAMA!')
        traceback.print_exc()





# ### protseduuuride defineerimise lopp ############################################







# #############################################################
# #################### MAIN ###################################
# #############################################################

localsocket = socket(AF_INET,SOCK_DGRAM) # for copies to apiserver
localsocket.settimeout(0.1) # response timeout from apiserver
basentuple = ('','','','') # mybasen info kandmiseks nagiosele tabelisse

# Receive messages
while 1:
    MONLOC="???" # algseis, kirjutatakse yle kui juba esineb controller tabelis
    NEWSOCKET=""
    inn=""
    try: # kas on infot udp sisendpuhvris, ootame timeout vorra mis alguses defineeritud. kui ei ole, saatma!
        datagram, addr = UDPSock.recvfrom(buf) # siin nyyde viide 0,1 s varasema 3 asemel. kui midagi ple tulnud, uuri kas on midagi saata vaja...
        #input_lines=input_lines+1
        #print("got message from addr: ",addr
        t = datetime.datetime.now()  #  datagrami saabumise aeg. allpool teeme sekunditeks
        ts = time.mktime(t.timetuple()) #sekundid praegu
        MONTS = str(int(ts)) ## punktita, voib olla ka kontrollerilt saadud aeg!!! taastamiseks kasutatav
        INfound = 0 # esialgu oletame int in: pole

        bnum = 0 # bnum=int(ts)%2 # 0 voi 1 soltuvalt jooksvast sekundist, paaris voi paaritu # proovime YHTE!
        # nagiosele1 lihtsalt kasutuseta...

        if (addr[1] < 1 or addr[1] > 65536):
            print("illegal source port " + str(addr[1]) + " in the message received from " + addr[0])

        indata = datasplit(datagram, addr) # split the incoming datagram into in-related pieces
        for data in indata: # splits into pieces with id and in if the latter exists
            print("processing data block from controller:", repr(data))
            if "id:" in data:
                lines=data[data.find("id:")+3:].splitlines()   # vaikesed tahed
                id = lines[0] # mac
                #print(" got incoming datagram (part) from controller id",id   # seda korratakse allpool nagunii

                if "in:" in data:
                    lines=data[data.find("in:")+3:].splitlines()   # vaikesed tahed
                    inn=lines[0]  # paketi jrk tunnus, voib sisaldada ka ts
                    if "," in inn:
                        if int(inn.split(',')[1]) > 1432645565:
                            MONTS = int(inn.split(',')[1]) # replace MONTS with controller time!
                            INfound = 1 # kontrolleri ts kasutusel, value ja status koos yhes datagrammis
                            print('... MONTS replaced with controller time '+str(MONTS))
                    else:
                        if int(inn) > 1432645565:
                            MONTS = int(inn) # the whole in can be a timestamp as well!

                NEWSOCKET = addr[0]+","+str(addr[1]) # ip,port kust tuli
                #print("newsocket ",NEWSOCKET  # salvestamiseks controller tabelis vaja

                print("\nprocessing data from controller",id, t, ", in:", inn, str(repr(data)))


                MONLOC=""
                SOCKET=""
                #korjame kokku locationi, kaivitatava sh scripti jm vajaliku

                Cmd="BEGIN IMMEDIATE TRANSACTION" # iga datagrami jaoks oma transaction monitor andmebaasi jaoks! tabelis controller, state, newstate, svcadd...
                conn.execute(Cmd)
                Cmd="SELECT servicetable,nagios_ip,location,socket, babup_user, babup_pass, babup_server, babup_services FROM controller WHERE mac='"+id+"'"
                cursor.execute(Cmd)
                for row in cursor: # peab tulema 1 rida
                    #MONEXE=row[0]
                    #MONEXE="/srv/scada/scripts/pumplad/haapsalu19"  # seda enam ei kasuta
                    MONSVCTABLE=row[0] # see maarab teenuste nimed ja keele
                    MONIP=row[1] # millisele nagiosele saata
                    MONLOC=row[2] # kus asub controller tabeli info alusel
                    SOCKET=row[3] # mis port ja aadress selle mac jaoks saadab
                    #basentuple = (babup_server, babup_user, babup_pass, babup_services) # the last one is path in fact! server contains aid!
                    basentuple = (row[6], row[4], row[5], row[7]) # the last one is path in fact! server contains aid!
                cursor.close() # voib ka mitte teha

                if (MONLOC != ""):  # asukoht controller tabelis olemas
                    ##pass 
                    print("\n ...processing data from",id,MONLOC,basentuple)  # str(datetime.datetime.now()) # alustame logis uut portsu
                else:
                    print("non-registered controller mac",id)

                if (SOCKET != NEWSOCKET):  # kust tuli viimane info on ka controller tabelis olemas, sh ka timestamp
                    #print("going to update controller registration data for mac",id,SOCKET,"->",NEWSOCKET
                    Cmd = "UPDATE controller SET socket='"+NEWSOCKET+"',socket_ts='"+str(MONTS)+"' WHERE mac='"+id+"'"
                    #print(Cmd) ## cursor.execute(Cmd) # saame yhe rea vastuseks kui sedagi

                    try:
                        conn.execute(Cmd)
                        #conn.commit() # see alles teeb tegelikult, ilma ei salvestu
                    except:
                        print("FAILED to update controller registration data for mac",id,SOCKET,"->",NEWSOCKET)
                        traceback.print_exc()
                    #print("updated or not controller registration data for mac",id,"done" ##
                #cursor.close()



                #SISENDINFO TOOTLUS KEY:VALUE PAARIDE HAAVAL
                #print('key value processing' ###

                lines = data.splitlines()
                reg = [] # tyhjaks, et teenuste registrinimed sisse panna
                #inns = [] # in: values list to send to controller in one datagram
                #print('ridu',len(lines) ##
                for i in range(len(lines)):
                    if ":" in lines[i]: # eraldaja peab olema
                        #print("   ",i,lines[i]
                        line = lines[i].split(':')
                        register = line[0]
                        value = line[1]
                        if value == '':
                            value = ' ' # tyhikuga kaitub paremine kui tyhjusega...
                            print("tyhjuse asendus tyhikuga registri",register,"jaoks")

                        #print("  got reg val ", register, str(value),"for mac",id ## ajutine ####


                        try:
                            if (register  !=  "id" and register  !=  "in" and register  !=  "chg" and register  !=  "frag" and value[0]  !=  "?"): # loetletud variantide korral state uuendamist ei toimu
                                #print("ei ole ka id ega in ega frag ega kyssa, register",register   ## ajutine
                                #kontrollime aliast ja muudame register nime kui vaja, ykshaaval nii sta kui val jaoks. aliase tabelis neil vahet ei tehta!
                                #Cmd="SELECT outregister from controller_service_alias where (mac='"+id+"' and inregister='"+register+"')" # n 21.02.2016
                                Cmd="SELECT outregister, mac from controller_service_alias where inregister='"+register+"'" # n 18.6.2016 voimaldame ka koikide teenuste asendust
                                cursor.execute(Cmd)
                                for row in cursor: # peab tulema 1 rida kui yldse tuleb
                                    newregister = row[0]
                                    idlike = row[1]
                                    if newregister != '' and (idlike in id): # aliases antud mac osaline match voimalik nt alguse alusel. tyhjus matchib koigega!
                                        print("replacing register",register,"with service alias",newregister,value,"for mac ",id)  # service alias only!
                                        register = newregister

                                cursor.close()
                                # siia vahele tsykkel addsvc abil uute teenuste lisamiseks 23.04.2013. peab algama W voi E-ga
                                # statemodify tuleb labi teha nii jooksva teenusega kui ka voimalike lisadega
                                addregister=['','','','',''] # registrid ja nende vaartused y m w d h
                                addvalue=['','','','','']
                                addrange=1 # see tekitab vaid svcnum 0, mis ei muuda midagi



                                if register[-1] == 'V' or register[-1] == 'W': # lisateenuste juurdetegemine kumulatiivse sisendi alusel, vaid perfdata olemasolul
                                    #vesi, elekter, side kumul. aga UTW, TCW? kontrolli parem tabelist svcadd tabelist...
                                    #print('possible service addition based on register,value',register,value  # avoid those not in addsvc table!
                                    # proovime nyyd alati kas on teenuseid paljundada vaja kumulatiivsete mingi ajavahemiku kohta
                                    print('trying svcadd_calc() with register',register,value,id) ## debug

                                    try:
                                        addkompott=svcadd_calc(register,value,id) # params strings. returns added registers,values ([],[])
                                        addregister=addkompott[0] # esimene osa vastusest, lisanduvad registrid
                                        addvalue=addkompott[1] # teine osa vastusest, vaartused nende registrite jaoks (voivad olla multivalue)
                                        if addregister != ['','','','','']:
                                            addrange=6 # esimene on originaal ja sinna otsa 5 lisa
                                            #print('svcadd_calc() returned',addkompott,'for mac',id,'register',register ##,addregister,addvalue ##

                                            #print('going to execute statemodify in loop for range',addrange # debug

                                            aregister=''
                                            avalue='' #added register value to be used below
                                            for svcnum in range(addrange): # 0 voi 0..6. liige 0 on alati olemas, originaalteenus!! 1..5 vastab aga added 0..4
                                                #print('svcnum',svcnum
                                                if svcnum>0: # registri ja value asendus - ei ole enam originaalteenus, see saadetakse esimesena muutmata kujul 0 puhul
                                                    aregister=addregister[svcnum-1] # register statemodify jaoks
                                                    if aregister != '': # tyhjus tahendab, et ei ole vaja seda varianti saata y m w d h hulgast num 0 1 2 3 4
                                                        avalue=addvalue[svcnum-1] # voib olla multivalue siin
                                                        print('svcadd produced added register,value',aregister,avalue) #,'based on addvalue',addvalue ###########################################
                                                        statemodify(aregister,avalue) # seda voib teha ainult siis, kui reg tyhi ei ole.
                                                        reg.append(aregister) # file4nagiose jaoks moeldud arraysse, registrinimede massiiv
                                                        print(" --- statemodify done for",id,aregister,avalue,DUE_TIME) # lisatud teenused
                                        #else:
                                            #print('svcadd_calc() FAILED for mac',id,'register',register # there was nothing to add

                                    except:
                                        print('failed svcadd_calc() for register',register)
                                        traceback.print_exc()
                                        sys.stdout.flush() # et kohe logis naha oleks

                                #else:
                                    #print('no need for svcadd_calc for id,register',id,register # debug


                                if register != '': # see siin on algne register, mis samuti uuendamist vajab
                                    #print(" --- going to execute statemodify for",id,register,value,DUE_TIME # POV ei joudnud siia kui val oli tyhi??? ####
                                    try:
                                        result = statemodify(register,value) # seda voib teha ainult siis, kui reg tyhi ei ole.
                                    #if result == 0: # edukas
                                        print(" --- statemodify done for",id,register,value,) # DUE_TIME # ei joudnud siia kui val oli tyhi??? ####
                                        reg.append(register) # file4nagiose jaoks moeldud arraysse, registrinimede massiiv
                                        print(" - reg.append done ",) # DUE_TIME # ei joudnud siia kui val oli tyhi??? ####
                                        if DUE_TIME>0:
                                            print(", added delay",DUE_TIME-ts,"s")
                                        else:
                                            print
                                    except:
                                        print("statemodify failed for",id,register,value)
                                        traceback.print_exc()

                            else: # state uuendamisele mittekuuluvad registrid voi vaartused - lisame siia dec 2011 ka aliasmac alusel info! ###LASTCHG below! ####
                                #print("state uuendamisele mittekuuluv register",register,"sest reg value on ",value[0] # ajutine
                                if value[0] == "?": # saadame tagasi selle registri viimase vaartuse, mis ei tohi olla vanem kui kysimargi taga olev sek vaartus
                                    # kui on vanem, saadame tagasi tyhjuse! kui nr ? taga  puudub, saadame ykskoik kui vana vaartuse.
                                    if len(value)>1:
                                        maxage=int(float(value[1:])) # sellest vanemaid vaartusi ei taha, siis tulgu vastuseks tyhjus
                                    else:
                                        maxage=315360000 # 10 aastat sekundites

                                    Cmd="SELECT mac from alias where (aliasmac='"+id+"')" # kas on mac ringisuunamisi olnud aliasmac peale, mis on jooksev id.
                                    #print("cmd for alias search",Cmd # ajutine

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

                                    print("cmd for state value over aliases: ",Cmd) # ajutine
                                    cursor.execute(Cmd) # state tabeli kallal kaidud

                                    for row in cursor: # peab tulema 1 rida yhe timestambiga
                                        latestvalueTS=row[0] # see on string!

                                    Cmd="select value from state where register='"+register+"' and timestamp='"+latestvalueTS+"'" #leiame viimase vaartuse yle mitme maci
                                    #print("cmd for value select over aliases:",Cmd # ajutine
                                    try:
                                        cursor.execute(Cmd) # state tabeli kallal kaidud, saadud yks varskeim value

                                        for row in cursor: # peab tulema ainult 1 rida
                                            value=row[0] # see on varskeim vaartus mis saada on
                                            print("got value",value," over aliases for register",register,"with timestamp",latestvalueTS,"to send back")

                                    except:
                                        print('failed cursor.execute(Cmd) for register',register)

                                    cursor.close()

                                    print("still got the value",value," over aliases for register",register,"with timestamp",latestvalueTS,"to send back, maxage",maxage,"now ts",ts)

                                    if (int(float(latestvalueTS))+maxage > ts): # kas on piisavalt varske see viimane leitud timestamp (string!)
                                        #value=str(int(float(value))+1) # ei saa liita, hakkabki kasvama! cmd puhul ei pea olema erinev value. 8.12.2011
                                        print("value fresh enough, sending back as",register,":",value)

                                    else:
                                        value='' # liiga vana vaartuse korral saadame tagasi tyhjuse
                                        print("too old value (more than maxage",maxage,", sending back empty register ",register,"value",value)

                                    print("inserting state value into newstate, id",id,"register",register,"value",value)

                                    Cmd="insert into newstate(mac,register,value) values('"+id+"','"+register+"','"+value+"')"
                                    print(Cmd) # debug. kuid newstate sisu ei saadeta, kui see on sama mis state!?!
                                    #lisame 1, et ei oleks sama...
                                    try:
                                        conn.execute(Cmd)
                                        #conn.commit()
                                    except:
                                        Cmd="update newstate set value='"+value+"', retrycount='7' where mac='"+id+"' and register='"+register+"'"	 # 10.12.2011
                                        # kui retrycount on 7 siis saadab 2 x enne kui 9 saab... lisaks peab saadetav register commands tabelis olema!
                                        print(Cmd) #lubame nyyd ootel olevate newstate vaartuste muutmist! siis ei pea kindlasti vastama vana vaartusega enne kui uue saab
                                        conn.execute(Cmd)

                        # oleme state tabelis registrid ara muutnud!
                        except:
                            print('mingi jama')
                            traceback.print_exc()

                try:
                    conn.commit()  # monitor transaktsiooni lopp
                    print("data transaction end, inn",inn, "MONTS",MONTS) ##
                except:
                    print("PROBLEM! mingi commit jama??")
                    traceback.print_exc()
                    sys.stdout.flush() # et kohe logis naha oleks
                    time.sleep(1)





                if (MONLOC == ""):
                    print("mac "+id+" (location) puudub tabelist controller!!") # ei saada nagiosele

                else:
                    #print('kaivitame file4nagios parameetrimassiiviga reg ',reg # ajutine. anname registrinimede masiivi kaasa!
                    file4nagios(reg) # kirjutame eraldi tabelisse nagiose teadete tegemiseks vt conn3 / oli 2 sammu eespool!!!



                #nyyd saadame vastuse newstate sisu alusel ####################################
                #if "frag:" in data:   # see oli fragment, ei vasta seekord
                #    print("no answer to this datagram with frag:"

                #if inn != '':    # ei ole fragment, voib vastata, kui on midagi saata...
                #    inns.append(inn) # str


            else:
                # printing data
                print(t, " \nillegal message (no colon) from ", str(addr))
                print(repr(data),"'\n")
        # end data piece processing
        #print('inns ready:',inns
        #kontrollerile(id,inns,addr) # juba datasplit juures tehtud!
        #lisaks uurime sama asja kasutades kontrollerile saatmise vajadust ka siis, kui midagi muud teha pole parajasti!


    except: # kuna midagi vastu votta polnud, siis saadame ootel asju YHE KORRA enne kui kontroller ise neid kysib...
        apiforward()  # 16.4.2016 lisatud apiserveri vastuse edastamine karlasse

        print(".",) # idle oleku margiks

        Cmd="BEGIN TRANSACTION" # newstate transaction start
        conn.execute(Cmd)
        Cmd="select newstate.mac, controller.socket, newstate.register, newstate.value, newstate.retrycount from newstate LEFT join controller on newstate.mac = controller.mac where controller.socket_ts > 10000 \
        and controller.socket  !=  '' and newstate.retrycount is null group by newstate.mac limit 10" # saame mac ja socketi, millega saatma hakata
        #print(Cmd)
        cursor.execute(Cmd)  # read from newstate (mailbox) table
        #conn.commit()

        for row in cursor:
            print('\n# fast delivery for id',row[0],' socket',(row[1].split(',')[0],int(float(row[1].split(',')[1]))),'to send',row[2],row[3],'retrycount',row[4],datetime.datetime.now())
            #kontrollerile(row[0],'0',(row[1].split(',')[0],int(float(row[1].split(',')[1])))) # saime mac, inn=0, addr tuple (str,int)
            lid = row[0]
            linn = '' # cmd not ack
            laddr = row[1].split(',')[0], int(float(row[1].split(',')[1]))
            print('..kontrollerile params',lid,linn,laddr)
            try:
                kontrollerile(lid, linn, laddr) # see ei ole ack, seega inn pole vaja saata!
            except:
                print('problem with fast delivery to id '+lid+' using kontrollerile()')
                traceback.print_exc()

            #aga retrycount tuleks kohe suurendada!
            Cmd="update newstate set retrycount='1' where mac='"+row[0]+"' and register='"+row[2]+"'"	 # 01.05.2013
            print(Cmd) # debug
            conn.execute(Cmd)

        conn.commit() # newstate transaction end
        sys.stdout.flush() # et kohe logis naha oleks kiired saatmised




## END ##