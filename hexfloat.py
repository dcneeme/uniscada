#!/usr/bin/python3
import sys
def floatfromhex(hex):
# 4000D3349FEBBEAE -> 2.10312771738 # lisa round()

    input_float = hex
    sign = int(input_float[0:2],16) & 128
    exponent = (int(input_float[0:3],16) & 2047)  - 1023
    if sign == 128:
        return float.fromhex('-0x1.'+input_float[3:16]+'p'+str(exponent))
    return float.fromhex('0x1.'+input_float[3:16]+'p'+str(exponent))



#print floatfromhex(sys.argv[1]) # see annab vea
#print(floatfromhex(sys.argv[1])) # see vist lisab \n
