# this class is to be universally used for sqlite tables in memory 
import sqlite3
import glob # for * in filenames
import sys
import traceback
conn = sqlite3.connect(':memory:')

class SQLgeneral: # for udp monitor, more generic than the droidcontroller.SQLgeneral!
    def __init__(self, SQLDIR, tables): # [multiple tables as tuple]
        self.sqldir=SQLDIR
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
        
        
