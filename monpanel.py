#!/usr/bin/python
# -*- coding: utf_8 -*-
#
# 08.04.2014 kasutajale lubatud hostgruppide ja hostide mobiilsele kliendile raporteerimine. nagiose query, json.load test


''' USAGE

from monpanel import *
s=Session() # instance tekitamine, teeb ka abitabeleid

#print FROM,USER
nagiosdata=s.get_userdata_nagios(FROM,USER)
s.nagios_hosts2sql(nagiosdata)
#s.dump_table()
s.sql2json() # paranda default query ja filter
s.sql2json(query='servicegroups', filter ='')
s.sql2json(query='hostgroup', filter ='saared')
s.sql2json(query='servicegroup', filter ='service_pumplad4_ee')

s.state2buffer() # read state to find updates, temporary polling!!
s.buffer2json() # service update json ws kliendle

'''

import cgi, cgitb ,re # Import modules for CGI handling
#cgitb.enable()

import sqlite3
import time
import traceback
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')  # proovime kas aitab? reload() vajalik!! AITAS! aga voib midagi untsu keerata py2 jaoks! py3 ongi utf8 default.
import requests  #  subprocess
import json
query=''

FROM='n.itvilla.com/get_user_data?user_name='
USER='sdmarianne' # :kvv6313    #  'sdtoomas'



class Session:
    ''' This class handles data for mobile operator panel of the UniSCADA monitoring via websocket '''

    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        #self.conn.text_factory = str # tapitahtede voimaldamiseks/ voi vastupidi, utf8 keelamiseks??? utf on u, mitte s
        self.conn.text_factory = lambda x: unicode(x, "utf-8", "ignore") # proovime nii, ignoreerib kui pole utf8?
        self.conn2 = sqlite3.connect('/srv/scada/sqlite/monitor') # ajutiselt, kuni midagi paremat tekib. state ja newstate tabelid
        #self.conn2.text_factory = str # tapitahtede voimaldamiseks
        self.conn2.text_factory = lambda x: unicode(x, "utf-8", "ignore")
        self.ts_last = 0 # last execution of state2buffer(), 0 means never

        self.conn.executescript("BEGIN TRANSACTION;CREATE TABLE servicebuffer(hid,key,status INT,value,timestamp NUMERIC); \
            CREATE UNIQUE INDEX hid_key_servicebuffer on 'servicebuffer'(hid,key);COMMIT;")
        self.conn.commit() #created servicebuffer

        self.conn.executescript("BEGIN TRANSACTION;CREATE TABLE 'ws_hosts'(hid,halias,ugid,ugalias,hgid,hgalias,cfg,servicegroup);COMMIT;")
        self.conn.commit() # created ws_hosts

        self.sqlread('/srv/scada/sqlite/controller.sql') # copy of hosts configuration data into memory

    def get_userdata_nagios(self,FROM,USER):
        '''Gets data fro user USER from Nagios FROM '''
        # https://hvv.itvilla.com/get_user_data?user_name=USER
        req = 'https://'+FROM+USER

        try:
            response = json.loads(requests.get(req).content)
            USERCHK=response.get('user_data').get('user_name')
            if USERCHK != USER:
                print('invalid response',response)
                exit()
            return response.get('user_data').get('user_groups'), response.get('user_data').get('hostgroups') # return tuple of [hostgroups,usergroups]
        except:
            msg='problem with nagios query, '+str(sys.exc_info()[1])
            print(msg)
        pass


    def sqlread(self, filename): # drops table and reads from sql file filename that must exist
        table = str(filename.split('.')[0].split('/')[-1:])
        try:
            sql = open(filename).read()
        except:
            msg='FAILURE in sqlread: '+str(sys.exc_info()[1]) # aochannels ei pruugi olemas olla alati!
            print(msg)
            return 1

        Cmd='drop table if exists '+table
        try:
            self.conn.execute(Cmd) # drop the table if it exists
            self.conn.executescript(sql) # read table into database
            self.conn.commit()
            msg='sqlread: successfully recreated table '+table
            #print(msg)
            return 0
        except:
            msg='sqlread: '+str(sys.exc_info()[1])
            print(msg)
            return 1



    def dump_table(self, table = 'ws_hosts', where=''):
        ''' reads the content of the table, debugging needs only '''
        ''' reads the content of the table, debugging needs only '''
        Cmd ="SELECT * from "+table
        if len(where)>0:
            Cmd=Cmd+' '+where # whatever condition
        cur = self.conn.cursor()
        cur.execute(Cmd)
        for row in cur:
            print(row)
        self.conn.commit() # kas on vaja kui transactioni pole?


    def sql2json(self, query = 'hostgroup', filter = 'saared'):
        ''' Returns json data about hosts and their groups based on query type and optional filtering parameter '''
        self.conn.row_factory = sqlite3.Row # This enables column access by name: row['column_name']
        cur=self.conn.cursor()
        rows={}
        # 'ws_hosts'(hid,halias,ugid,ugalias,hgid,hgalias,cfg,servicegroup)
        if (query == 'hostgroups' and filter == None):
            Cmd="select hgid as hostgroup, hgalias as alias from ws_hosts group by hgid" # gruppide loetelu
            rows = cur.execute(Cmd).fetchall()
            self.conn.commit()
            return json.dumps( [dict(ix) for ix in rows] )

        elif query == 'hostgroups':
            #filter=filter
            Cmd="select hid, servicegroup, halias from ws_hosts where hgid='"+filter+"'" # gruppide loetelu
            #print(Cmd) # debug
            cur.execute(Cmd)
            hdata={}
            hgdata = {"hostgroup":filter, "hosts":[] }
            for row in cur:
                hdata['id']=row[0]
                hdata['servicegroup']=row[1]
                hdata['alias']=row[2].encode('utf-8').strip() # to avoid errors of utf8 codec
                hgdata['hosts'].append(hdata)
            return json.dumps(hgdata)

        elif (query == 'servicegroups' and filter == None): # list servicegroups without services in use for hosts
            Cmd="select servicegroup from ws_hosts group by servicegroup" # gruppide loetelu lihtsalt, pole tegelikult vaja, hostide infos olemas
            rows = cur.execute(Cmd).fetchall()
            self.conn.commit()
            return json.dumps( [dict(ix) for ix in rows] )

        elif query == 'servicegroups': # services in the servicegroup to be returned
            #filter=filter
            #(svc_name,sta_reg,val_reg,in_unit,out_unit,conv_coef,desc0,desc1,desc2,step,min_len,max_val,grp_value,multiperf,multivalue,multicfg)
            Cmd="select sta_reg, val_reg, svc_name, out_unit, desc0, desc1, desc2, multiperf, multivalue, multicfg from "+filter #
            #print(Cmd) # debug
            cur.execute(Cmd) #
            hgdata = {"servicegroup": filter, "services":[] }
            for row in cur: # service loop
                hdata={}
                sta_reg=row[0]
                val_reg=row[1]
                hdata['svc_name']=row[2]
                unit=row[3]
                desc=[]
                desc.append(row[4].encode('utf-8').strip()) # to avoid errors of utf8 codec
                desc.append(row[5].encode('utf-8').strip()) # to avoid errors of utf8 codec
                desc.append(row[6].encode('utf-8').strip()) # to avoid errors of utf8 codec
                multiperf=row[7]
                multivalue=row[8] # to be shown in the end of desc after colon
                try: # igas teenusetabelis ei ole esialgu seda tulpa
                    multicfg=row[9] # configurable
                except:
                    multicfg=''

                # key finding, depends.... svc_name can be used instead of key in fact.
                if ((val_reg[-1:] == 'V' or val_reg[-1:] == 'W') and sta_reg[-1:] =='S'): # single perf or multiperf service. must have sta_reg too.
                    show=True
                    key=val_reg
                elif (val_reg == '' and sta_reg[-1:] == 'S'): # status, single on/off, value will be the same as status for grapring via perf
                    show=True
                    key=sta_reg
                elif (val_reg != '' and sta_reg == ''): # no status, must be general setup variable or cmd, not related to service configuration
                    show=False
                    key=val_reg
                else:
                    #print 'strange service',sta_reg,val_reg # debug
                    key='' # '?'+sta_reg+val_reg+'?' # neid ei naita, kuna teenustetabelis defineerimata
                    show=False

                if key != '': # skip if no key
                    hdata['key']=key
                    hdata['show']=show
                    # members status and desc
                    mperf=multiperf.split(' ')
                    mvalue=multivalue.split(' ')
                    #print 'key,mperf,mvalue',key,mperf,mvalue # debug

                    hdata['description']=[]
                    for dm in range(len(desc)): # desc0 desc1 desc2 processing ##############################################
                        desc_dm=''
                        description={}
                        description['status']=dm # 0 1 2

                        if (len(mvalue) > 0 and len(mperf) > 0): # there are members, some members to be shown too
                            if ':' in desc[dm]: # show values only if colon in desc
                                for m in range(len(mperf)):
                                    if str(m+1) in mvalue:
                                        desc_dm=desc[dm]+' {{ '+mperf[m]+'.val }}'+unit
                        description['desc']=desc_dm
                        hdata['description'].append(description)

                    hdata['multiperf']=[]
                    for mp in range(len(mperf)): # multicfg processing #####################################################
                        multiperf={}
                        multiperf['member']=mp # 0+1...
                        multiperf['name']=mperf[mp]
                        multiperf['cfg']=False
                        if (len(multicfg) > 0 and len(mperf) > 0): # there are members, some members are configurable too
                            if str(mp+1) in multicfg:
                                multiperf['cfg']=True
                        hdata['multiperf'].append(multiperf)

                    hgdata['services'].append(hdata)

            return json.dumps(hgdata)

        else:
            print('illegal query parameter',query) # debug
            return None

        try:
            rows = cur.execute(Cmd).fetchall()

        except:
            traceback.print_exc()
        #print rows # debug


    def reg2key(self,hid,register): # returns key,staTrue,staExists,valExists based on hid,register. do not start transaction or commit her!
        cur=self.conn.cursor() # peaks olema soltumatu kursor
        sta_reg=''
        val_reg=''
        staTrue=False
        staExists=False
        valExists=False
        key=''
        Cmd="select servicetable from controller where mac='"+hid+"'"
        cur.execute(Cmd)
        for row in cur: # one row
            servicetable=row[0]
        Cmd="select sta_reg, val_reg from "+servicetable+" where sta_reg='"+register+"' or val_reg='"+register+"'"
        cur.execute(Cmd)
        for row in cur: # one row
            #svc_name=row[0]
            sta_reg=row[0]
            val_reg=row[1]

        if sta_reg !='': # sta_reg in use
            staExists=True
            if register == sta_reg:
                staTrue=True
            elif register == val_reg:
                staTrue=False
            key=val_reg # in most cases

        if val_reg !='': # val_reg exist
            valExists=True
            if register == sta_reg:
                staTrue=True
            elif register == val_reg:
                staTrue=False
            key=val_reg # in most cases

        return key,staTrue,staExists,valExists # '',False,False,False if not defined in servicetable



    def nagios_hosts2sql(self, data, table = 'ws_hosts'): # incoming data is tuple: groupdata, user_data. fills ws_hosts
        ''' data from nagios put into tuple data
        [{u'saared': {u'alias': u'saared', u'members': {u'00204AB80BF9': u'saared tempa kanal'}}},
        {u'saared': {}, u'kvv': {u'00204AB80BF9': u'saared tempa kanal'}}}]
        Also adds servicegroup info from controllers. Does it gets dumped on each addcontroller?

        '''
        cur=self.conn.cursor()
        Cmd="BEGIN IMMEDIATE TRANSACTION"
        self.conn.execute(Cmd)
        # ws_hosts(hid,halias,ugid,ugalias,hgid,hgalias,cfg,servicegroup)
        for gid in data[0].keys(): # access info usr_group alusel
            groupdata=data[0].get(gid) #
            #galias=groupdata.get('alias') # seda ei ole esialgu user_group jaoks
            for hid in groupdata.keys():
                halias=groupdata.get(hid)
                Cmd="insert into "+table+"(hid,halias,ugid) values('"+hid+"','"+halias+"','"+gid+"')"
                #print(Cmd) # debug
                self.conn.execute(Cmd)

        for gid in data[1].keys(): # hostgroup kuuluvus  - neid voib olla rohkem kui neid millele on ligipaas. where filtreerib valja!
            groupdata=data[1].get(gid) # alias, members{}
            galias=groupdata.get('alias') # seda ei ole esialgu!
            members=groupdata.get('members')
            for member in members.keys():
                hid=member
                Cmd="select servicetable from controller where mac='"+hid+"'"
                cur.execute(Cmd)
                for row in cur:
                    servicetable=str(row[0])
                    Cmd="update "+table+" set hgid='"+gid+"',hgalias='"+galias+"', servicegroup='"+servicetable+"' where hid='"+hid+"'"
                #print(Cmd) # debug
                self.conn.execute(Cmd)

        Cmd="select servicegroup from ws_hosts group by servicegroup" # open servicetables for service translations
        cur.execute(Cmd)
        for row in cur:
            servicetable=str(row[0])
            self.sqlread('/srv/scada/sqlite/'+servicetable+'.sql')

        # controller and used servicetables must remain accessible in memory
        self.conn.commit()


    def state2buffer(self, hostgroup = 'saared'): # FIXME filter hostgroup alusel vajalik!
        ''' Returns service refresh data as json in case of change or update from host based on timestamp.
            With default ts_last all services are returned, with ts_last > 0 only those updated since then.
        '''
        cur2=self.conn2.cursor()
        self.ts = int(round(time.time()))
        if self.ts_last == 0:
            ts_last = self.ts - 300 # first execution, limit the number of selected records (no id filter here until FIXME!)

        #  servicebuffer(hid,svc_name,sta_reg,status INT,val_reg,value,timestamp NUMERIC) via conn
        Cmd="BEGIN IMMEDIATE TRANSACTION"
        self.conn.execute(Cmd) # transaction for servicebuffer
        #Cmd="select mac,register,value from state where timestamp+0>"+str(self.ts_last) # use last ts here
        Cmd="select mac,register,value,timestamp from state where timestamp+0>"+str(self.ts_last)+" and (mac='00204AA95C56' or mac='00204AB80D57')" # debug, limit the hosts
        #print(Cmd) # debug
        cur2.execute(Cmd)
        self.conn2.commit()
        for row in cur2:
            hid=row[0]
            register=row[1]
            value=row[2].encode('utf-8').strip() # to avoid errors of utf8 codec
            timestamp=row[3]
            #print('hid,register,value',hid,register,value) # debug

            regkey=self.reg2key(hid,register) # returns key,staTrue,staExists,valExists # all but first are True / False
            key=regkey[0]
            if regkey[1] == True: # status
                status=int(value) # replace value with status
                if regkey[3] == False:
                    value=str(status)

            if regkey[1] == False: # value
                if regkey[2] == False: # no status
                    status=0 # or -1?

            if key != '': # service defined in serviceregister
                try:
                    Cmd="insert into servicebuffer(hid,key,status,value,timestamp) values('"+hid+"','"+key+"','"+str(status)+"','"+value+"','"+str(timestamp)+"')" # orig timestamp
                    self.conn.execute(Cmd)
                except:
                    #traceback.print_exc() # debug insert
                    #return 2 # debug
                    if regkey[1] == True: # status
                        Cmd="update servicebuffer set status='"+str(status)+"' where key='"+key+"' and hid='"+hid+"'" # no change to value
                    else: # must be value
                        Cmd="update servicebuffer set value='"+value+"' where key='"+key+"' and hid='"+hid+"'"
                    self.conn.execute(Cmd)
                #print(Cmd) # debug, what was selected

        self.conn.commit() # servicebuffer transaction end
        self.ts_last = self.ts
        return 0




    def buffer2json(self):
        '''  Returns json for service refresh in websocket client '''
        #servicebuffer(hid,key,status INT,value,timestamp NUMERIC)
        cur=self.conn.cursor()
        cur2=self.conn.cursor()
        Cmd="BEGIN IMMEDIATE TRANSACTION"
        self.conn.execute(Cmd) # transaction for servicebuffer
        Cmd="select hid from servicebuffer where status IS NOT NULL and value<>'' group by hid" # wait for for update
        cur.execute(Cmd)
        hid=''
        hid=''
        data=[] # tegelikult 1 host korraga
        hdata={}
        for row in cur: # hosts loop
            hid=row[0] # host id
            hdata={}
            hdata['host']=hid
            hdata['services']=[]
            hdata['timestamp']=self.ts # current time, not the time from hosts
            # servicebuffer(hid,svc_name,status INT,value,timestamp NUMERIC);
            Cmd="select * from servicebuffer where status IS NOT NULL and value<>'' and hid='"+hid+"'" #
            cur2.execute(Cmd)
            for row2 in cur2: # services loop
                key=row2[1]
                status=row2[2] # int
                value=row2[3] #
                sdata={}
                sdata['key']=key
                sdata['status']=status
                sdata['value']=[]
                if key[-1:] == 'W':
                    valmems=value.split(' ') # only if key ends with W
                else:
                    valmems=[value] # single value

                for mnum in range(len(valmems)): # value member loop
                    valmember={}
                    valmember['member']=mnum+1
                    valmember['val']=valmems[mnum]
                    sdata['value'].append(valmember) # member ready
                hdata['services'].append(sdata) # service ready
            #print('hdata: ',hdata) # debug
            data.append(hdata) # host ready


        Cmd="delete from servicebuffer where status IS NOT NULL and value<>''"
        self.conn.execute(Cmd)
        self.conn.commit()
        #print data # debug
        return json.dumps(data)



# ##################### MAIN #############################



if __name__ == '__main__':

    COOKIEAUTH_DOMAIN = 'itvilla_com'

    USER = None

    import Cookie
    try:
        USER = Cookie.SimpleCookie(os.environ["HTTP_COOKIE"])[COOKIEAUTH_DOMAIN].value.split(':')[0]
    except (Cookie.CookieError, KeyError, IndexError):
        print("Status: 401 Not Found")
        print("Content-type: application/json; charset=utf-8")
        print
        print("{\n  \"message\" : \"User not authenticated\"\n}\n")
        sys.exit(0)

    # starting with http output
    print("Content-type: application/json")
    print

    USER='sdmarianne' # debug, kui kommenteerida, votab tegeliku kasutaja cookie alusel.

    s=Session()

    # Create instance of FieldStorage
    form = cgi.FieldStorage()

    # Get data from fields
    query =  form.getvalue('query')
    if query == None:
        print('query parameter missing') # debug
        sys.exit()

    elif query == 'hostgroups': # START WITH THIS query! otherwise the rest will fail.
        filter = form.getvalue('hostgroup')

    elif query == 'servicegroups':
        filter = form.getvalue('servicegroup')

    elif query == 'services': # return service update information as pushed via websocket
        filter=''

    else:
        print('illegal query parameter',query) # debug
        #exit() # illegal query, comment for debugging
        pass

    # actual query execution

    nagiosdata=s.get_userdata_nagios(FROM, USER) # get user rights relative to the hosts
    s.nagios_hosts2sql(data=nagiosdata) # fill ws_hosts table and creates copies of servicetables in the memory

    print(s.sql2json(query = query, filter = filter)) # outputs json
