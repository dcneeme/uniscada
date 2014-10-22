#!/usr/bin/python3
# -*- coding: UTF-8 -*-# testime universaalset sisendinfopaneeli, mis oleks kiirem, kui nagios
# 03.01.2014 
# 9.10.2013
# 03.01.2014 kui olek on olemas, on ta enne value vaartust. sel juhul olekut ei naita, vaid varvime vaartuse rea vastavalt olekule roh koll pun
# 15.02.2014 nahtavale uuesti xxS teenused ja kogu asi ilusamaks
#5.5.midagi muutunud cookie osas?
# 17.10.2014 filter valitavate teenuste jaoks ja vaartuste seadmine (kaugjuhtimine)
#   20.10.2014 teha telefonile sobivas formaadis, yks rida iga teenuseliikme kohta.


''' simple html UI for fast viewing and remote control '''


def output(register,filter=None,value='puudub!',age=999,status=9): 
    ''' Output html lines for one service, incl servicename, description.
        Line bgcolor depends on status. Filtered based on servicename if filter exists. 
        If conv_coef != '' then +/- buttons, else toggle button for multicfg members.
        Every member vill add one value line in embedded table of the value cell.
    '''
    global maxage, servicetable
    statusrida=None
    
    Cmd2="select svc_name, out_unit, conv_coef, multiperf, multivalue, multicfg, desc0, desc1, desc2 from "+servicetable+" where sta_reg = '"+register+"' or val_reg = '"+register+"'" 
    #print(Cmd2+'<br>') # debug
    
    #TR="<tr><table border = '1'><tr bgcolor='#cccccc'>" # html tag rea algusesse, varvi defineerimine, muudetakse statuse alusel
    cursor2.execute(Cmd2)
    servicename="<i>teenus defineerimata v&otilde;i seadistusmuutuja</i>" # juhuks, kui vastet ei leita
    desc = []
    for row in cursor2: # yks rida
        servicename=row[0]
        out_unit = row[1]
        conv_coef = row[2]
        multiperf = row[3]
        multivalue =  row[4]
        multicfg =  row[5]
        for i in range(3):
            desc.append(row[i+6])
        
        valcount = len(value.split(' ' )) # if xyW
        
        mperf=[]
        mvalue=[]
        mval=[]
        mcfg=[]
        for i in range(valcount): # liikmed
            mperf.append(multiperf.split(' ')[i]) # member name
            mvalue.append(value.split(' ')[i])    # member value
            if str(i+1) in multivalue:
                mval.append('1')
            else:
                mval.append('0')
            
            if str(i+1) in multicfg:
                mcfg.append('1')
            else:
                mcfg.append('0')
        
    if filter != None and filter not in servicename: # skip this service
        #print('exit1',register,servicename) # debug
        return ''
        
    if desc == [] or mval == []:
        #print('exit2',register,servicename) # debug
        return '' # teenus kirjeldamata
        
    if mperf == []: # kasutame teenusenime
        mperf=[servicename]
    
    
    # tulemus olemas, naidata desc ja liikmete read  ##############
    
    output = "<tr>" 
    bgcolors=['#ccffcc', '#ffffcc', '#ffcccc'] # G Y R
    if status<3: 
        TR="<tr bgcolor='#ccffcc'>" # taust roh, ok
        if len(value)>1: # perf, olgu veidi tumedam roheline
            TR="<tr bgcolor='"+bgcolors[status]+"'>" 
    
    if age>0.9*maxage: # hoiatame oranzi varviga, et selle info uuenemine on loppenud
        TR="<tr bgcolor='#F87217'>" # unkown, nagu nagioses, uuenemine lopenud. pumpkin orange
            
    buttoncode='' # printbutton('ON',0,register,'1')
    output += TR+"<td colspan='3'><b> "+desc[status]+"</b></td></tr>\n"
    
    if out_unit == 'm':
        step = 50 # mm
    else:
        step = 20
        
    for i in range(valcount):
        output += "<tr><td> "+mperf[i]+"</td><td align='right'>"
        if conv_coef != '' and float(conv_coef) > 0:
            mvalue[i] = round(1.0*int(float(mvalue[i]))/int(float(conv_coef)))
        output += str(mvalue[i])+" "+out_unit+"</td><td width='300px' align='middle' valign='middle'>"
        
        if str(i+1) in multicfg:
            if out_unit != '':
                output += printbutton(register, value, i+1, '-') #' - + ' # printbutton(out_unit,1,register,) # 'cfg'
                output += printbutton(register, value, i+1, '+')
            else:
                output += printbutton(register, value, i+1, 'OFF')
                output += printbutton(register, value, i+1, 'ON')
                
        output += "</td></tr>\n"
    
    output += "</tr>\n"    
    #print(output+'<br>') # debug
    return output


def printbutton(register,value,member,buttonvalue,step=50): # trykkigu status ja nupp tabeli cellis nii et nupul kindel koht
    ''' Print a button for config change or switching. If clicked generates new value to be forwarded to newstate '''
    # cfg samm service failis ette anda? cfgstep
    # kui mode on 1, siis on muutumas. kui aga bitikaal 2 on mangus, siis on toggle button vajalik. kui 4, siis +/- nupud. 
    global dis,mac
    bcolor = 'yellow'
    if buttonvalue == 'ON':
        bcolor = 'green'
    elif buttonvalue == 'OFF':
        bcolor = 'red'

    values = value.split(' ')
    newvalue=''
    nobutt = 0
    for i in range(len(values)):
        if newvalue != '':
            newvalue += '_' # alakriips tyhiku asemel url peal edastamiseks!
        
        if i == member - 1:
            if 'O' in buttonvalue: # ON or OFF
                if 'OFF' in buttonvalue and values[i] == '0' or 'ON' in buttonvalue and values[i] == '1':
                    newvalue += values[i]
                else:
                    newvalue += str(int(values[i])^1)
            elif '+' in buttonvalue: 
                newvalue += str(int(values[i]) + step)
            elif '-' in buttonvalue: 
                newvalue += str(int(values[i]) - step)
            else:
                newvalue += values[i] # perhaps not ever needed
        else:            
            newvalue += values[i]
           
    
    #print(register,value,' / ',newvalue,'<br>') # debug
    
    if newvalue == value.replace(' ','_'): # no change needed
        buttoncode = "<input "+dis+" type='button' style='position:relative; height:80px; width:140px; background-color:transparent; color:transparent;' value='' />" 
    else: 
        buttoncode = "<b><input "+dis+" type='button' style='font-size:36px; position:relative; height:80px; width:140px; background-color:"+bcolor+"; color:black;' value='"+buttonvalue+"' onclick=location.href='https://receiver.itvilla.com/conf/cmd2controller2.py?mac="+mac+"&reg="+register+"&val="+newvalue+"'  title='"+buttonvalue+"' /></b>" 
    # eemaldatud float:center; position:relative; 
    
    return buttoncode

    
    
# ##################### MAIN #############################


# Import modules for CGI handling 
import cgi, cgitb ,re
cgitb.enable() 

from sqlite3 import dbapi2 as sqlite3 

import time
import datetime
#from pytz import timezone
#import pytz
#utc = pytz.utc
import traceback
import os

tsnow = time.mktime(datetime.datetime.now().timetuple()) #sekundid praegu
age=0
age_meelde=0
register=''
register_meelde=''
lastperfregister=''
status=0
status_meelde=0
servicename=''
servicename_meeld=''
statusrida=''
statusrida_meelde=''
location = ''
mac=''
last=0 # viimase saatmise ts
perf=0

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac =  form.getvalue('mac')
if mac == None:
    mac='000101200006'
    #print('Error: no mac! </body></html>')
    #exit()
filter = form.getvalue('filter')
    
maxage =  form.getvalue('maxage')
if maxage == None or maxage == '':
    maxage = 500 # s
else:
    maxage=int(float(maxage)) # numbriks


COOKIEAUTH_DOMAIN = 'itvilla_com'

USER = None

URL = ''
if 'HTTPS' in os.environ and os.environ['HTTPS'] == 'on':
    URL += 'https://' + os.environ.get('HTTP_HOST', 'localhost')
    port = os.environ.get('SERVER_PORT', '443')
    if port != '443':
        URL += ':' + port
else:
    URL += 'http://' + os.environ.get('HTTP_HOST', 'localhost')
    port = os.environ.get('SERVER_PORT', '80')
    if port != '80':
        URL += ':' + port
URL += os.environ.get('REQUEST_URI', '/')

http_status = 'Status: 200 OK'
http_data = {}

try:
    # Python 2
    import Cookie
except (NameError, ImportError):
    # Python 3
    import http.cookies as Cookie

try:
    USER = Cookie.SimpleCookie(os.environ["HTTP_COOKIE"])[COOKIEAUTH_DOMAIN].value.split(':')[0]
except (Cookie.CookieError, KeyError, IndexError):
    pass # raise SessionAuthenticationError('not authenticated')
        
    
conn = sqlite3.connect('/srv/scada/sqlite/monitor')
cursor=conn.cursor()
cursor2=conn.cursor() # second connection to the same db

conn.execute('BEGIN IMMEDIATE TRANSACTION') # alustame transaktsiooni, peaks parem olema...

Cmd="select servicetable,location from controller where mac = '"+str(mac)+"'" # teenusetabel
cursor.execute(Cmd)
for row in cursor: # saame ainult yhe rea konkreetse mac kohta, tabelil unikaalne index
    servicetable=row[0]
    location=row[1]
    
cursor.execute('select MAX(timestamp) from state where mac = '+"'"+str(mac)+"'") # side korrasoleku kontroll
for row in cursor:
    if row[0] != '' and row[0] != None:
        last = int(float(row[0]))

if last < tsnow - 900:
    print("<span style='color:red'><b>Side objektiga on katkenud!</span>\n")
    dis = "disabled='true'" # side puudumise ajal argu nupud toimigu!
else:
    dis = '' # side ok

# starting with html output
print("Content-type: text/html")
print()
print("<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd'>\n")
print("<html><head>\n")
print("<style media='screen' type='text/css'> body {background-color:#ffffff; font-family: arial; font-size: 150%; } table { font-family: arial; font-size: 150%;} </style>")
print("<title>OlekuPaneel</title>\n")
print("<meta http-equiv='Content-Type' content='text/html; charset=utf-8'/>\n")
print("<meta http-equiv='refresh' content='3'/>\n")  # 3s tagant automaatne reload #####
#print("<style>\nhtml {background-size:cover; }\n body {margin: 0; height: 100%; font-size: 24px;\n}\n</style>")
print("</head>\n<body>")
print("<h2> Objekt: "+mac+"</h2>\n")
print("<table border='5' width='100%'>\n")  # paneeli algus
print("<tr bgcolor='#aaaaaa'><td colspan='3'>"+USER+" <b>"+location+"</b>, filter:"+str(filter)+" </td></tr>") # esimene rida


Cmd="select register,value,timestamp from state where mac = '"+str(mac)+"' and timestamp+0>"+str(tsnow)+"-"+str(maxage)+" order by register" # find all fresh data
   
cursor.execute(Cmd)
for row in cursor: #  monitooringusse saabunud key:val info hulgast selle maci varskem info. siin olek ja perfdata eraldi key-dega, lopp S voi V/W!
    if row[0] != '' and row[2] != None:
        register = row[0]
        value = row[1]
        last = int(float(row[2])) # leiame maksimumi koikide loetute hulgast
        age = int(round(tsnow - last))
        #print('register,value,age',register,value,age,'<BR>') # debug
        
    if register[-1] == 'S': # status
        #print('status ',register,value) # debug
        #if register_meelde[:-1] != register[:-1]: # uus statusregister
        if lastperfregister[:-1] != register_meelde[:-1]: # peab eelmise ootel statuserea valjastama
            print(output(register_meelde,str(status_meelde),age_meelde,status_meelde)) # yksiku statusteenuse valjastamine (siin teenuses perfdata puudub)
        register_meelde = register
        status_meelde = status
        age_meelde = age
        try: # if value != '':
            status=int(float(value)) 
        except: # else:
            status = -1 # puuduv status olgu -1, vaatame mis saab
        status_meelde = status
        
    elif register[-1] == 'V' or register[-1] == 'W': # perfdata
        lastperfregister=register # tunnus et oli V voi W
        print(output(register,filter,value,age,status_meelde))  # valjasta kohe meelesoleva staatusega
    else: 
        print(output(register,filter,value,age)) # siin ei oska mingit statust anda
    
            
conn.commit() # end transaction

print("\n</table>\n<br>\n")  # lopetame tabeli
print("</body></html>\n")

