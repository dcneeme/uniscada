#!/usr/bin/python
#vaata ka setup.py!
# see tootleb regulaaravaldite abil veebitage ja kaivitab alamprotsessina setup.py

# Import modules for CGI handling 
import cgi, cgitb ,re
#from pysqlite2 import dbapi2 as sqlite3
from sqlite3 import dbapi2 as sqlite3 # basen serveris

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mac = form.getvalue('mac')
filename = form.getvalue('file')


f = open(mac+"/"+filename, "r")
text = f.read()

# kui siin kommentaar, naed sorcu
print "Content-type: text/html"
print

# koik vaartused sellele macile 
# select mac,register,value from state  
conn = sqlite3.connect('monitor')
#kuhu panna monitor.ini vms, metacommands? .timeout 200 naiteks voiks olla
cursor=conn.cursor()
cursor.execute('select register,value from state where mac = '+"'"+mac+"'")
for row in cursor:
	# intelligente vark asendame group 1 group 2 mis leidsime ja lisame value=row[1] sellega lahevad koik tavalised valjad
	# muutujate printimine, kommenteeri valja kui tahad muutujaid andmebaasist naha
	# print row[0]+" "+row[1]
	

	text = re.sub(r'(name=[\"\']?'+re.escape(str(row[0]))+r'[\"\']? )(.*?)value=[\"\']?(.*?);[\"\']?',  r'\1\2 value="'+str(row[1])+r'"',text)
	#nyyd asendame selectid mis pole bitmapid
	# <select size=1 name=W512>
        #   <option value=0&LSetup(3,"%s",512,W,0,"
        text = re.sub(r'(option.value='+re.escape(str(row[1]))+r')&LSetup\([0-9],"..",'+re.escape(row[0][1:])+r',(.*?);' ,  r'\1 selected="selected"',text)
	# bitmap muutujad veel teha.
	



##
## Koik  LSetupid, mida seni ei asendatud, saavad tyhjad vaartused
##
##

# Asendame koigpealt tavalised valjad  tyhjadega, st jutukatega
regexp = r'[\"\']?\&LSetup\([0-9],"%[sud]",' + r'[0-9]+' + r'(,.)?\);[\"\']?'
p = re.compile(regexp)
text = p.sub(r'""',text)

# nyyd selected asjad uueks, st paris tyhjaks isegi jutumarke pole
regexp = r'[\"\']?\&LSetup\([0-9],"%[su]",' + r'[0-9]+' + r'.*?\);[\"\']?'
p = re.compile(regexp)
text = p.sub(r'',text)

# Korjaks ara ka need LBASid
regexp = r'[\"\']?\&LBAS\([0-9],.*?\);[\"\']?'
p = re.compile(regexp)
text =   p.sub(r'',text)

# Korjaks ara ka need &L()
regexp = r'[\"\']?\&L\(.*?\);[\"\']?'
p = re.compile(regexp)
text =   p.sub(r'',text)


# Korjaks ara &LIO()  # neeme 13jul 2012 - asendada neid state vaartustega nagunii ei saa...
regexp = r'[\"\']?\&LIO\(.*?\);[\"\']?'
p = re.compile(regexp)
text =   p.sub(r'',text) # see asendab tyhjusega


# setup cgi tuleb asendada setup py ga
regexp = r'setup.cgi'
p = re.compile(regexp)
text =   p.sub(r'setup.py',text)


# Mac aadress tuleb edasi kanda L value sees
#regexp = r'name=["]?L["]? value=["]?uisaved.html["]?'
regexp = r'name=["]?L["]? value=["]?ui.*.html["]?' # neeme 13jul2012 et sobiks molemad
#regexp = r'name=["]?L["]? value=["]?uiappsetup1.html["]?'
p = re.compile(regexp)
print  p.sub(r'name="mac" value="'+mac+r'"',text)


