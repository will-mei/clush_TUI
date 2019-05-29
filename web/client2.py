#!/usr/bin/env python
# coding=utf-8
import socket

import sys 
import json
import time
import hashlib
#import string
#import random


connection_info = {
    # an encoded token
    'session_key'     : b'test_user_id',
    # the serer replies only task id and confirm status info 
    'server_ip'       : '192.168.59.252',
    'server_port'     : 9999,
    'msg_trans_unit'  : 8192,
    'socket_timeout'  : 5,
}


def _get_slice_list(_list, slice_size):
    return [_list[i:i + slice_size] for i in range(0, len(_list), slice_size)]

def _get_time_stamp():
    _time = time.time()
    _time_tx    = time.strftime("%Y/%m/%d-%H:%M:%S_", time.localtime(_time))
    #_rand_tx    = ''.join(random.sample([chr(i) for i in range(65,91)], 5))
    #_rand_tx    = ''.join(random.sample(string.ascii_letters, 5))  
    # microsecends info instead of random text  
    _float_tx   = hex(int( str(_time).split('.')[1] )).upper()
    return _time_tx + _float_tx  # len timestamp 27

def _get_sum(prefix='', msg_tx, _encoding='utf-8'):
    if isinstance(prefix, str):
        _content = (prefix 
                    + msg_tx + _get_time_stamp()).encode(_encoding)
    elif isinstance(prefix, bytes):
        _content = (prefix.decode(_encoding) 
                    + msg_tx + _get_time_stamp()).encode(_encoding)
    return hashlib.sha256(_content).hexdigest()


###############################################################

def _send_msg(con_info, _msg, _seq_nu=None, _socket_obj=None ):
    _prefix     = con_info['session_key']
    _server_ip  = con_info['server_ip']
    _server_port= con_info['server_port']
    _timeout    = con_info['socket_timeout']
    _len_max    = con_info['msg_trans_unit']

    if _socket_obj:
        _socket = _socket_obj
    else:
        _socket     = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((server_ip, server_port))

    # welcome
    print(_socket.recv(_len_max).decode('utf-8'))

    # task id
    _tid        = _get_time_stamp()

    # hash with token & time
    _sum        = _get_sum(prefix=_prefix, _msg) 

    # format message / slice
    if _seq_nu:
        _data = {
            #
            'seq_nu': _seq_nu,

        }



    else:
        _data   = {'sum': _sum,
                   'msg': _msg,
                   'tid': _tid,
                  }
    _data_pkg   = json.dumps(_data).encode('utf-8')

    # slice and make header
    _size       = len(_data_pkg)
    # extra info length: 124 (not json indent)
    if _size > _len_max - 124:
        _slice_list = _get_slice_list(_msg)
        index = 0
        for _slice in _slice_list:
            _send_msg(con_info, _slice, _socket_obj=_socket, _seq_nu=index)
            index = index + 1
    else:
    # send msg 
        _socket.send(pkg)
    print(_socket.recv(_len_max).decode('utf-8'))

    # close socket 
    _socket.send(b'exit')
    _socket.close()


if sys.argv[1]:
    _msg        = ' '.join(sys.argv[1:])
    _send_msg(connection_info, _msg)
    exit(0)
else:
    print('nothing to send, you can type some string to send to remote server')


