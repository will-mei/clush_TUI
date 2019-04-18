#!/usr/bin/env python
# coding=utf-8

# python3 by default 

widths = [
  (126,  1), (159,  0), (687,   1), (710,  0), (711,  1),
  (727,  0), (733,  1), (879,   0), (1154, 1), (1161, 0),
  (4347,  1), (4447,  2), (7467,  1), (7521, 0), (8369, 1),
  (8426,  0), (9000,  1), (9002,  2), (11021, 1), (12350, 2),
  (12351, 1), (12438, 2), (12442,  0), (19893, 2), (19967, 1),
  (55203, 2), (63743, 1), (64106,  2), (65039, 1), (65059, 0),
  (65131, 2), (65279, 1), (65376,  2), (65500, 1), (65510, 2),
  (120831, 1), (262141, 2), (1114109, 1),
]
def get_width( o ):
    """Return the screen column width for unicode ordinal o."""
    global widths
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1
  
def get_char_width(ch):
    try:
        # python2
        _u_char = ch.decode('utf-8')
    except AttributeError:
        # python3
        _u_char = ch
    return get_width(ord(_u_char))
    
def get_str_width(tx):
    try:
        return sum(map(lambda x : get_width(ord(x)), tx))
    except:
        return sum(map(lambda x : get_width(ord(x.decode('utf-8'))), tx))

def printable_char(ch):
    if get_char_width(ch) == 0:
        return False
    else:
        return True

def get_printable(tx):
    return ''.join(filter(printable_char, tx))
    
# Generate an array of char and cursor cursor_position in relative 
def gen_tx_cursor_array(tx):
    # an array stores cursor_position for char of a string 
    _cursor_array = {}
    # key   : index of char in str 
    # value : cursor position 
    _relative_cursor_position = 0
    for i in range(len(tx)) :
        _cursor_array[i] = _relative_cursor_position 
        _cur_step = get_char_width(tx[i])
        _relative_cursor_position += _cur_step 
    return _cursor_array 

# don't use this class in new code !
class wide_str(str):
    def __add__(self, y):
        _tmp_str = str(self) + str(y)
        return zstr(_tmp_str)
    def __len__(self):
        # return the width of str not the count of char 
        return get_str_width(self)

