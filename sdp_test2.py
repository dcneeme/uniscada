#!/usr/bin/python3
# naidis kontrollerile saatmiseks

from sdp import *

x2 = SDP()

d='BRS:2\nLVW:123 456 111\nLHV:123\nBTV:?\nLWW:?\nid:abc123123123\nin:9\n'
x2.decode(d) # d on sissetulnud teade udp

print(str(x2)) # uue instance debug
print
#print(str(x2.get_data()))


for (key, val) in x2.get_data_list():
    print("key: " + key + " val:" + str(val))

print()
