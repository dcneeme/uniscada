#sdpbuffer.py
''' Buffer to store messages in Uniscada Service Description Protocol
    (key:value pairs on separate lines, one pair in the datagaram must contain id:<host_id>,
    keys in a datagram are unique and represent either status or value(s) of a service
    or multiple services,related to the same site controller (host).
    Key for status ends with S, value contain one number (status) from 0 to 2.
    Key for value is similar to status key with last character replaces with V
    (single numerical value or string) or W (multiple space-separated numerical values).
    Each key-value pair ends with line feed (\n).
 '''

import sys
import traceback
import sqlite3
import glob
import time


class SDPBuffer: # for the messages in UniSCADA service description protocol
    def __init__(self, SQLDIR, tables, comm = None): # [multiple tables as tuple]
        self.comm = comm # from / to communication interface towards site controllers
        self.sqldir=SQLDIR
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.ts=time.time() # needs to be refreshed on every comm2state()
        print('sdpbuffer: created sqlite connection')
        for table in tables:
            if '*' in table:
                print('multiple tables read follow',table) # debug
                for singletable in glob.glob(self.sqldir+table):
                    self.sqlread(singletable.split('/')[-1].split('.')[0]) # filename without path and extension
            else:
                #print('single table',table) # debug
                self.sqlread(table)


    def sqlread(self, table): # drops table and reads from file table.sql that must exist
        sql=''
        filename=self.sqldir+table+'.sql' # the file to read from
        try:
            sql = open(filename).read()
            msg='found '+filename
            print(msg)
        except:
            msg='FAILURE in opening '+filename+': '+str(sys.exc_info()[1])
            print(msg)
            #udp.syslog(msg)
            traceback.print_exc()
            return 1

        Cmd='drop table if exists '+table
        try:
            self.conn.execute(Cmd) # drop the table if it exists
            self.conn.commit()
            self.conn.executescript(sql) # read table into database
            self.conn.commit()
            msg='sqlread: successfully recreated table '+table
            print(msg)
            #udp.syslog(msg)
            return 0

        except:
            msg='sqlread() problem for '+table+': '+str(sys.exc_info()[1])
            print(msg)
            #udp.syslog(msg)
            traceback.print_exc()
            return 1


    def print_table(self, table, column = '*'):
        ''' reads and returns he content of the table '''
        output=[]
        Cmd ="SELECT "+column+" from "+table
        cur = self.conn.cursor()
        cur.execute(Cmd)
        self.conn.commit()
        for row in cur:
            output.append(row)
        return output


    def dump_table(self, table):
        ''' Writes a table into SQL-file '''
        msg='going to dump '+table+' into '+SQLDIR+table+'.sql'
        print(msg)
        try:
            with open(self.sqldir+table+'.sql', 'w') as f:
                for line in self.conn.iterdump(): # see dumbib koik kokku!
                    if table in line: # needed for one table only! without that dumps all!
                        f.write('%s\n' % line)
            return 0
        except:
            msg='FAILURE dumping '+table+'! '+str(sys.exc_info()[1])
            print(msg)
            #syslog(msg)
            traceback.print_exc()
            return 1


    def get_column(self, table, column, like=''): # returns raw,value,lo,hi,status values based on service name and member number
        ''' Returns member values as tuple from channel table (ai, di, counter) based on service name '''
        cur=self.conn.cursor()
        if like == '':
            Cmd="select "+column+" from "+table+" order by "+column
        else:
            Cmd="select "+column+" from "+table+" where "+column+" like '"+like+"' order by "+column # filter
        #print(Cmd) # debug
        cur.execute(Cmd)
        value=[]
        for row in cur: # one row per member
            #print('get_value() row:', row) # debug
            value.append(row[0])

        self.conn.commit()
        return value # tuple from member values


    def comm2state(self, host, data): # executes also statemodify to update the state table
        ress=0
        res=0
        valueback = ''
        self.ts=time.time()
        if "id:" in data: # first check based on host id existence in the received message, must exist to be valid message!
            lines=data.splitlines()
            #print('received lines count',len(lines)) # debug
            id=data[data.find("id:")+3:].splitlines()[0]
            #res = self.controllermodify(id, addr) # update socket data if changed
            res=0
            if res != 0:
                print('unknown host id',id,'in the message from',addr)
                return res # no further actions for this illegal host

            inn=data[data.find("in:")+3:].splitlines()[0] # optional datagram id
            Cmd="BEGIN TRANSACTION" #
            self.conn.execute(Cmd)
            for i in range(len(lines)): # looking into every member (line) of incoming message
                #print('line',i,lines[i]) # debug
                if ":" in lines[i] and not 'id:' in lines[i] and not 'in:' in lines[i]:
                    line = lines[i].split(':') # tuple
                    register = line[0] # setup reg name
                    value = line[1] # setup reg value
                    print('received from controller',id,'key:value',register,value) # debug
                    if '?' in value: # return the buffered value from state
                        cur = self.conn.cursor() # local!
                        Cmd="select value from state where mac='"+id+"' and register='"+register+"'"
                        cur.execute(Cmd)
                        for row in cur:
                            valueback = row[0]
                        print('going to answer to/with', id, register, valueback) # debug
                        res = self.newstatemodify(id,register,valueback)
                    
                    else:
                        res = self.statemodify(id, register, value) # only if host id existed in controller
                        if res == 0:
                            print('statemodify done for', id, register, value)
                        else:
                            print('statemodify FAILED for', id, register, value)
                ress += res
            self.conn.commit() # transaction end
            sendmessage = self.message4host(id, inn) # ack, w newstate
            self.message2host(host, sendmessage)
        else:
            print('invalid datagram, no id found in', data)
            ress += 1
        return ress


    def statemodify(self, id, register, value): # received key:value to state table
        ''' Received key:value to state table. This is used by comm2state() '''
        DUE_TIME=self.ts+5 # min pikkus enne kordusi, tegelikult pole vist vaja
        try: 
            Cmd="INSERT INTO STATE (register, mac, value, timestamp, due_time) VALUES \
            ('"+register+"','"+id+"','"+str(value)+"','"+str(self.ts)+"','"+str(DUE_TIME)+"')"
            print Cmd # debug
            self.conn.execute(Cmd) # insert, kursorit pole vaja

        except:   # UPDATE the existing record
            Cmd="UPDATE STATE SET value='"+str(value)+"',timestamp='"+str(self.ts)+"',due_time='"+str(DUE_TIME)+"' \
            WHERE mac='"+id+"' AND register='"+register+"'"
            print Cmd # debug
            try:
                self.conn.execute(Cmd) # update, kursorit pole vaja
            except:
                traceback.print_exc()
                return 1 
        return 0


    def newstatemodify(self, id, register, value): # received key:value to newstate table
        ''' Commands and setup values to by pairs to newstate table, to be sent regularly '''
        if value == '' or value == None:
            print('no value for newstate, exiting newstatemodify')
            return 1
            
        try: 
            Cmd="INSERT INTO newstate(register,mac,value,timestamp) VALUES \
            ('"+register+"','"+id+"','"+str(value)+"','"+str(self.ts)+"')"
            print Cmd  # debug
            self.conn.execute(Cmd) # insert, kursorit pole vaja
            return 0

        except:   # no updates, insert only
            print('newstatemodify could not add to newstate', id, register, value)
            return 1 
   
   
    def controllermodify(self, id, addr): # socket data refresh in controller table if changed
        ''' Refreshes the socket data in the controller table for a host.
            Auto adding (new unknown) records for testing could be possible. Socket changes to be detected?
        '''
        Cmd="UPDATE controller SET socket='"+str(addr[0])+","+str(addr[1])+"',socket_ts='"+str(self.ts)+"' \
            WHERE mac='"+id+"' and socket !='" +str(addr[0])+","+str(addr[1])+"'" # keeps the last change time

        try: # new state for this id
            self.conn.execute(Cmd) # insert, kursorit pole vaja
            self.conn.commit()
            return 0
        except:   # no such id
            print(Cmd) # debug
            traceback.print_exc() # debug
            return 1


    def message4host(self, id, inn = 0): # for one host at the time. inn = msg id to ack, skip for commands
        ''' Putting together message to a host, just id if used for ack or also data from newstate if present for this host '''

        #cur = self.conn.cursor()
        Cmd="BEGIN TRANSACTION" #
        self.conn.execute(Cmd)

        Cmd="select newstate.register,newstate.value from newstate LEFT join state on newstate.mac = state.mac and \
        newstate.register=state.register where ( state.value <> newstate.value or newstate.register in \
        (select register from commands where commands.register = newstate.register)) and  \
        (newstate.retrycount < 9 or newstate.retrycount is null) and newstate.mac='" + str(id) + "' limit 10"

        #print Cmd
        self.cursor.execute(Cmd)  # read from newstate table

        if inn == "":
            data = "id:" + id + "\n" # alustame vastust id-ga
        else:
            data = "id:" + id + "\nin:" + inn + "\n" # saadame ka in tagasi

        answerlines = 0
        for row in self.cursor:
            #print "select for sending to controller newstate left join state row",row
            register=row[0]
            value=row[1]
            data=data + str(register) + ":" + str(value) + "\n" # cmd or setup message to host in addition to id and inn
            answerlines = answerlines + 1

        #retrycount refresh, not needed if no cmd / setup to send
        if answerlines > 0:
            # retrycount must be updated
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

            self.conn.execute(Cmd)

        self.conn.commit() # end transaction

        print("---answer or command to the host ", id, data) # debug
        return data


    def message2host(self, host, data): # actual send based on eval(self.sender)
        host.comm.send(host.chdata,data)
        

    def setcomm(self, comm): # cannot set it in init, unknow at this time
        self.comm =  comm