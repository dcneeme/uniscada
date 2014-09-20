import unittest

from sdp import *

class SDPTests(unittest.TestCase):
    '''
    This is the unittest for the uniscada.sdp module
    '''
    def setUp(self):
        self.sdp = SDP()

    def test_get_data_missing(self):
        self.assertEqual(self.sdp.get_data('AAS'), None)
        self.assertEqual(self.sdp.get_data('ABV'), None)
        self.assertEqual(self.sdp.get_data('id'), None)

    def test_add_keyvalue_status(self):
        ''' Test setting/getting key:val for Status '''
        self.sdp.add_keyvalue('AAS', 2)
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)
        self.assertEqual(self.sdp.get_data('AAs'), None)
        self.assertEqual(self.sdp.get_data('aaS'), None)

        self.sdp.add_keyvalue('ABS', '3')
        d = self.sdp.get_data('ABS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 3)
        self.assertEqual(self.sdp.get_data('ABs'), None)
        self.assertEqual(self.sdp.get_data('abS'), None)

        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ACS', 'a')
        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ADS', [1, 2])

    def test_add_status(self):
        ''' Test setting/getting Status key:val '''
        self.sdp.add_status('AA', 2)
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 2)
        self.assertEqual(self.sdp.get_data('AAs'), None)
        self.assertEqual(self.sdp.get_data('aaS'), None)

        self.assertRaises(Exception, self.sdp.add_status, 'AB', 'a')
        self.assertRaises(Exception, self.sdp.add_status, 'AC', [1, 2])

    def test_add_keyvalue_value(self):
        ''' Test setting/getting key:val for Value '''
        self.sdp.add_keyvalue('AAV', 1234)
        d = self.sdp.get_data('AAV')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1234)
        self.assertEqual(self.sdp.get_data('AAv'), None)
        self.assertEqual(self.sdp.get_data('aaV'), None)

        self.sdp.add_keyvalue('ABV', 1.5)
        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, float))
        self.assertEqual(d, 1.5)
        self.assertEqual(self.sdp.get_data('ABv'), None)
        self.assertEqual(self.sdp.get_data('abV'), None)

        self.sdp.add_keyvalue('ACV', 'abc')
        d = self.sdp.get_data('ACV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc')
        self.assertEqual(self.sdp.get_data('ACv'), None)
        self.assertEqual(self.sdp.get_data('acV'), None)

        self.sdp.add_keyvalue('ADV', 'cde xyz')
        d = self.sdp.get_data('ADV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'cde xyz')
        self.assertEqual(self.sdp.get_data('ADv'), None)
        self.assertEqual(self.sdp.get_data('adV'), None)

        self.sdp.add_keyvalue('AEV', '1 2 3.5')
        d = self.sdp.get_data('AEV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '1 2 3.5')
        self.assertEqual(self.sdp.get_data('AEv'), None)
        self.assertEqual(self.sdp.get_data('aeV'), None)

        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ADV', [1, 2])

    def test_add_keyvalue_values(self):
        ''' Test setting/getting key:val for List of Values '''
        self.sdp.add_keyvalue('AAW', '1')
        d = self.sdp.get_data('AAW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1])
        self.assertEqual(self.sdp.get_data('AAw'), None)
        self.assertEqual(self.sdp.get_data('aaW'), None)

        self.sdp.add_keyvalue('ABW', '1 2 3.5')
        d = self.sdp.get_data('ABW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, 2, 3.5])
        self.assertEqual(self.sdp.get_data('ABw'), None)
        self.assertEqual(self.sdp.get_data('abW'), None)

        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ACW', 1)
        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ADW', 1.5)
        self.assertRaises(Exception, self.sdp.add_keyvalue, 'AEW', 'a')

    def test_add_value(self):
        ''' Test setting/getting Value and List of Values key:val '''
        self.sdp.add_value('AA', 1234)
        d = self.sdp.get_data('AAV')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1234)
        self.assertEqual(self.sdp.get_data('AAv'), None)
        self.assertEqual(self.sdp.get_data('aaV'), None)
        self.assertEqual(self.sdp.get_data('AAS'), None)
        self.assertEqual(self.sdp.get_data('AAW'), None)

        self.sdp.add_value('AB', 1.5)
        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, float))
        self.assertEqual(d, 1.5)
        self.assertEqual(self.sdp.get_data('ABv'), None)
        self.assertEqual(self.sdp.get_data('abV'), None)
        self.assertEqual(self.sdp.get_data('ABS'), None)
        self.assertEqual(self.sdp.get_data('ABW'), None)

        self.sdp.add_value('AC', 'value')
        d = self.sdp.get_data('ACV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'value')
        self.assertEqual(self.sdp.get_data('ACv'), None)
        self.assertEqual(self.sdp.get_data('acV'), None)
        self.assertEqual(self.sdp.get_data('ACS'), None)
        self.assertEqual(self.sdp.get_data('ACW'), None)

        self.sdp.add_value('AD', [1])
        d = self.sdp.get_data('ADW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1])
        self.assertEqual(self.sdp.get_data('ADv'), None)
        self.assertEqual(self.sdp.get_data('adV'), None)
        self.assertEqual(self.sdp.get_data('ADS'), None)
        self.assertEqual(self.sdp.get_data('ADV'), None)

        self.sdp.add_value('AE', [1, 2, 3])
        d = self.sdp.get_data('AEW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, 2, 3])
        self.assertEqual(self.sdp.get_data('AEv'), None)
        self.assertEqual(self.sdp.get_data('aeV'), None)
        self.assertEqual(self.sdp.get_data('ADS'), None)
        self.assertEqual(self.sdp.get_data('ADV'), None)


    def test_add_keyvalue_data(self):
        ''' Test setting/getting key:val for Other Data '''
        self.sdp.add_keyvalue('aa', '123abc')
        d = self.sdp.get_data('aa')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '123abc')
        self.assertEqual(self.sdp.get_data('AA'), None)
        self.assertEqual(self.sdp.get_data('a'), None)
        self.assertEqual(self.sdp.get_data('aaa'), None)

        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ab', 1)
        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ac', 1.5)
        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ad', [1, 2])

    def test_add_keyvalue_request_data(self):
        ''' Test setting/getting key:val where val == '?' '''
        self.sdp.add_keyvalue('AAS', '?')
        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')
        self.assertEqual(self.sdp.get_data('AAs'), None)
        self.assertEqual(self.sdp.get_data('aaS'), None)

        self.sdp.add_keyvalue('ABV', '?')
        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')
        self.assertEqual(self.sdp.get_data('ABv'), None)
        self.assertEqual(self.sdp.get_data('abV'), None)

        self.sdp.add_keyvalue('ACW', '?')
        d = self.sdp.get_data('ACW')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')
        self.assertEqual(self.sdp.get_data('ACw'), None)
        self.assertEqual(self.sdp.get_data('acW'), None)

    def test_add_keyvalue_values(self):
        ''' Test setting/getting key:val for List of Values '''
        self.sdp.add_keyvalue('AAW', '1')
        d = self.sdp.get_data('AAW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1])
        self.assertEqual(self.sdp.get_data('AAw'), None)
        self.assertEqual(self.sdp.get_data('aaW'), None)

        self.sdp.add_keyvalue('ABW', '1 2 35')
        d = self.sdp.get_data('ABW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [1, 2, 35])
        self.assertEqual(self.sdp.get_data('ABw'), None)
        self.assertEqual(self.sdp.get_data('abW'), None)

        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ACW', 1)
        self.assertRaises(Exception, self.sdp.add_keyvalue, 'ADW', 1.5)
        self.assertRaises(Exception, self.sdp.add_keyvalue, 'AEW', 'a')
        self.assertRaises(Exception, self.sdp.add_keyvalue, 'AFW', '1.5 2.2')

    def test_encode_with_id(self):
        ''' Test encoder for full packet'''
        self.sdp.add_keyvalue('id', 'abc123')
        self.sdp.add_keyvalue('ip', '10.0.0.10')
        self.sdp.add_keyvalue('AAS', 1)
        self.sdp.add_keyvalue('ABV', 2)
        self.sdp.add_keyvalue('ACV', 3.5)
        self.sdp.add_keyvalue('ADV', '4')
        self.sdp.add_keyvalue('AEV', '5.5')
        self.sdp.add_keyvalue('AFV', 'abc')
        self.sdp.add_keyvalue('AGW', '4')
        self.sdp.add_keyvalue('AHW', '5 6 75')
        self.sdp.add_keyvalue('AIS', '?')
        self.sdp.add_keyvalue('AJV', '?')
        self.sdp.add_keyvalue('AKW', '?')
        self.sdp.add_keyvalue('iq', '?')
        datagram = self.sdp.encode()
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(sorted(datagram.splitlines()), [
            'AAS:1',
            'ABV:2',
            'ACV:3.5',
            'ADV:4',
            'AEV:5.5',
            'AFV:abc',
            'AGW:4',
            'AHW:5 6 75',
            'AIS:?',
            'AJV:?',
            'AKW:?',
            'id:abc123',
            'ip:10.0.0.10',
            'iq:?',
        ])

    def test_encode_with_id_param(self):
        ''' Test encoder with id for full packet'''
        self.sdp.add_keyvalue('id', 'abc123')
        self.sdp.add_keyvalue('ip', '10.0.0.10')
        self.sdp.add_keyvalue('AAS', 1)
        self.sdp.add_keyvalue('ABV', 2)
        self.sdp.add_keyvalue('ACV', 3.5)
        self.sdp.add_keyvalue('ADV', '4')
        self.sdp.add_keyvalue('AEV', '5.5')
        self.sdp.add_keyvalue('AFV', 'abc')
        self.sdp.add_keyvalue('AGW', '4')
        self.sdp.add_keyvalue('AHW', '5 6 75')
        self.sdp.add_keyvalue('AIS', '?')
        self.sdp.add_keyvalue('AJV', '?')
        self.sdp.add_keyvalue('AKW', '?')
        self.sdp.add_keyvalue('iq', '?')
        datagram = self.sdp.encode(id = 'def456')
        self.assertTrue(isinstance(datagram, str))
        self.assertEqual(sorted(datagram.splitlines()), [
            'AAS:1',
            'ABV:2',
            'ACV:3.5',
            'ADV:4',
            'AEV:5.5',
            'AFV:abc',
            'AGW:4',
            'AHW:5 6 75',
            'AIS:?',
            'AJV:?',
            'AKW:?',
            'id:def456',
            'ip:10.0.0.10',
            'iq:?',
        ])

    def test_encode_without_id(self):
        ''' Test encoder without id'''
        self.assertRaises(Exception, self.sdp.encode)

    def test_decode_valid(self):
        ''' Test decoder with valid datagram '''
        self.sdp.decode('id:abc123\nAAS:1\nABV:2\nACV:3.5\nADV:4\nAEV:5.5\nAFV:abc\nAGW:4\nAHW:5 6 75\nAIS:?\nAJV:?\nAKW:?\niq:?\nip:10.0.0.10\n')

        d = self.sdp.get_data('id')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc123')

        d = self.sdp.get_data('ip')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '10.0.0.10')

        d = self.sdp.get_data('AAS')
        self.assertTrue(isinstance(d, int))
        self.assertEqual(d, 1)

        d = self.sdp.get_data('ABV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '2')

        d = self.sdp.get_data('ACV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '3.5')

        d = self.sdp.get_data('ADV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '4')

        d = self.sdp.get_data('AEV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '5.5')

        d = self.sdp.get_data('AFV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, 'abc')

        d = self.sdp.get_data('AGW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [4])

        d = self.sdp.get_data('AHW')
        self.assertTrue(isinstance(d, list))
        self.assertEqual(d, [5, 6, 75])

        d = self.sdp.get_data('AIS')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = self.sdp.get_data('AJV')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = self.sdp.get_data('AKW')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

        d = self.sdp.get_data('iq')
        self.assertTrue(isinstance(d, str))
        self.assertEqual(d, '?')

    def test_decode_invalid(self):
        ''' Test decoder with invalid datagram '''
        self.assertRaises(Exception, self.sdp.decode, '')
        self.assertRaises(Exception, self.sdp.decode, '\n')
        self.assertRaises(Exception, self.sdp.decode, 'id:abc\n\n')
        self.assertRaises(Exception, self.sdp.decode, 'id:abc\n\nAAS:1')
        self.assertRaises(Exception, self.sdp.decode, 'id:abc\nABC')
        self.assertRaises(Exception, self.sdp.decode, '\nid:abc')
        self.assertRaises(Exception, self.sdp.decode, 'id:abc\nABS:abc')
        self.assertRaises(Exception, self.sdp.decode, 'id:abc\nACW:123 bcd')
        self.assertRaises(Exception, self.sdp.decode, 'id:abc\nADW:1.0 2.2')
        self.assertRaises(Exception, self.sdp.decode, 'id:abc\nxyz:123 : 456')
