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
            if not isinstance(val, int) and \
               not isinstance(val, float) and \
               not isinstance(val, str):
                raise Exception('Value _MUST_BE_ str, int or float type')
            self.add_value(key[:-1], val)
        elif key[-1] == 'W':
            if not isinstance(val, str):
                raise Exception('List of Values _MUST_BE_ string of numbers')
            self.add_value(key[:-1], list(map(float, val.split(' '))))
        else:
            if not isinstance(val, str):
                raise Exception('Data _MUST_BE_ string')
            self.data['data'][key] = val

    def add_status(self, key, val):
        if not isinstance(val, int):
            raise Exception('Status _MUST_BE_ int type')
        self.data['status'][key] = int(val)

    def add_value(self, key, val):
        if not isinstance(val, int) and \
           not isinstance(val, float) and \
           not isinstance(val, str) and \
           not isinstance(val, list):
            raise Exception('Value _MUST_BE_ str, int, float or list type')
        self.data['value'][key] = val

    def get_data(self, key):
        if key[-1] == 'S':
            return self.data['status'].get(key[:-1], None)
        elif key[-1] == 'V':
            val = self.data['value'].get(key[:-1], None)
            if isinstance(val, list):
                return None
            return val
        elif key[-1] == 'W':
            val = self.data['value'].get(key[:-1], None)
            if isinstance(val, list):
                return val
            return None
        else:
            return self.data['data'].get(key, None)

    def get_data_list(self):
        for key in self.data['status'].keys():
            yield (key + 'S:', str(self.data['status'][key]))
        for key in self.data['value'].keys():
            if isinstance(self.data['value'][key], list):
                yield (key + 'W:', ' '.join(map(str, self.data['value'][key])))
            else:
                yield (key + 'V:', str(self.data['value'][key]))
        for key in self.data['data'].keys():
            yield (key, str(self.data['data'][key]))

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
        if self.get_data('id') is None:
            raise Exception('id: _MUST_ exists in datagram')

    def __str__(self):
        return str(self.data)
