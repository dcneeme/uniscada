# linkida nimele nagiosele32_1.py, sys.argv[0] jagab edasi. viimane muudatus 15.04.2015 neeme

# saadame tabelist nagiosele1 SOOME SERVERIS sonumid nagiosse, vajadusel ka mitu vaartust yhe teenuse kohta 
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
# 15.10.2012 koopia uue termnet serveri peale, nyyd siis yudp korti 50000 korraga saattmine 212.47.221.86 ja 46.183.73.35 
# 17.10.2012 uues serveris infokadu 10% zone omaga vorreldes! proovime ka tcp kasutada saatmmisel uude, port 500001

# 06.01.2013 nsca protokoll kasutusele udp asemel nagiosele saatmiseks. port 50001
#07.01.2013 nsca saatmine ridahaaval on surmavalt aeglane, prooviks ssh kaudu mitu rida korraga - send_ssh
#08.01.2012 ssh kasutusele udp asemel! subprocess kaudu, hulk ridu korraga reavahetusega eraldatult nagiose nagios.cmd torusse
#22.03.2013 TS= saatmine maha, CF ka!




import time
import datetime
from pytz import timezone
import pytz
utc = pytz.utc
import decimal

#from pysqlite2 import dbapi2 as sqlite3
#import sqlite3
from sqlite3 import dbapi2 as sqlite3 # basen serveris nii vaja
import sys
import traceback
import subprocess

from socket import *
import string

#import libssh2 # ssh yhenduse jaoks
#ssh=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#nagiosip="91.236.222.106" # port siin igal juhul 22

nagiossocket = socket(AF_INET,SOCK_DGRAM)
port=50000 # sama koikidel nagiostel

#import pynsca # ehk on see parem kui lihtne udp... millega on mingi arusaamatu infokadu termnet serveris
#from pynsca import NSCANotifier
#notif=NSCANotifier("91.236.222.106", 50001, 1, None) # hostname, port, encryption, password


location="" # globaalne muutuja vajalik
step="" # CF jaoks, tuleb service tabeli kaudu 
perftype="" # multi voi puudub

#create sqlite connections
try:
    conna = sqlite3.connect('/srv/scada/sqlite/alias',2) # siit ainult alias kasutusel!
    conna.text_factory = str # tapitahtede karjumise vastu, baasis iso8850-1
except:
    traceback.print_exc()

    
try:
    #conn = sqlite3.connect('/srv/scada/sqlite/nagiosele1',2) # monitor1 on main db. timeout 2 s (default on 5)
    if '_0' in sys.argv[0]:
        conn = sqlite3.connect('/srv/scada/sqlite/nagiosele0',2) # timeout 2 s (default on 5)
    else:
        conn = sqlite3.connect('/srv/scada/sqlite/nagiosele1',2) # timeout 2 s (default on 5)
    conn.text_factory = str # tapitahtede karjumise vastu, baasis iso8850-1
except:
    traceback.print_exc()

conn.execute("PRAGMA synchronous=0")  # et kiirem oleks ja kogu aeg ei kirjutaks kettale
#conn.execute("PRAGMA read_uncommitted=1")  # et kiirem oleks ja kogu aeg ei kirjutaks kettale

send_ssh_string="" # globaalne muutuja nagiosele saatmiseks
send_http_string = '' # to codeborne karla 


# ### protseduuuride defineerimine ######################

def send2nagios(saddr,sdata):
    #kui selle aadressiga handle on veel avamata, avame
    addr_port=(saddr,port)  
    nagiossocket.sendto(sdata,addr_port)
    print "udp-->",saddr,sdata
    time.sleep(0.01) # ilma selleta votab nagios vaid esimese kirje vastu!

    

def send_nsca(mac,svc_name,status,desc_perf):
    #parameetrid peaks jaama lokaalseks siin
    #nsca_string='"'+mac+'",'+svc_name+','+str(status)+',"'+desc_perf+'"'  # paneme enne kokku, muidu tekib jama pynsca.py sees...
    #print "nsca_string-->",nsca_string
    #notif.svc_result(nsca_string)  # ei toimi nii ka... 
    
    print "nsca-->",
    print(mac,svc_name,status,desc_perf)
    #notif.svc_result(mac,svc_name,status,desc_perf) # ebaonnestub!

    
#def send_ssh():
    ##ssh.connect((nagiosip, 22))
    ##session = libssh2.Session()
    ##session.startup(ssh)
    #session.userauth_password('john', '******')  # seda pole mul vaja, public key kasutusel
    ##channel = session.channel()
    ##channel.execute('ls -l')
    #print channel.read(1024) # tagasi ei saada midagi, ei huvita. aga kui miskit tuleb, voib viga olla!

    
def send_ssh2(send_string):
    exec_cmd='/srv/scada/bin/send_ssh.sh "'+send_string+'"'
    subprocess.call([exec_cmd],shell=True)  # executing shell script forking other scripts
    print 'ssh', send_ssh_string
    return 0
    
    
def send_http(send_string):
    exec_cmd='/srv/scada/bin/send_http.sh "'+send_string+'"'
    subprocess.call([exec_cmd],shell=True) # executing shell script forking other scripts
    print 'http', send_ssh_string
    return 0
 
 
    
def floatfromhex(hex):

    process = subprocess.Popen("/srv/scada/float/fltest.py "+hex, shell=True, stdout=subprocess.PIPE)
    print "fltest call","/srv/scada/float/fltest.py "+hex 
    process.wait()
    ascfloat = process.stdout.read()
    print "fltest call","/srv/scada/float/fltest.py "+hex,ascfloat 
    return ascfloat 





def tegutseme():
    global send_ssh_string, send_http_string # ports teateid reavahetustega eraldatud
    
    send_list=[] # passive chk udp, kahtlus et osa infot laheb kaduma... ip: , text:
    send_nsca_list=[] # tcp nsca protokoll passive chk jaoks, peaks parem olema. mac: , svc_name: , status: , desc_perf:

    exit_status=0


    # t = datetime.datetime.now()  #  praegune aeg - allpool teeme kohe sekunditeks
    tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu

    #korjame kokku vajaliku info vordse ja varasema timestambiga - tegelikult vaatame vaid vanemaid kui sekundi vanused et xxS ja xxV paarid moodustuks korralikult 
    Cmd="SELECT * from nagiosele where abs(timestamp) <= "+str(ts)+" and (due_time is null or abs(due_time) =0) or abs(due_time) > 0 and abs(due_time) <= "+str(tsnow)
    #print Cmd

    cursor = conn.cursor()

    try:
        cursor.execute(Cmd)
        #conn.commit()
        #annab aja alusel, sest nii kirjutati ka sisse... st sortima ei pea.
        ridu=0 # loendame mitu rida  tuli, kui midagi ei saanud, siis ka ei kustuta midagi allpool!
        #('00204AA95C56', '212.47.221.83', 'Veetase', None, '0', 'LVV', '540', 'Veetase on:', '1318942493.0', '1000', 'm', 'hellamaa biopuhasti', '10', '0', None, '', '')
        for row in cursor:
            #print row # ajutine debug
            value="-" # igaks juhuks algvaartused
            desc="mis?"
            location="kus?"
            status=0
            min_val=0
            max_val=0
            out_value=0
            nagios=0 # vana server 0, zone 1, nagios_ip alusel
            
            mac=row[0] 
            nagios_ip=row[1]
            svc_name=row[2]
            #sta_reg=row[3]  # see ei huvita, tegeleme teenusenimedega
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
            
            if "91.236.222.106" in nagios_ip:
                nagios=1 # zone server, siis CF ja TS ei saada, kuid voib saata multiperf kui teenus xxW         
                #print mac,"svc",svc_name,"status",status,"val_reg",val_reg,"value",value,"desc",desc,"nagios",nagios  # et paremin aru saaks, mis toimub
            
            perfdata="" # esialgu tyhi
            
            #kui aga out_unit == \%, siis toru taha ilma \
            if out_unit == "\%":
                out_unit2="%"  # toru taha
                print "out_unit asendus", out_unit2
            
            elif out_unit == '':
                out_unit2 = '_' # et yhikuta graafikud kohakuti ajada teistega
                
            else:
                out_unit2=out_unit # seda kasutame perf datas mitte desc sees
            
            
            #tekitame perfdata vastavalt sellele, millega tegu
            
            if float(due_time)>0:
                print "due_time>0:",due_time,"tsnow:",tsnow
                print "\n",location,mac,"DELAYED",svc_name,str(status),value+"  "+str(datetime.datetime.now())  # alustame uue teenusega selles portsus
            else:
                print "\n***",location,mac,svc_name,str(status),value+"  "+str(datetime.datetime.now())  # alustame uue teenusega selles portsus
                
            ridu=ridu + 1
            
            # tootleme erandeid - mis tuleks aga teha klassi kaudu kuidagi
            # neid harvaesinevaid asju ei tasu ka kontrollerisofti lisada (jalle yks taiendav seadistusmuutuja)
            
            if (svc_name=="FlowTotal" or svc_name=="PumbatudKogus"): # kas seda automaatselt avastada ei saa, et value on hex?
                value=floatfromhex(value)
                print "tehtud value korrigeerimine, uus value=",value
            

           
            # num value voi status? teeme perfdata, soltub teenusest, W lopuga asi teine!        
            
            try: # kas val reg on olemas
                dummy=val_reg[-1] # kas on yldse olemas value reg, pyyame viimast char
                #print 'val reg on olemas', val_reg,'lopeb:',dummy # ajutine
                
            except:
                dummy=""
                #print 'ei ole val reg'# ajutine
                
            if dummy == 'W': # multiperf 10s! mitu vaartust ja neist valitavad perfdatas naitamiseks. komaga eraldus! muidu votab num seest yksikuid kohti
                perftype="multi" # peab olema rohkem kui 1 vaartus value sees 
                #print 'multiperf!',val_reg # ajutine
                if multiperf==None:
                    multiperf='' # None ei tohi olla, seda ei saa splittida
                # koigepealt PERFDATA osa ###############  MULTI PERFDATA  ####################
                perfdata=""
                lenperf=len(multiperf.split(' '))  # allpool tahame teada mitu liiget on value sees, siin nimed
                lenvalue=len(value.split(' '))  # liikmed value sees tyhikuga eraldatud, see voib olla yhe (voi tyhikute kasutuse koral enam) vorra pikem
                # lenvalue ei tohi olla vaiksem kui lenperf!
                
                for ser in range(len(multiperf.split(' '))):  # tyhikuga seerianimesid - MIS SIIN VIGA OLI?
                    servalueS=''  #algselt tyhi
                    sername='' #seeria nimi
                    if ser<lenvalue: # siin on ser integer 0...lenperf-1
                        servalue=value.split(' ')[ser] # value on tyhikuga eraldatud vaartuste joru yhe value asemel xxW puihul
                        sername=multiperf.split(' ')[ser] # tyhikuga eraldatud nimede jorust eraldame viidatud seerianime
                        #print 'sername',sername,'servalue',servalue # ajutine
                        
                        try: # multi value
                            pummy=float(conv_coef) # komaga number
                            if pummy>0: # nulliga jagada ei yrita
                                c=decimal.getcontext().copy()
                                if servalue == 'NaN': # tahame seda vaartust vahele jatta
                                    servalueS=servalueS+sername+"="
                                else: # normaalne number
                                    servalue=c.create_decimal(str(float(servalue)/float(conv_coef)))
                                    #servalueS=servalueS+sername+"="+ "%.2F" % servalue+out_unit # +" "  # jarjekordne vorduse a la 'Seeria=0.50m'
                                    servalueS=servalueS+sername+"="+ "%.2F" % servalue+out_unit2 # alakriips yhiku puudumisel
                                #print 'servalueS tulemus praegu',servalueS # ajutine

                        except: # tundub et multi olek, sest conv_coef PUUDUB
                            #servalueS=servalueS+sername+"="+str(servalue)  # liidame jargmise seeria, kusjuures olekule yhikut pole vaja 
                            servalueS=servalueS+sername+"="+str(servalue)+out_unit2  # liidame jargmise seeria, kusjuures olekule yhikut pole vaja 
                            #print 'KONVERTEERIDA POLE VAJA' # ajutine

                        perfdata=perfdata+servalueS+" "  # MULTI PERF LOPP # lisame servalueS perfdata loppu, servalueS muutujat voib uuesti kasutada        
            
                    else:
                        print 'error in received data, lenperf must be equal or smaller than lenvalue! svc-name',svc_name,'mac',mac  
                
                
                
                    
                #nyyd DESC taiendamine        ##################### MULTI DESC ###############################
                lendata=len(multidata.split(' '))  # mitu liiget on mida desc loppu naidata vaja
                for ser in multidata.split(' '): #  desc lopus naidatavad numbrid siin viidatu alusel leiame multiperf seest
                    servalueS=''  #algselt tyhi
                    #print 'multidesc! ser',val_reg,ser,'lenperf',lenperf,'desc',desc # ajutine abi
                    
                    if  (":" in desc and ser<>''): # koolon desc lopus ja ser on olemas
                        if int(ser)-1<lenvalue: # viidatud val liige on olemas
                            servalue=value.split(' ')[int(ser)-1] # see viide on txt kujul!
                            print 'servalue',servalue,'mac',mac # ajutine abi
                            
                            try:
                                pummy=float(conv_coef) # kui see onnestub siis on value, mitte olek
                                #print 'conv_coef olemas',conv_coef,'pummy',pummy,'mac',mac # ajutine abi
        
                            except: # siis on olekute joruga tegu
                                servalueS= str(servalue) # yhikut pole vaja
                                pummy=0
                                #print 'viidatud value desc taha konverteerida ei saanud, servalueS','mac',mac # ajutine abi

                            if pummy>0: #desc taha jagatav value - aga kui ei taha alati komaga numbrit? siis on pummy 0...
                                c=decimal.getcontext().copy()
                                servalue=c.create_decimal(str(float(servalue)/float(conv_coef)))
                                #servalueS= "%.2F" % int(servalue)+out_unit # sama muutuja korduvkasutus, seekord desc sisse
                                servalueS=str(round(servalue,2))+out_unit # sama muutuja korduvkasutus, seekord desc sisse
                            
                            else: # txt kooloni taha, ehk laheb vaja
                                servalueS=str(servalue) # sama muutuja korduvkasutus, seekord desc sisse, igaksk juhuks str, voib nii olek kui txt olla...
                            
                            print 'multidata',multidata,'value',value,'ser',ser,'servalue',servalue,'mac',mac # ajutine abi

                            desc=desc+" "+servalueS # jarjekordne vaartus desc otsa koolonin taha    #  DESC VALMIS ##### multi ####
                        
                        #else: # ajutine
                            #print 'ei saanud viidata, lenperf',lenperf,'int(ser)',int(ser),'lenvalue',lenvalue # ajutine abi
                    
                print 'desc tuli selline:',desc,'mac',mac
            

            else: # tavaline teenus, value xxV voib aga ei pruugi olemas olla. lisaks allpool uurime kas uus voi vana server, CF ja TS
                
                #print 'tavaline teenus, value olemas, conv_coef',conv_coef # ajutione
                if dummy<>"": #value reg siiski olemas
                    try:
                        pummy=float(conv_coef)
                        #print 'pummy',pummy # ajutine
                    
                    except:                    
                        perfdata=svc_name+"="+str(status)
                        pummy=0
                        #print 'conv_coef ei olnud number, seega perfdatasse status:',perfdata # ajutine


                    if pummy >0 and value<>'':   # kui conv_coef on olemas ja nullist suurem, siis leiame tulemuse kui komaga numbri
                        c=decimal.getcontext().copy()
                        out_value=c.create_decimal(str(float(value)/float(conv_coef)))
                        #descvalueS=str(out_value)+out_unit  #kas siia tuleks printf panna, et fixed point decimal saada??
                        descvalueS="%.2F" % out_value+out_unit # nii on parem kui eelmine mis annab jubeda komakohtade koguse float sisendi jaoks
                        descvalueS=str(round(out_value,2))+out_unit # nii ehk veel parem?
                        
                        #print "TAVALISE TEENUSE VALUE desc taha:",descvalueS
                        

                        # perfdata num value erandid  ##############################################
                        
                        if (svc_name=="VeenivooKaevus"): # hellamaa vesi
                            min_val=-10 # anduri sygavus selle mac jaoks, alla selle ta nagunii ei naita
                            out_value=out_value+min_val # maapinna suhtes negatiivne tulemus sellel objektil vaja, anduri paigaldussygavus 10m
                            # enne oli 9m, aga siis kippus 1 m yle aare andma tulemust 14.01.2010...
                            print "tehtud VeenivooKaevus out_value korrigeerimine, uus out_value ja min, max",out_value,min_val,max_val
                    
                        if (svc_name=="KilbiTemperatuur"): # 256 tahendab info puudumist
                            if out_value>130: # katkestame, vordub info puudumisega
                                print "vigane temperatuur, katkestame. vaartus oli",out_value
                                #return # ei tohi sest jaab kustumata nagioselel tabelis!

                            if out_value == 0: # kahtlane
                                print "kahtlane temperatuur, vaartus oli",out_value
                                #return # ei tohi sest jaab kustumata naghiosele tabelis

                                
                         
                        #lopuks  perfdata ja desc stringid koos yhikuga
                        perfdata=svc_name+'='+ "%.2F" % out_value+out_unit # 10.12.2010
                        if ":" in desc:
                            desc=desc+" "+descvalueS # kooloni taha jagatud vaartus koos yhikuga
                        
                    else: # conv_coef pole voi 0, aga kui mingi value olemas, anname kooloniga loppeva desc taha
                        if ":" in desc: # desc lopus koolon, siis yks ja ainus value sinna taha koos yhikuga
                            desc=desc+" "+value  # kooloni taha value mis iganes ta on, txt voi num

                    
                        
                else: # conv_coef puudub voi on 0, tavaline teenus, perfdatasse status, yhikut ei ole
                    perfdata=svc_name+"="+str(status)+str(out_unit2) # alakriips yhikuks, et kohakuti graafikud saada
                    #print 'value oli tyhi, seega perfdatasse status'

            
                    



            #print "kokkuvotlik desc:",desc,"perfdata:",perfdata  # ajutine
            
            #miks jargmise asjana ei panda alat kokku oiget nagiose sonumit?

            #formeerime teated ja saadame ara, yksteisest soltumatult
            #kontrollime, kas mac asemel ei peaks olema aliasmac
            Cmd="select aliasmac,direction from alias where mac='"+mac+"'"
            aliasmac="" # tekitame local variable, muidu tekib viga
            aliasdir=0 # 1 kui sisend ringi suunatakse, 2 kui valjund ringi suunatakse, 3 kui molemad
            
            cursor3 = conna.cursor() # tabel alias/alias 
            try:
                cursor3.execute(Cmd)
            except:
                traceback.print_exc()

            for row in cursor3: # peab tulema 1 rida
                aliasmac=row[0]
                aliasdir=int(float(row[1]))
            cursor3.close()

            if len(aliasmac) == 12 and aliasdir>0: # alias olemas, oletame et nagioses ei ole muid objecte kui mac 12 kohalise hex numbriga tahistatud
                print "mac asendus",mac,aliasmac
                mac=aliasmac

            
            nagstring="["+str(timestamp)+"] PROCESS_SERVICE_CHECK_RESULT;"+mac+";"+svc_name+";"+str(status)+";"+desc+"|" # seda vahel ei teki??
            # siia otsa perfdata, mida voib olla mitu seeriat 
            
            if (nagios==0): # vana server
                #nagstring=nagstring+svc_name+"="
                nagstring=nagstring+perfdata # perfdata sisaldab ka teenuse nimeja vordusmarki
                nagstring_koopia=nagstring+"\n" # siia ei pane lisajura! uue serveri jaoks, ajutine abi yleviimise ajaks!
                 
                ##if step=="1": # lisame vana serveri jaoks CF siia, et tapsemat graafikut saada, naiteks LVV ja IxS
                    ##nagstring=nagstring+",CF=step1" # sin oli 18.10 2011 viga, jattis varasema nagstring arvestamata
                    #kuid miks avaldus ka AegStardist jaoks, kas sellel on siis step 1? voi jaab step eelmisest meelde? 
                    #sadamas oli AegStardist step1!

                ##nagstring=nagstring+",TS="+str(timestamp)+"\n"  # see lopetab vana serveri sonumi moodustamise
                nagstring=nagstring+"\n"  # see lopetab vana serveri sonumi moodustamise

            else: # uus server 
                nagstring=nagstring+perfdata+"\n" # siia lisajura!
                #desc_perf=desc+"|"+perfdata # send_nsca jaoks
                
            #print nagstring # nagsend logib nagunii
            
            # saatmiseks nagiosele #########################
            #send_list.append({"ip":nagios_ip,"text":nagstring}) # konfitud serverisse voimasliku TS infoga perfdatas
            #send_nsca_list.append({"mac":mac,"svc_name":svc_name,"status":status,"desc_perf":desc_perf}) # mac: , svc_name: , status: , desc_perf:
            send_ssh_string=send_ssh_string+nagstring # teeme yhe suure stringi mille ssh ara saadan yhe korraga
            if '000101300' in mac: # codeborne karla info
                send_http_string += nagstring # http kaudu saatmiseks
            
    except:
        traceback.print_exc()  # valitud teenustega tegutsemise lopp 

    # saadame dictionaryst ara

    cursor.close()

    

    #kustutame need saadetud read    
    if ridu > 0:
        Cmd="delete from nagiosele where abs(timestamp) <= "+str(ts)+" and (due_time is null or abs(due_time) =0) \
        or abs(due_time) > 0 and abs(due_time) <= "+str(tsnow)
        #Cmd="delete from nagiosele where abs(timestamp) <= "+str(ts) # sellega kustutas ootele pandud ka ara enne viite labisaamist
        #print Cmd
        try:
            conn.execute(Cmd)
            conn.commit()
              
	    # saadame ainult siis kui kustutamine onnestus. Kui kirjutuslukku ei saa, siis voib asi ebaonnestuda. 
            # monitor 
    	    ##for item in send_list: # nagu vaike andmebaas on see list
                #print "udp_send",item["ip"],item["text"]  # saab vaadata mida saadetakse
                ##send2nagios(item["ip"],item["text"])  # siin saadame kogutud listi minema #### kommenteeri debugimise ajaks!
                ##time.sleep(0.01) # time.sleep(0.1)  # igaks juhuks vaike viide vahele - 0.1 oli kyll liiga suur!!! vaid 10 teadet sekundis!!!! nyyd 50
                
            send_list=[] # tyhjaks
                
            #for item in send_nsca_list: # uutmoodi, 6.1.2013 
                #print "nsca_send",item["mac"],item["svc_name"],item["status"],item["desc_perf"]   # saab vaadata mida saadetakse
                #send_nsca(item["mac"],item["svc_name"],item["status"],item["desc_perf"])  # siin saadame kogutud listi minema #### kommenteeri debugimise ajaks!
                
            #send_nsca_list=[]

            #send_ssh(send_ssh_string) # yhe stringina teele yle libssh2
            send_ssh2(send_ssh_string) # nagiosele saatmine subprocess call kaudu, lihtsam oli kaima saada...
            
            if len(send_http_string) > 10:
                send_http(send_http_string)  # to codeborne
                
            send_ssh_string = "" # tyhjaks. peaks ehk proovima exit statuse alusel kas onnestus saatmine?
            send_http_string = '' #tyhjaks
            
        except:
            exit_status=-1
            traceback.print_exc()
	    # kui ei onnestu teeme restardi.
            #kui ei onnestu, siis jargmine kord proovib uuesti... saadab nagiosele ka uuesti muidugi.


    return exit_status
 
 
 
 
# #############################################################
# #################### MAIN ###################################
# #############################################################

#tsykliliselt umbes kord sekundis lugeda info puhvertabelist 'nagiosele' ja saata nagiosele
# 8.22.1011 neeme lisas 0,1 s viidet max timestamp leidmisele, et xxS xxV paarid kokku saada ja mitte osalise infoga topeltteateid nagiosele saata

while 1:

    #teeme kindlaks hiliseima timestambi        
    cursor2 = conn.cursor()
    Cmd="SELECT max(timestamp),count(timestamp) from nagiosele"
    
    try:
        res = cursor2.execute(Cmd) #  seda vist pole vaja?
        
        for row in cursor2: # peab tulema 1 rida
            ts=row[0]  # otsime koige vanemat kirje ajamarki 
            ridu=row[1] # mitu kirjet baasis?
            
        if ts != None:
            #print "baasis nagiosele1 max timestamp ",ts, "ridu",ridu
            #print "baasis nagiosele0 max timestamp ",ts, "ridu",ridu
            try:
                time.sleep(0.2) # anname aega xxV / xxS paaride moodustumiseks
                if tegutseme() < 0:
                    break
                    sys.stdout.flush()

            except:
                traceback.print_exc()
                print "tegutseme main exception",ts
        
        else:
            #print "baas nagiosele1 tyhi"
            print sys.argv[0],"baas nagioseleX tyhi"
            #traceback.print_exc()  # ajutine abi
            
    except:
        dummy="miks siia sattus? uuri asja"
        #print dummy
        #traceback.print_exc()  # ajutine abi
    
    #viide 
    cursor2.close()
    time.sleep(0.5)
    
