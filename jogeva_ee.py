#!/usr/bin/python
#neeme 09.02.2013, jogevale kaugjuhtimispaneel

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

#cmd = [ 'sss', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '' , '', '', '', '', '', '' , '', '', '', '', '', '' ] # cmdX array
#desc = [ '', '', '', '' , '' , '', '', '', '', '', '', '', '', '', '', '', '', '', '' , '', '', '', '', '', '' , '', '', '', '', '', '' ]  #selgitused cmd juurde
L1W=['','',''] # needsamad muutujanimed ja multivalue liikmed, millega olekuid raporteeritakse
L2W=['','',''] # valgustus ruum 35
L3W=['','',''] # ruum 56
L4W=['','',''] # valgustus 3 gruppi ruumis 57
L1S=[0,0,0,0] # abimuutujad
L2S=[0,0,0,0] # valgustus ruum 35
L3S=[0,0,0,0] # ruum 56
L4S=[0,0,0,0] # valgustus 3 gruppi ruumis 57

HEW=['','','',''] # kyte 4 ruumi
COW=['','','',''] # jahutus
HUW=['','','',''] # niisutus
D1V=''  # string tabloo txt
D2V=''  # string tabloo txt
D3V=''  # string tabloo txt
D4V=''  # string tabloo txt

# index range peab arrayl aga suurem olema, rown ja coln voivad ylel minna!?

asuk='asuk_puudub'
location='loc_puudub'
host='host_puudub'
mac='mac_puudub'
filename='filename'
mon='type_puudub'
dis='' # dis="disabled='true'" selleks et nupud ei toimiks, keelamine allpool 
diss='' # ootel korralduste olemasolul ei ole disabled kustutamise nupp
last=0 # viimase saatmise ts

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
filename1 = form.getvalue('file1')
#filename2 = form.getvalue('file2')
mac =  form.getvalue('mac')
host = form.getvalue('host') # displayname
rows =  form.getvalue('rows') # vajaliku tabeli read
columns =  form.getvalue('columns') # vajaliku nuputabeli tulbad

command=''
color="red"  # ootel korralduste kustutamise nupule
reg='' # juhtimise register, kasutame L1W..L4W, HEW, HUW, COW
val='' # multivalue 
chg=0

#lisa kui vaheks jaab, ka eespool cmd ja desc masiividele liikmeid!



# protseduurid
def printbutton(what,mode): # trykkigu status ja nupp tabeli cellis nii et nupul kindel koht
# kui mode on 1, siis on muutumas. kui aga bitikaal 2 on ,mangus, siis on button vajalik. nii et enamsati mode 0 voi 2 voi 3. 
    global dis,mac,reg,val
    #print "<td><table border='0' BORDERCOLOR='#999999' width='100%'><tr bgcolor='#999999'>"  # kuidas muuta border nahtamatuks?
    print "<td><table width='100%' style='border:0px solid transparent;'>"  # siseminse tabeli borderid nahtamatuks!
    if what == "ON" or what == '1': # olek aktiivne
        print "<td style='font-family:sans-serif; height:25px; background-color:limegreen; color:yellow;'>&nbsp;&nbsp;Kehtiv olek: "+what+"</td>\n<td bgcolor='#999999' width='40px' align='center'>" # ON statuse naitamine #  width='50px'
    else: # muud inaktiivsed variandid
        print "<td style='font-family:sans-serif; height:25px; background-color:grey; color:yellow;'>&nbsp;&nbsp;Kehtiv olek: "+what+"</td>\n<td bgcolor='#999999' width='40px' align='center'>" # OFF statuse naitamine
        
    
    if (mode&1) == 0: # ei ole muutumas.  
        if (mode&2) == 2: # button vajalik
            if what == "ON": # lisame nupu ja lopetame pooliku celli
                print "<input "+dis+" type='button' style='float:center; position:relative; height:20px; width:35px; background-color:red; color:yellow;' value='OFF' onclick=location.href='http://46.183.73.35/conf/cmd2controller.py?mac="+mac+"&reg="+reg+"&val="+val+"'  title='V&auml;ljal&uuml;litamine' /></td>" 
                # selle nupu vajutus lylitagu valja
            if what == "OFF":  # lisame nupu ja lopetame pooliku celli
                print "<input "+dis+" type='button' style='float:center; position:relative; height:20px; width:35px; background-color:limegreen;color:yellow;' value='ON' onclick=location.href='http://46.183.73.35/conf/cmd2controller.py?mac="+mac+"&reg="+reg+"&val="+val+"' title='Sissel&uuml;litamine' /></td>" 
                # selle nupu vajutus lylitagu sisse, hetkel on valjas
                
    else: # on muutumas
        if (mode&2) == 2: # button vajalik aga mitteakstiivne,  # lisame nupu ja lopetame pooliku celli
            print "<input "+diss+" type='button' style='float:center; position:relative; height:25px; width:35px; background-color:khaki;color:yellow;' value='changing' /></td>" 
        else: # buttoni koht vaja jatta nahtamatuna, lisame nahtamatu nupu ja lopetame pooliku celli
            #print "<td align='center' bgcolor='#999999'>&nbsp;</td>"
            print "<input "+dis+" type='button' style='float:center; position:relative; height:25px; width:35px; background-color:transparent;color:transparent;' value='' /></td>" 
            
    print "</tr></table></td>" # lopetab celli sisese tabeli ja ka juhitava maatriksi celli enda





# ###########  MAIN  ##################

# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print 

#print cmd, mon # ajutine proov
#print cmd

conn = sqlite3.connect('/srv/scada/sqlite/monitor')
cursor=conn.cursor()

print "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd'>\n"
print "<html><head>\n	<script type='text/javascript' src='/calendar/scripts/jquery_v2.js'></script>\n"
print "<style media='screen' type='text/css'> body {background-color:#ffffff; font-family: arial; font-size: 75%; } table { font-family: arial;} </style>" 
# kui fffff nagu nagiosel siis firefox ei vilgu. chrome ja ie vilguvad ikka, ajax vaja vist...
print "<title>KaugJuhtimisPaneel</title>\n"
print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'/>\n" # <meta http-equiv="refresh" content="1" />
print "<meta http-equiv='refresh' content='3'/>\n"  # 3s tagant automaatne reload #####
	
print "</script></head><body>"

print "<h2> Kaugjuhtimispaneel objektile " +str(mac)+ " (" +str(host)+ ")</h2>" 
print "<h4> Vilkumisest vabastab selle lehe Firefoxi kasutamine!</h4>" 
print "<br><br>\n"


#kontrollime kas side on olemas
cursor=conn.cursor()
conn.execute('BEGIN IMMEDIATE TRANSACTION') # alustame transaktsiooni, peaks parem olema...
cursor.execute('select MAX(timestamp) from state where mac = '+"'"+str(mac)+"'") # side korrasoleku kontroll
for row in cursor:
    if row[0]<>'' and row[0]<>None:
        last=int(float(row[0]))

if last < tsnow - 900:
    print "<td colspan='6'><span style='color:red'><b>Side objektiga on katkenud, hetkel juhtimine ei toimi ning paneeli info on vananenud!</b> Kontakteeru support@itvilla.ee</span></tr>\n"
    dis="disabled='true'" # side puudumise ajal argu nupud toimigu!
else:
    print "<span style='color:green'><b>Side objektiga on korras. </span> <br> Juhtimistegevused teostatakse kuni 20 sekundi jooksul vastava nupu klikkimisest.<br>\n"
    print "Kui selle ajaga ootel korraldus ei kao, kustuta see ja proovi uuesti."
print "<p>\n"



#kontrollime kas moni selle kontrolleri korraldus on juba ootel
ootel='' # lihtsalt string
cursor.execute('select register,value from newstate where mac = '+"'"+str(mac)+"'") # kas on midagi ootel newstate tabelis selle kontrolleri jaoks
for row in cursor:
    cmd=row[0]
    ootel=ootel+" "+row[0]+":"+row[1] # koik ootel cmd jarjest kokku yle tyhiku
if ootel == '':
    diss="disabled='true' title='Praegu ei ole ootel korrraldusi'" # kui korraldusi ootel pole, ei pea neid ka kustutada saama!
    color="pink" # lahjem variant, ei ole midagi kustutada
    
cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'HEW'") # kytte olek
for row in cursor:
    if row[0]<>'':
        HEW=row[0].split(' ') # taidab liikmed vaartustega
   
cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'HUW'") # niisutuse olek
for row in cursor:
    if row[0]<>'':
        HUW=row[0].split(' ')
   
cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'COW'") # jahutus
for row in cursor:
    if row[0]<>'':
        COW=row[0].split(' ')
    
cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'L1W'") # valgustus ruum 34
for row in cursor:
    if row[0]<>'':
        L1W=row[0].split(' ')

cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'L2W'") #  valg 35
for row in cursor:
    if row[0]<>'':
        L2W=row[0].split(' ')

cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'L3W'") #  valg 56
for row in cursor:
    if row[0]<>'':
        L3W=row[0].split(' ')

cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'L4W'") # valg 57
for row in cursor:
    if row[0]<>'':
        L4W=row[0].split(' ')
        
#tablootekstid ka, et ilus oleks...
cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'D1V'") # tabloo 34, siin ei spliti!
for row in cursor:
    if row[0]<>'':
        D1V=row[0] #.split(' ')

cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'D2V'") # tabloo 35
for row in cursor:
    if row[0]<>'':
        D2V=row[0] #.split(' ')

cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'D3V'") # tabloo 56
for row in cursor:
    if row[0]<>'':
        D3V=row[0] #.split(' ')

cursor.execute('select value from state where mac = '+"'"+str(mac)+"' and register = 'D4V'") # tabloo 57
for row in cursor:
    if row[0]<>'':
        D4V=row[0] #.split(' ')
        
conn.commit() # transaktsiooni lopp

# muutujad tegeliku olukorra kohta olemas, kas teha maatriksiks? parem tabelit genereerida?   
#print 'L1W',L1W,'L2W',L2W,'L3W',L3W,'L4W',L4W,'HEW',HEW,'COW',COW,'HUW',HUW # praegune seis state alusel
   

rown=0
coln=0
# kasutame tabeli celli taustavarve, see ei vilgu ega formaadi tabelit ringi erinevalt piltide reloadimisest! saab ilma ajaxita!
#ON="<td align='center' bgcolor='#33ee33'>ON</td>" # roheline cell kirjaga on
#OFF="<td align='center' bgcolor='#999999'>OFF</td>" # hall cell kirjaga off
#nyyd nupud kaiku hoopis!

# reg ja val vaartused pannakse iga tabeli nupu jaoks eraldi paika allpool
NAN="<td align='center' bgcolor='#999999'> &nbsp; </td>" # ei ole seda muutujatki state tabelis voi on see liiga vana, peaks kontrollima...
command=''

print "<table border='12'>\n"  # paneeli algus

# enne maatriksi algust naitame tablooteadete sisu
print "<tr><td bgcolor='#999999'></td>" # tyhi kast nurgas, voiks olla ka "Ruumi tabloo tekst"
print "<td nowrap style='font-family:sans-serif; font-family: monospace; font-size:125%; text-align:center; background-color:black; color:cyan;'>"+str(columns.split(',')[1])+": "+D1V+"</td>" # taastasin ka mittesaadetava ruumi nr ja kooloni koos tyhikuga
print "<td nowrap style='font-family:sans-serif; font-family: monospace; font-size:125%; text-align:center; background-color:black; color:cyan;'>"+str(columns.split(',')[2])+": "+D2V+"</td>" # nyyd on tablooteate tapne kooopia...
print "<td nowrap style='font-family:sans-serif; font-family: monospace; font-size:125%; text-align:center; background-color:black; color:cyan;'>"+str(columns.split(',')[3])+": "+D3V+"</td>" # jube uhke olen... 10.2.2013 neeme
print "<td nowrap style='font-family:sans-serif; font-family: monospace; font-size:125%; text-align:center; background-color:black; color:cyan;'>"+str(columns.split(',')[4])+": "+D4V+"</td>"
print "</tr>\n" # tablooteadete rea lopp

#nyyd automaatselt paigutatud nupud rows ja columns parameetrite alusel
for rown in range(len(rows.split(','))): # iga rea jaoks indexiga row 0...
    print "<tr>" # rea algus
    for coln in range(len(columns.split(','))): # iga tulba cell tulbaindexiga column vahemikust 0...
        #print "<td bgcolor='#eeeeee'>" 
        if rown == 0: # esimene rida, anname sisuks tulpade nimed columns seest
            print "<th align='center' bgcolor='#eeeeee'>"+str(columns.split(',')[coln])+"</th>" # tulpade nimed
        else:
            if coln == 0: # esimene veerg
                print "<th bgcolor='#eeeeee'>"+str(rows.split(',')[rown])+"</th>" # ridade nimed
            else:
                #print str(rown)+","+str(coln) # tabeli ylejaanud sisuks indeksinumbrid esialgu
                
       
                cgh=0 # printbuttoni jaoks , et muutusest marku anda
                if rown > 0 and rown < 4: # valgustigrupid 1..3 nendel ridadel
                    if coln == 1: # ruum 34 ehk sygavkylm
                        if L1W[0]<>'': # on loota vaartust 
                            reg="L1W" # registri nimi, kui peaks olema vaja  newstate kirjutada
                            if reg in ootel:
                                chg=3 # button vajalik ja ootel
                            else:
                                chg=2 # button vajalik ja ei ole ootel
                            
                            # row 1..3 =jaoks yhe liikme 1..3 inversioon tegeliku suhtes teha, teised jatta nagu on
                            for n in range(3): # 3 gruppi, n=0..2
                                L1S[n]=int(float(L1W[n])) # int abimuutujasse algseis
                                if n == rown-1: # see yks kolme hulgast inverteerida
                                    L1S[n]=1^L1S[n] # inversioon xor kaudu
                                
                            val=str(L1S[0])+"_"+str(L1S[1])+"_"+str(L1S[2])+"_"+str(L1S[0]+2*L1S[1]+4*L1S[2]) # 4 liiget
                            
                            if int(float(L1W[rown-1])) == 1: # grupp 1 aktiivne
                                printbutton("ON",chg) # enne seda peab reg ja val olemas olema!
                            else:
                                printbutton("OFF",chg)
                            
                        else: # muutuja puudub selle ruumiparameetri jaoks state tabelis
                            print NAN #"<td></td>" # tyhi cell tabelisse
                            
                    if coln == 2: # ruum 35
                        if L2W[0]<>'': # on loota vaartusi
                            reg="L2W" # registri vaartus, kui peaks olemna vaja  newstate kirjutada
                            if reg in ootel:
                                chg=3
                            else:
                                chg=2
                            
                            # row 1..3 =jaoks yhe liikme 1..3 inversioon tegeliku suhtes teha, teised jatta nagu on
                            for n in range(3): # 3 gruppi, n=0..2
                                L2S[n]=int(float(L2W[n])) # int abimuutujasse algseis
                                if n == rown-1: # see yks kolme hulgast inverteerida
                                    L2S[n]=1^L2S[n] # inversioon xor kaudu
                            
                            val=str(L2S[0])+"_"+str(L2S[1])+"_"+str(L2S[2])+"_"+str(L2S[0]+2*L2S[1]+4*L2S[2]) # 4 liiget
                            
                            if int(float(L2W[rown-1])) == 1:
                                printbutton("ON",chg)
                            else:
                                printbutton("OFF",chg)
                            
                        else: # muutuja puudub selle ruumiparameetri jaoks state tabelis
                            print NAN #"<td></td>" # tyhi cell tabelisse

                    if coln == 3: # ruum 56
                        if L3W[0]<>'': # on loota vaartust
                            reg="L3W" # registri vaartus, kui peaks olemna vaja  newstate kirjutada
                            if reg in ootel:
                                chg=3
                            else:
                                chg=2
                                
                            # row 1..3 =jaoks yhe liikme 1..3 inversioon tegeliku suhtes teha, teised jatta nagu on
                            for n in range(3): # 3 gruppi, n=0..2
                                L3S[n]=int(float(L3W[n])) # int abimuutujasse algseis
                                if n == rown-1: # see yks kolme hulgast inverteerida
                                    L3S[n]=1^L3S[n] # inversioon xor kaudu
                            
                            val=str(L3S[0])+"_"+str(L3S[1])+"_"+str(L3S[2])+"_"+str(L3S[0]+2*L3S[1]+4*L3S[2]) # 4 liiget
                                 
                            if int(float(L3W[rown-1])) == 1:
                                printbutton("ON",chg)
                            else:
                                printbutton("OFF",chg)
                            
                        else: # muutuja puudub selle ruumiparameetri jaoks state tabelis
                            print NAN #"<td></td>" # tyhi cell tabelisse

                            
                    if coln == 4: # ruum 57 
                        if L4W[0]<>'':  
                            reg="L4W" # registri vaartus, kui peaks olemna vaja  newstate kirjutada
                            if reg in ootel:
                                chg=3
                            else:
                                chg=2
                            
                            # row 1..3 =jaoks yhe liikme 1..3 inversioon tegeliku suhtes teha, teised jatta nagu on
                            for n in range(3): # 3 gruppi, n=0..2
                                L4S[n]=int(float(L4W[n])) # int abimuutujasse algseis
                                if n == rown-1: # see yks kolme hulgast inverteerida
                                    L4S[n]=1^L4S[n] # inversioon xor kaudu
                            
                            val=str(L4S[0])+"_"+str(L4S[1])+"_"+str(L4S[2])+"_"+str(L4S[0]+2*L4S[1]+4*L4S[2]) # 4 liiget
                            
                            if int(float(L4W[rown-1])) == 1:
                                printbutton("ON",chg)
                            else:
                                printbutton("OFF",chg)
                        else: # muutuja puudub selle ruumiparameetri jaoks state tabelis
                            print NAN # tyhi cell tabelisse
                            
                if rown == 4: # kyte
                    if HEW[0]<>'':
                        reg="HEW" # registri vaartus, kui peaks olemna vaja  newstate kirjutada
                        if reg in ootel:
                            chg=1
                        else:
                            chg=0
                        if coln == 1:
                            val=str(1^int(float(HEW[0])))+"_"+str(HEW[1])+"_"+str(HEW[2])+"_"+str(HEW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 2:
                            val=str(HEW[0])+"_"+str(1^int(float(HEW[1])))+"_"+str(HEW[2])+"_"+str(HEW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 3:
                            val=str(HEW[0])+"_"+str(HEW[1])+"_"+str(1^int(float(HEW[2])))+"_"+str(HEW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 4:
                            val=str(HEW[0])+"_"+str(HEW[1])+"_"+str(HEW[2])+"_"+str(1^int(float(HEW[3]))) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        
                        if int(float(HEW[coln-1])) == 1:
                            printbutton("ON",chg)
                        else:
                            printbutton("OFF",chg)
                                                
                    else:
                        print NAN
                        
                if rown == 5: # jahutus
                    if COW[0]<>'':
                        reg="COW" # registri vaartus, kui peaks olemna vaja  newstate kirjutada
                        if reg in ootel:
                            chg=1
                        else:
                            chg=0
                        if coln == 1:
                            val=str(1^int(float(COW[0])))+"_"+str(COW[1])+"_"+str(COW[2])+"_"+str(COW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 2:
                            val=str(COW[0])+"_"+str(1^int(float(COW[1])))+"_"+str(COW[2])+"_"+str(COW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 3:
                            val=str(COW[0])+"_"+str(COW[1])+"_"+str(1^int(float(COW[2])))+"_"+str(COW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 4:
                            val=str(COW[0])+"_"+str(COW[1])+"_"+str(COW[2])+"_"+str(1^int(float(COW[3]))) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        
                        if int(float(COW[coln-1])) == 1: # nyyd voib printbuttonisse minna sest val on olemas
                            printbutton("ON",chg)
                        else:
                            printbutton("OFF",chg)
                        
                    else:
                        print NAN
                        
                if rown == 6: # niisutus
                    if HUW[0]<>'':
                        reg="HUW" # registri vaartus, kui peaks olemna vaja  newstate kirjutada
                        if reg in ootel:
                            chg=1
                        else:
                            chg=0
                        if coln == 1:
                            val=str(1^int(float(HUW[0])))+"_"+str(HUW[1])+"_"+str(HUW[2])+"_"+str(HUW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 2:
                            val=str(HUW[0])+"_"+str(1^int(float(HUW[1])))+"_"+str(HUW[2])+"_"+str(HUW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 3:
                            val=str(HUW[0])+"_"+str(HUW[1])+"_"+str(1^int(float(HUW[2])))+"_"+str(HUW[3]) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        if coln == 4:
                            val=str(HUW[0])+"_"+str(HUW[1])+"_"+str(HUW[2])+"_"+str(1^int(float(HUW[3]))) # inversioon (1 xor value) liikmele 1 (juhuks, kui nuppu vajutatakse)
                        
                        if int(float(HUW[coln-1])) == 1:
                            printbutton("ON",chg)
                        else:
                            printbutton("OFF",chg)
                        
                    else:
                        print NAN
                
                
    
        #print "</td>"
        
    print "</tr>\n" # rea lopp
    
    
print "</tr>\n</table>\n<br>\n"  # lopetame tabeli

    
print "<p><input "+diss+" type='button' style='height:25px; width:200px; background-color:"+color+";' value='Kustuta ootel korraldused' onclick=location.href='http://46.183.73.35/conf/cmd2controller.py?mac="+mac+"&cmd=CLEAR'>" # ootel maha
print ootel # mis ootel on newstate alusel?
# peaks aga kontrollima kas on ootel midagi yldse!

    
print "<p><A HREF=http://46.183.73.35/conf/bn3setup1.py?mac="+str(mac)+"&file="+filename1+" > <b>Seadistusparameetrid </b></A>"
print " juhtkontrolleris - vajaduseta mitte muuta! <b><br>"

print "</body></html>\n"

