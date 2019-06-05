#!/usr/bin/env python
# coding=utf-8
import socket

import sys 
import json
import time
import hashlib
#import string
#import random

import logging 
logging.basicConfig(
    #filename= '/var/log/messages',
    filename= '../log/client_socket.log',
    #level   = logging.INFO,
    level   = logging.DEBUG,
    format  = '%(asctime)s %(name)s %(process)d - %(thread)d:%(threadName)s - %(levelname)s - %(pathname)s %(funcName)s line: %(lineno)d - %(message)s',
    datefmt = '%Y/%m/%d %I:%M:%S %p'
)

def _join(*args):
    return ' '.join(map(str, args))


def _get_slice_list(_list, slice_size):
    return [_list[i:i + slice_size] for i in range(0, len(_list), slice_size)]

def _get_time_stamp(_tag=None):
    _time = time.time()
    _time_tx    = time.strftime("%Y/%m/%d-%H:%M:%S_", time.localtime(_time))
    #_rand_tx    = ''.join(random.sample([chr(i) for i in range(65,91)], 5))
    #_rand_tx    = ''.join(random.sample(string.ascii_letters, 5))  
    # microsecends info instead of random text  
    if _tag:
        return _time_tx + _tag 
    else:
        _float_tx   = hex(int( str(_time).split('.')[1] )).upper()
        return _time_tx + _float_tx
# len timestamp 27

def _get_sum(msg_tx, tid_tx, prefix=b'', _encoding='utf-8'):
    _msg = msg_tx.encode(_encoding)
    _tid = tid_tx.encode(_encoding)
    if isinstance(prefix, str):
        prefix = prefix.encode(_encoding)
    return hashlib.sha256(prefix + _msg + _tid).hexdigest()
# len summary   64


###############################################################

class api_client():
    def __init__(self, con_info):
        # connection info 
        self._prefix     = con_info['server_id']
        self._server_ip  = con_info['server_ip']
        self._server_port= con_info['server_port']
        self._timeout    = con_info['socket_timeout']
        self._len_max    = con_info['msg_trans_unit'] - 80

    def _format_msg(self, _msg):
        # task id
        _tid        = _get_time_stamp()
        # hash with token & time
        _sum        = _get_sum(_msg, _tid, prefix=self._prefix) 
        # head 64+27+9 = 100
        _data   = {'sum': _sum, #64
                   'tid': _tid, #27
                   'msg': _msg,
                  }
        logging.debug(_join(
            'msg info:',
            '\nsum:', _sum,
            '\ntid:', _tid,
            '\nmsg:', _msg,
        ))
        return _data

    def _send_pkg(self, _socket_obj, _data_pkg):
        # extra info length: 80 = 16 + 64
        index = 0
        if len(_data_pkg) > self._len_max:
            # split long messages
            _slice_list = _get_slice_list(_data_pkg, self._len_max)
            _max        = hex(len(_slice_list) -1).encode('utf-8').rjust(8, b'f')
            for _slice in _slice_list:
                # seq 16, 16 = 8+8 = nu + max
                # nu = '0x' + '6' (max 16G text)
                # max = '0x' + '6'
                _seq    = hex(index).encode('utf-8').rjust(8, b'f')
                # sum 64, use sha256 hash 
                _sum    = hashlib.sha256(_seq + _slice).hexdigest().encode('utf-8')
                # send 
                _socket_obj.send( _seq + _max + _sum + _slice)
                reply   = _socket_obj.recv(self._len_max)
                if reply == _sum :
                    _status = 'success'
                else:
                    _status = 'failed'
                logging.warn(_join(
                    'slice info:',
                    '\nslice seq:', _seq, len(_seq),
                    '\nslice max:', _max, len(_max),
                    '\nslice sum:', _sum, len(_sum),
                    '\nslice content:', _slice, len(_slice),
                    '\nslice status:', _status,
                ))
                index = index + 1
        else:
            _slice  = _data_pkg.ljust(self._len_max - 80, b' ') 
            _seq    = hex(index).encode('utf-8').rjust(8, b'f')
            _max    = hex(index).encode('utf-8').rjust(8, b'f')
            _sum    = hashlib.sha256(_seq + _data_pkg).hexdigest().encode('utf-8')
            _socket_obj.send( _seq + _max + _sum + _slice)
            reply   = _socket_obj.recv(self._len_max)
            if reply == _sum :
                _status = 'success'
            else:
                _status = 'failed'
            logging.warn(_join(
                'slice info:',
                '\nslice seq:', _seq, len(_seq),
                '\nslice max:', _max, len(_max),
                '\nslice sum:', _sum, len(_sum),
                '\nslice content:', _data_pkg, len(_data_pkg),
                '\nslice status:', _status,
            ))

        # confirm data transport stop
        _socket_obj.send(b'f'*16)

    def _send_msg(self, _msg):
        _socket     = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self._server_ip, self._server_port))
        # welcome
        #print(_socket.recv(_len_max).decode('utf-8'))

        _data_pkg   = self._format_msg(_msg)
        data_pkg    = json.dumps(_data_pkg).encode('utf-8')
        try:
            self._send_pkg(_socket, data_pkg)
            # the serer replies only confirm status info 
            reply   = _socket.recv(self._len_max).decode('utf-8')
            if reply == _data_pkg['sum']:
                logging.debug(_join(
                    _data_pkg, 'send success'
                ))
            else:
                logging.debug(_join('reply:', reply))
        #except:
        #    print('send failed')
        finally:
            # close socket
            _socket.send(b'exit')
            _socket.close()
            logging.debug('connection closed')

if __name__ == "__main__":
    # define a connection 
    connection_info = {
        # an encoded token
        'server_id'     : b'test_user_id',
        'server_ip'       : '192.168.59.252',
        'server_port'     : 9999,
        'msg_trans_unit'  : 512,
        'socket_timeout'  : 5,
    }

    if len(sys.argv) > 1:
        _msg        = ' '.join(sys.argv[1:])
        s = api_client(connection_info)
        s._send_msg(_msg)
        exit(0)
    else:
        _msg = '^^^^----____'*128
        s = api_client(connection_info)
        s._send_msg(_msg)
        print('nothing to send, you can type some string to send to remote server')


