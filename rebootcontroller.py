#!/usr/bin/python
# reboot controller from within nagios as reaction to button ONCLICK

# Import modules for CGI handling 

import cgi, cgitb, re
from pysqlite2 import dbapi2 as sqlite3

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac = form.getvalue('mac')
filename = form.getvalue('file')




# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print

#if ..... # kontrolliks kas side on olemas, buttons.pys teab 
#else:
    try:
	cursor.execute('insert into newstate(mac,register,value) values('+"'"+mac+"','"'+"'cmd,'REBOOT'") 
        print "Korraldus salvestatud, reaktsioon peaks avalduma kuni 5 minuti jooksul."

    except:
        print "Eelmine korraldus sellele kontrollerile on ootel, saatmine ei onnestunud.<br/>" 
        print "Proovi hiljem uuesti."



