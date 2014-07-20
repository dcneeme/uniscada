#!/usr/bin/python
#see salvestab bn3setup.py poolt saadetavad registrid/vaartused newstate tabelisse
#neeme muutis 21.01.2012
# 16.06.2013 ei ole vaja saata neid muutujaid, mis on juba soovitud vaartusega. vordle state tabeliga!

 
# Import modules for CGI handling 
import sys, cgi, cgitb ,re # neeme lisas sys 13.07.2012
cgitb.enable() # neeme lisas 21.01.2012

#from pysqlite2 import dbapi2 as sqlite3
from sqlite3 import dbapi2 as sqlite3 # basen serveris

import string
import traceback


def getall(theform, nolist=False):
    """
    Passed a form (cgi.FieldStorage
    instance) return *all* the values.
    This doesn't take into account
    multipart form data (file uploads).
    It also takes a keyword argument
    'nolist'. If this is True list values
    only return their first value.
    """
    data = {}
    for field in theform.keys():                
    # we can't just iterate over it, but must use the keys() method
        if type(theform[field]) ==  type([]):
            if not nolist:
                data[field] = theform.getlist(field)
            else:
                data[field] = theform.getfirst(field)
        else:
            data[field] = theform[field].value
    return data


# Create instance of FieldStorage 
theform = cgi.FieldStorage() 

# Get data from fields
mac = theform.getvalue('mac')

# sql baas
conn = sqlite3.connect('monitor',1)
#kuhu panna monitor.ini vms, metacommands? .timeout 200 naiteks voiks olla
cursor=conn.cursor()


# kui siin kommentaar, naed sorcu - oigemine brauser pakub siin toodetut faili salvestada
print "Content-type: text/html"
print

print '<p> mac',mac,'</p>' # ajutine abi

# Koik valjad
formdict = getall(theform)
params = []

#print formdict

# loome regulaaravaldise, mis vastab bitmuutujatele
regexp = r'([bB][0-9]+)[bB]([0-7])'
bit_regexp = re.compile(regexp)
bit_registers = {}




#sql_string='insert into newstate (mac,register,value) values '
sql_string_start="insert into newstate (mac,register,value) values "
sql_string = ""

Cmd="BEGIN IMMEDIATE TRANSACTION" # lisasin IMMEDIATE, toimub monitor baasiga
#cursor.execute(Cmd) # miks kursor? voiks olla conn.execute
conn.execute(Cmd) # miks kursor? voiks olla conn.execute

jama=0


#try:
if mac <> None : 
    for entry in formdict:
        # mac on meie oma muutuja
        if entry <>  "mac":
            varinfo = bit_regexp.search(entry)
            if  varinfo <> None: # bitimuutujad
                # register name
                reg_name = varinfo.group(1) 
                # bit position
                reg_bitpos = varinfo.group(2) 
                if  bit_registers.get(reg_name) == None:
                    bit_registers[reg_name] = 0
                if str(formdict[entry]) == "1" :
                    bit_registers[reg_name] =  int(bit_registers[reg_name]) | (128 >> int(reg_bitpos))
                #print "var="+entry+" bitpos ="+reg_bitpos+" bit="+str(128 >> int(reg_bitpos))+" vaartus="+str(formdict[entry]) 
            else: # byte muutujad
                Cmd="select value from state where mac='"+mac+"' and register='"+entry+"'" # neeme lisa, et ilmaaegu newstate yle ei koormaks
                cursor.execute(Cmd)
                for row in cursor: # peaks tulema yks vastusrerida
                    value=row[0]
                
                if value<>formdict[entry]: # on erinev, voib salvestada newstate sisse
                    sql_string = sql_string_start +  "(\'"+mac+"\',\'"+entry+"\',\'"+str(formdict[entry])+"\')"
                    #print "<p> value entry sql",value,formdict[entry],sql_string # ajutine debug
                    try:
                        cursor.execute(sql_string)
                    except:
                        print "Error for",sql_string
                        traceback.print_exc()
                        jama=1

    # nyy teeme sql laused koigi bit muutujatega
    #print "bitvars <p>"
    for bitvar in bit_registers:
        sql_string = sql_string_start +  "(\'"+mac+"\',\'"+bitvar+"\',\'"+str(bit_registers[bitvar])+"\');"
        cursor.execute(sql_string)
        print sql_string # ajutine abi 2
    # tegelikult ei kasuta bitimuutujaid, alati baitides/sonades seadistus...

    if jama == 0:
        print "<p>Andmed on salvestatud ja uuendatakse kontrolleris paari minuti jooksul"
        conn.commit()
        print "<p><FORM><INPUT TYPE='button' VALUE='Tagasi' onClick='history.go(-1);return true;'/></FORM>"
    
    else:
        print "<p>Andmete salvestamisel tekkis viga, eelmine info on ilmselt veel saatmata! Proovi hiljem uuesti."
        print "<p><FORM><INPUT TYPE='button' VALUE='Tagasi' onClick='history.go(-1);return true;'/></FORM>"
    

#except:
else:
    print "<p>mac missing! kontrolli uiappsetup1.html form setup.cgi rida!</p>" # Ootamatu viga, proovi uuesti"
    traceback.print_exc()
    #traceback.print_exc(file=sys.stdout) # see ehk naitab valja ka mis viga oli

