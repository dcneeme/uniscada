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


    
class SDPBuffer: # for the messages in UniSCADA service description protocol
    def __init__(self, SQLDIR, tables): # [multiple tables as tuple]
        self.sqldir=SQLDIR
        conn = sqlite3.connect(':memory:')
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
            conn.execute(Cmd) # drop the table if it exists
            conn.commit()
            conn.executescript(sql) # read table into database
            conn.commit()
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
        cur = conn.cursor()
        cur.execute(Cmd)
        conn.commit()
        for row in cur:
            output.append(row) 
        return output


    def dump_table(self, table):
        ''' Writes a table into SQL-file '''
        msg='going to dump '+table+' into '+SQLDIR+table+'.sql'
        print(msg)
        try:
            with open(self.sqldir+table+'.sql', 'w') as f:
                for line in conn.iterdump(): # see dumbib koik kokku!
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
        cur=conn.cursor()
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
        
        conn.commit()
        return value # tuple from member values    
        
    def udp2state(self,data): # executes also statemodify to update the state table
        ress=0
        res=0
        if "id:" in data: # first check based on host id existence in the received message, must exist to be valid message!
            lines=data.splitlines()
            #print('received lines count',len(lines)) # debug
            id=data[data.find("id:")+3:].splitlines()[0]
            for i in range(len(lines)): # looking into every member (line) of incoming message
                #print('line',i,lines[i]) # debug
                if ":" in lines[i] and not 'id:' in lines[i]:
                    line = lines[i].split(':') # tuple
                    register = line[0] # setup reg name
                    value = line[1] # setup reg value
                    #print('received from controller',id,'key:value',register,value) # debug
                    res=self.statemodify(id,register,value)
                    if res == 0:
                        print('statemodify done for',id,register,value)
                    else:
                        print('statemodify FAILED for',id,register,value)
                ress+=res
        else:
            print('invalid datagram, no id found in',data)
            ress+=1
        return ress
        
    
    def statemodify(self, id, register, value): # received key:value to state table
        ''' received key:value to state table '''
        DUE_TIME=self.ts+5 # min pikkus enne kordusi, tegelikult pole vist vaja
        try: # new state for this id
            Cmd="INSERT INTO STATE (register,mac,value,timestamp,due_time) VALUES \
            ('"+register+"','"+id+"','"+str(value)+"','"+str(self.ts)+"','"+str(DUE_TIME)+"')"
            #print Cmd
            conn.execute(Cmd) # insert, kursorit pole vaja
                    
        except:   # UPDATE the existing state for id
            Cmd="UPDATE STATE SET value='"+str(value)+"',timestamp='"+str(self.ts)+"',due_time='"+str(DUE_TIME)+"' \
            WHERE mac='"+id+"' AND register='"+register+"'"
            #print Cmd
            
            try:
                conn.execute(Cmd) # update, kursorit pole vaja
                #print 'state update done for mac',id,'register',locregister # ajutine
                
            except:
                traceback.print_exc()
                return 1 # kui see ka ei onnestu, on mingi jama

        return 0 # DUE_TIME  state_modify lopp

        