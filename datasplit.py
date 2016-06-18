def datasplit(data):
    ''' tykeldab monitor50.py jaoks mitme in keyvaluega datagrammi
    
        >>> data='id:123\nin:1,2\nI1W:1 1\nI1S:0\nin:2,3\nI1W:2 2\nI1S:1\nin:3,4\nI1W:3 3\nI1S:1\n'
        >>> datasplit(data5)
        ['id:123\nin:1,2\nI1W:1 1\nI1S:0\n', 'id:123\nin:2,3\nI1W:2 2\nI1S:1\n', 'id:123\nin:3,4\nI1W:3 3\nI1S:1\n']
        
        >>> data2='I1W:1 1\nI1S:0\nI1W:2 2\nI1S:1\nid:123\nin:1,2\n'
        >>> datasplit(data2)
        ['I1W:1 1\nI1S:0\nI1W:2 2\nI1S:1\nid:123\nin:1,2\n']
        
        >>> data3='I1W:1 1\nI1S:0\nI1W:2 2\nI1S:1\nid:123\n'
        >>> datasplit(data3)
        ['I1W:1 1\nI1S:0\nI1W:2 2\nI1S:1\nid:123\n']
    '''
    dataout = []
    if "id:" in data:
        lines=data[data.find("id:")+3:].splitlines() 
        id = lines[0] 
        #print "id",id   
        incount = len(data.split('in:')) - 1 # 0 if n is missing
        if incount > 1:
            for i in range(incount):
                inpos = data.find('in:')
                inn = data[inpos + 3:].splitlines()[0]
                appdata = 'id:'+id+'\nin:'+data.split('in:')[1]
                #print i,appdata
                dataout.append(appdata)
                data = data[inpos+4+len(inn):]
        else:
            dataout.append(data)
        return dataout # list
    else:
        print 'invalid data, missing id'
    return dataout

    