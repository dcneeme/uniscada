''' Uniscada Service Description Protocol
'''

import logging
log = logging.getLogger(__name__)

class SDP:
    def __init__(self):
        self.data = {}
        self.data['data'] = {}
        self.data['status'] = {}
        self.data['value'] = {}

    def add_keyvalue(self, key, val):
        if key[-1] == 'S':
            self.add_status(key[:-1], int(val))
        elif key[-1] == 'V':
            self.add_value(key[:-1], str(val))
        elif key[-1] == 'W':
            self.add_value(key[:-1], list(map(int, val.split(' '))))
        else:
            self.data['data'][key] = val

    def add_status(self, key, val):
        self.data['status'][key] = int(val)

    def add_value(self, key, val):
        self.data['value'][key] = val

    def get_data(self, key):
        if key[-1] == 'S':
            return self.data['status'].get(key[:-1], None)
        elif key[-1] == 'V' or key[-1] == 'W':
            return self.data['value'].get(key[:-1], None)
        else:
            return self.data['data'].get(key, None)

    def get_data_list(self):
        for key in self.data['data'].keys():
            yield (key, str(self.data['data'][key]))
        for key in self.data['status'].keys():
            yield (key + 'S:', str(self.data['status'][key]))
        for key in self.data['value'].keys():
            if isinstance(self.data['value'][key], list):
                yield (key + 'W:', ' '.join(map(str, self.data['value'][key])))
            else:
                yield (key + 'V:', str(self.data['value'][key]))

    def encode(self, id=None):
        datagram = ''
        if id:
            self.add_keyvalue('id', id)
        if not 'id' in self.data['data']:
            raise Exception("id missing");
        for key in self.data['data'].keys():
            datagram += key + ':' + str(self.data['data'][key]) + '\n'
        for key in self.data['status'].keys():
            datagram += key + 'S:' + str(self.data['status'][key]) + '\n'
        for key in self.data['value'].keys():
            if isinstance(self.data['value'][key], list):
                datagram += key + 'W:' + ' '.join(map(str, self.data['value'][key])) + '\n'
            else:
                datagram += key + 'V:' + str(self.data['value'][key]) + '\n'
        return datagram

    def decode(self, datagram):
        for line in datagram.splitlines():
            try:
                (key, val) = line.split(':')
            except:
                raise Exception('error in line: \"' + line + '\"')
            self.add_keyvalue(key, val)

    def __str__(self):
        return str(self.data)
