''' Uniscada Service Description Protocol
'''

import logging
log = logging.getLogger(__name__)

class SDP:
    def __init__(self):
        print type(self)
        self.data = {}
        self.data['data'] = {}
        self.data['status'] = {}
        self.data['value'] = {}
        self.data['values'] = {}

    def add_keyvalue(self, key, val):
        if key[-1] == 'S':
            self.add_status(key[:-1], int(val))
        elif key[-1] == 'V':
            self.add_value(key[:-1], val)
        elif key[-1] == 'W':
            self.add_values(key[:-1], map(int, val.split(' ')))
        else:
            self.data['data'][key] = val

    def add_status(self, key, val):
        self.data['status'][key] = int(val)

    def add_value(self, key, val):
        self.data['value'][key] = val

    def add_values(self, key, val):
        self.data['values'][key] = val

    def get_data(self):
        return self.data

    def encode(self, id=None):
        datagram = ''
        if id:
            self.add.keyvalue('id', id)
        if not 'id' in self.data['data']:
            raise Exception("id missing");
        for key in self.data['data'].keys():
            datagram += key + ':' + str(self.data['data'][key]) + '\n'
        for key in self.data['status'].keys():
            datagram += key + 'S:' + str(self.data['status'][key]) + '\n'
        for key in self.data['value'].keys():
            datagram += key + 'V:' + str(self.data['value'][key]) + '\n'
        for key in self.data['values'].keys():
            datagram += key + 'W:' + ' '.join(map(str, self.data['values'][key])) + '\n'
        return datagram

    def decode(self, datagram):
        for line in datagram.splitlines():
            try:
                (key, val) = line.split(':')
            except:
                raise Exception('error in line: \"' + line + '\"')
            self.add_keyvalue(key, val)

    def __str__(self):
        s = ''
        for key in self.data['data'].keys():
            s += 'key=\"' + str(key) + '\", val=\"' + str(self.data['data'][key]) + '\"\n'
        for key in self.data['status'].keys():
            s += 'key=\"' + str(key) + 'S\", val=\"' + str(self.data['status'][key]) + '\"\n'
        for key in self.data['value'].keys():
            s += 'key=\"' + str(key) + 'V\", val=\"' + str(self.data['value'][key]) + '\"\n'
        for key in self.data['values'].keys():
            s += 'key=\"' + str(key) + 'W\", val=' + str(self.data['values'][key]) + '\n'
        return s
