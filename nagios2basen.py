# saadame tabelist nagios0.nagiosele SOOME SERVERIS sonumid nagiosse ja/voi mybasen
# SELLE voib debugimiseks ka paralleelselt teise nagiosele scriptiga kaima lasta! jagavad tabeli 'nagiosele' kirjeid nagu juhtub.
# aga siis peaks mac alusel filtreerima et mitte koikide hostide graafikuid rikkuda... kommenteeri sendnagios line 338

# 02.10.2011 viimane muudatus enne 30: TS ja CF vahelejatmine soltuma nagios serverist, controller tabeli info alusel
# nyyd aga samamoodi kui enne oli TS js CF lisada xyE info!
# 16.10.2011 hilistada nagiosele saatmist 1 s vorra, et nii xxS kui xxV oleks kohale joudnud!
# 17.10.2011 edasiarendus nagiosele27zone.py alusel, kasutusele laiendatud olekuvaartused
# selle mote on extended info edastamine, lisagraafikute tegemiseks naiteks pumbarikete selgituseks.
# kui val_reg nimi lopus W, siis service tabelis olgu multiperf ja multidata
# tabelisse nagiosele pannakse siis value osasse mitu tyhikuga eraldatud numbrit, mille tahendused multiperf tulbas.
# nagiosele saadetakse perf dataks neist numbritest desc taha see (voi need), mille jrk 1... on antud tulbas multidata.
# 18.10.2011 palju parandusi. vanade teenustega ok. uus (multiperf) ei taha kohe minna...
# parandusi veel 19.10.2011
# 26.11.2011 alias tabelisse lisatulp direction, yhesuunaliseks asenduseks kui direction=1, st liidab eri kontrollerite infot. nagiosele32.py
# 26.08.2012 ts js cf ei saada uude serverisse koopiana
# 15.10.2012 koopia uue termnet serveri peale, nyyd siis udp porti 50000 korraga saatmine 212.47.221.86 ja 46.183.73.35
# 17.10.2012 uues serveris infokadu 10% zone omaga vorreldes! proovime ka tcp kasutada saatmisel uude, port 500001

# 06.01.2013 nsca protokoll kasutusele udp asemel nagiosele saatmiseks. port 50001
#07.01.2013 nsca saatmine ridahaaval on surmavalt aeglane, prooviks ssh kaudu mitu rida korraga - send_ssh
#08.01.2012 ssh kasutusele udp asemel! subprocess kaudu, hulk ridu korraga reavahetusega eraldatult nagiose nagios.cmd torusse
#22.03.2013 TS= saatmine maha, CF ka!
#13.5.2016 lisaks siia nagios.py testi tegeliku infoga / otsi vigu!

# 17.06.2016 lisatud nagiosele tabelisse  basen_url, basen_uid, basen_pass, basen_path
# 18.6.2016 class tehtud. saatma ka mybasen serverile. tornado ioloop, async side mybasen, python3!



import time
import datetime
#from pytz import timezone
#import pytz
#utc = pytz.utc
import decimal

#from pysqlite2 import dbapi2 as sqlite3
#import sqlite3
#from sqlite3 import dbapi2 as sqlite3 # basen serveris nii vaja
import sqlite3 # basen serveris nii vaja
import sys
import traceback
import subprocess

from socket import *
import string

import logging
try:
    import chromalog # colored
    chromalog.basicConfig(level=logging.INFO, format='%(name)-30s: %(asctime)s %(levelname)s %(message)s')
except: # ImportError:
    logging.basicConfig(format='%(name)-30s: %(asctime)s %(levelname)s %(message)s') # 30 on laius
    print('warning - chromalog and colorama probably not installed...')
log = logging.getLogger(__name__)



from nagios import * # nagios message
from mybasen_send import * # basen platform
from periodiccallback import PeriodicCallback # tornado

location="" # globaalne muutuja vajalik
location="" # globaalne muutuja vajalik
step="" # CF jaoks, tuleb service tabeli kaudu
perftype="" # multi voi puudub



class Buffer2Platforms(object):  ################################################################################
    ''' send data to monitoring platform, either nagios and/or mybasen, according to controller cfg '''
    def __init__(self):
        self.n = NagiosMessage('host_dummy', debug_svc = True) # # use self.n.convert() to get nagios messages
        self.m = MyBasenSend() # use m.convert() to get mybasen messages
        self.mybasen = False
        self.mybasen_rows = []
        self.basentuple = (None, None, None, None)
        self.conna = sqlite3.connect('/srv/scada/sqlite/alias',2) # siit ainult alias kasutusel!
        self.conna.text_factory = str # tapitahtede karjumise vastu
        self.conn = sqlite3.connect('/srv/scada/sqlite/nagiosele0',2) # timeout 2 s (default on 5)
        self.conn.text_factory = str
        self.conn.execute("PRAGMA synchronous=0")  # et kiirem oleks ja kogu aeg ei kirjutaks kettale
        self.conn.commit()
        self.loop = tornado.ioloop.IOLoop.instance()
        self.send_scheduler = PeriodicCallback(self.tegutseme, 500, io_loop = self.loop) # send every 500 ms
        self.send_scheduler.start()
        log.info('class Buffer2Platforms init done')


    def send_ssh2(self, send_string):# selle kaudu saadame nagiosele!
        exec_cmd='/srv/scada/bin/send_ssh.sh "'+send_string+'"'
        subprocess.call([exec_cmd],shell=True)  # executing shell script forking other scripts
        print(send_string) # jaab mond logisse
        return 0


    def tegutseme(self): # kui edutu, siis katkesta programm!
        send_ssh_string = ''
        send_http_string = ''
        nagstring_uus = '' # nagios.py jaoks
        multivalue = ['']
        tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu
        ts = int(round(tsnow,0)) #vaatame vaid vanemaid kui sekundi vanused et xxS ja xxV paarid moodustuks korralikult

        Cmd="SELECT * from nagiosele where abs(timestamp) <= "+str(ts)+" and (due_time is null or abs(due_time) =0) or (abs(due_time) > 0 and abs(due_time) <= "+str(tsnow)+") order by basen_url"
        # kui basen url mutub siis teine saatmine
        #print Cmd

        cursor = self.conn.cursor()

        try:
            cursor.execute(Cmd)
            ridu = 0 # loendame mitu rida  tuli, kui midagi ei saanud, siis ka ei kustuta midagi allpool!
            #('00204AA95C56', '212.47.221.83', 'Veetase', None, '0', 'LVV', '540', 'Veetase on:', '1318942493.0', '1000', 'm', 'hellamaa biopuhasti', '10', '0', None, '', '')
            for row in cursor:
               #print row # ajutine debug
                ridu += 1
                value="-" # igaks juhuks algvaartused
                desc="mis?"
                location="kus?"
                status = 0
                min_val = 0
                max_val = 0
                out_value = 0
                # (mac,nagios_ip,svc_name,sta_reg,status,val_reg, # 0..5
                # value,desc,timestamp, conv_coef, out_unit, # 6..10
                # location, step, due_time, max_val, multiperf, # 11..15
                # multivalue, basen_url, basen_uid, basen_pass, basen_path) # columns 16..20 in table nagiosele

                mac=row[0]
                nagios_ip=row[1]
                svc_name=row[2]
                sta_reg=row[3]  # see ei huvita muul juhul kui nagiosele testis
                status=int(row[4]) # vaja on numbrit nsca saatmise jaoks!
                val_reg=row[5] # see huvitab xxW avastamiseks
                value=row[6] # 6?
                desc=row[7] # kirjeldus
                #timestamp=row[8]
                timestamp=str(int(float(row[8]))) # vist ei tohi olla kymnendkohaga
                conv_coef=row[9] # jagamistegur
                out_unit=row[10] # oli 10?      # yhik peale jagamist
                location=row[11]      # asukoht et paremini aru saaks
                step=str(row[12])     # graafiku max ajaline granulaarsus s
                due_time=str(row[13]) # saata mitte enne kui sellel ajal # kas on oige?
                # 14 on grp_value, mida siin pole vaja
                multiperf=str(row[15]) # multiperf, graafikute nimed
                multidata=str(row[16]) # multidata, desc sisse kooloni taha need mis loetletud
                basentuple = (row[17], row[18], row[19], row[20]) # kui see muutub siis saada... sordi selle alusel?
                if basentuple[0] != '' and basentuple[0] != None:
                    mybasen = True # sinna ka saata paralleelselt nagiosele voi ainult?
                else:
                    mybasen = False
                #print('mac', mac, 'svc_name', svc_name, 'self.mybasen', str(self.mybasen), 'mybasen', str(mybasen), 'basentuple',str(basentuple)) ##

                # info olemas ka sendtuple jaoks, nagios.py testiks (sta_reg, status, val_reg, value) = sendtuple
                sendtuple = (sta_reg, status, val_reg, value)
                multivalue = multidata.strip(' ').split(' ') if multidata != None else []
                mperf = multiperf.strip(' ').split(' ')

                #kontrollime, kas mac asemel ei peaks olema aliasmac
                Cmd="select aliasmac,direction from alias where mac='"+mac+"'"
                aliasmac="" # tekitame local variable, muidu tekib viga
                aliasdir=0 # 1 kui sisend ringi suunatakse, 2 kui valjund ringi suunatakse, 3 kui molemad

                cursor3 = self.conna.cursor() # tabel alias/alias
                try:
                    cursor3.execute(Cmd)
                except:
                    traceback.print_exc()

                for row in cursor3: # peab tulema 1 rida
                    aliasmac=row[0]
                    aliasdir=int(float(row[1]))
                cursor3.close()

                if len(aliasmac) == 12 and aliasdir>0: # alias olemas, oletame et nagioses ei ole muid objecte kui mac 12 kohalise hex numbriga tahistatud
                    log.warning('mac '+mac+' replaced with '+aliasmac)
                    mac=aliasmac


                try:
                    nagstring_uus = self.n.convert(sendtuple, mperf, multivalue, svc_name=svc_name, out_unit=out_unit, conv_coef=conv_coef, desc=desc, host_id=mac, ts=timestamp) #########################
                except:
                    print('n.convert() PROBLEM with sendtuple '+str(sendtuple)+' for host '+mac)
                    nagstring_uus = None
                    traceback.print_exc()

                if mybasen != self.mybasen: ### change! send on stop, also on basentuple change below
                    if self.mybasen: # lubatuse lopp
                        if len(self.mybasen_rows) > 0: # enam ei ole mybasen LOPP, saada minema self.mybasen_rows kui olemas
                            #print('need to send '+str(len(self.mybasen_rows))+' mybasen_rows due to mybasen change to False, basentuple '+str(basentuple))
                            self.basentuple2mybasen_send(); self.mybasen_send() ## kogu list self.mybase_rows minema
                    self.basentuple = basentuple # et allpool saaks appendima hakata
                    self.mybasen = mybasen # muutus meelde

                if mybasen: ############# True
                    if len(sendtuple[3].split(' ')) == 1 : # single values only accepted so far
                        mybasen_row = self.n.convert2mybasen(sendtuple, mperf, multivalue, svc_name=svc_name, out_unit=out_unit, conv_coef=conv_coef, desc=desc, host_id=mac, ts=timestamp) ########
                        print('single value mybasen_row: '+str(mybasen_row)) # logging ei toimi...
                        if mybasen_row != None:
                            if self.basentuple == basentuple: # sama addr mis eelmine
                                self.mybasen_rows.append(mybasen_row)
                                print('new mybasen_rows length: '+str(len(self.mybasen_rows)))
                            else: # uus koht kuhu saata
                                #print('basentuple change from '+str(self.basentuple)+' to '+str(basentuple))
                                if len(self.mybasen_rows) > 0:
                                    print('sending '+str(len(self.mybasen_rows))+' mybasen_rows due to basentuple change')
                                    self.basentuple2mybasen_send(); self.mybasen_send() ## eelmine list minema ja tyhjaks
                                self.mybasen_rows.append(mybasen_row) # uut koguma
                                print('new mybasen_rows length: '+str(len(self.mybasen_rows)))
                                self.basentuple = basentuple # uus meelde

                ##self.basentuple = basentuple # eelmine igal juhul meelde

                if nagstring_uus == None: ##
                    log.error('nagstring_uus None based on sendtuple '+str(sendtuple)+', mperf '+str(nagstring_uus)+', multivalue '+str(multivalue)+', mac '+mac)
                else:
                    send_ssh_string = send_ssh_string + nagstring_uus ### teeme yhe suure stringi mille ssh ara saadab yhe korraga

        except:
            traceback.print_exc()  # valitud teenustega tegutsemise lopp

        cursor.close()

        #kustutame need saadetud read
        if ridu > 0:
            Cmd="delete from nagiosele where abs(timestamp) <= "+str(ts)+" and (due_time is null or abs(due_time) =0) \
            or abs(due_time) > 0 and abs(due_time) <= "+str(tsnow)
            #print Cmd
            try:
                self.conn.execute(Cmd) # ajutiselt ei kustuta
                self.conn.commit()

                self.send_ssh2(send_ssh_string) # nagiosele saatmine vaid siis kui kustutamine onnnestus. subprocess call kaudu, lihtsam oli kaima saada...

                if len(send_http_string) > 10:
                    print('send_http_string: ', send_http_string)  # to mybasen
                    self.send_http(send_http_string)  # to mybasen

                send_ssh_string = '' # tyhjaks
                send_http_string = '' #tyhjaks

            except:
                log.error('FAILURE')
                traceback.print_exc()
                sys.exit() # restart


    def mybasen_send(self): # async using tornado
        ''' sends self.mybasen_rows and clears it / does not buffer! there should be good tcp connection between servers... '''
        print('sending to mybasen: '+str(self.mybasen_rows))
        #self.basentuple2mybasen_send() # set server params BEFORE sendtuple changesm in tegutseme()
        self.m.mybasen_send(self.m.domessage(self.mybasen_rows)) # compile the full message and send in async mode using tornado ioloop
        self.mybasen_rows = [] # tyhjaks


    def basentuple2mybasen_send(self):
        ''' Set parameters to send '''
        self.m.url = basentuple[0]
        self.m.uid = bytes(basentuple[1], 'utf-8') # binary!
        self.m.passwd = bytes(basentuple[2], 'utf-8') # binary!
        self.m.path = basentuple[3]


# #############################################################
# #################### MAIN ###################################
# #############################################################

app = Buffer2Platforms()
log.info('use app.method() to test methods in this main script')

if __name__ == "__main__":
    tornado.ioloop.IOLoop.instance().start() # start your loop, event-based from now on
