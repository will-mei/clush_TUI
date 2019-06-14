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

# type target action data timestamp 
'''
TerminalTask
GroupTask
HostTask
msg
'''

import pickle 


# join all obj to a str list 
def _join(*args):
    return ' '.join(map(str, args))

# split a list with a given unit length
def _get_slice_list(_list, slice_size):
    return [_list[i:i + slice_size] for i in range(0, len(_list), slice_size)]

def _get_time_stamp():
    _time = time.time()
    _time_tx    = time.strftime("%Y/%m/%d-%H:%M:%S_", time.localtime(_time)) #20
    # microsecends info instead of random text  
    _float_tx   = hex(int( str(_time).split('.')[1] )).upper() #8
    return (_time_tx, _float_tx)

# get sum with an id info and a prefix 
def _get_sum(bin_data, bin_id, prefix=b'', _encoding='utf-8'):
    if isinstance(prefix, str):
        prefix = prefix.encode(_encoding)
    return hashlib.sha256(prefix + bin_data + bin_id).hexdigest() #64


###############################################################
# input -> obj/str (msg str/json str) -> pickle bin / encode bin
# -> [add] sum(hash) + id/timestamp + given tag -> pickle bin data 
# -> sliced list -> [fixed length] slice -> [add] seq bin + max bin + sum bin + slice bin
# -> send through socket/pipe
# done
###############################################################

class api_client():
    def __init__(self, con_info):
        # this value is the slice num max in hex; and it should be set the same as the server's
        self.hex_max    = 8
        self.sum_length = 64
        self._eof       = b'0'
        # connection info 
        self._prefix        = con_info['server_id']
        self._server_ip     = con_info['server_ip']
        self._server_port   = con_info['server_port']
        self._timeout       = con_info['socket_timeout']
        #self._mtu           = con_info['msg_trans_unit']
        #self._decode_cost   = len(hex(len(self.mtu)))
        self._len_max       = con_info['msg_trans_unit'] - self.hex_max*2 - 64 - len(self._eof) # (seq + max) + 64(256sum) + adjust status

    # format bin data into a formated pkg 
    def _mark_pkg(self, _data_bin, _tag=False):
        _bin_data   = _data_bin

        # generate an id for data  
        _time_stamp = _get_time_stamp()
        if _tag:
            _id     = _time_stamp[0] + _tag
        else:
            _id     = ''.join(_time_stamp)
        _bin_id     = _id.encode('utf-8')

        # hash with token & id & time
        _sum        = _get_sum(_bin_data, _bin_id, prefix=self._prefix) 
        _data_pkg   = {
            'sum':      _sum, #str 
            'bin_id':   _bin_id, #bytes 
            'bin_data': _bin_data, #bytes 
        }
        logging.debug(_join(
            'data info:',
            '\nsum:',       _sum,
            '\nbin_id:',    _bin_id,
            '\nbin_data:',  _bin_data,
        ))
        return _data_pkg

    def _deliver_pkg(self, _socket_obj, _data_pkg):
        # extra info length: 80 = 16 + 64
        index = 0
        if len(_data_pkg) > self._len_max:
            # split long messages
            _slice_list = _get_slice_list(_data_pkg, self._len_max)
            # seq max 
            _max        = hex(len(_slice_list) -1).encode('utf-8').rjust(self.hex_max, b'f')
            # send them one by one 
            for _slice in _slice_list:
                # seq info length: 16 if self.hex_max = 8
                # 16 = 8+8
                #    = seq nu + seq max
                    # nu = '0x' + '6' (ie, max 16G text msg)
                    # max = '0x' + '6'
                _seq    = hex(index).encode('utf-8').rjust(self.hex_max, b'f')
                # sum info length:64, use sha256 hash 
                _sum    = hashlib.sha256(_seq + _slice).hexdigest().encode('utf-8')

                # send 8 + 8 + 64 + sliced data 
# adjust EOF
                if _seq == _max:
                    _socket_obj.send( (_seq + _max + _sum + _slice + self._eof).ljust(self._len_max, b' '))
                else:
                    _socket_obj.send( _seq + _max + _sum + _slice + self._eof)
                # check
                reply   = _socket_obj.recv(self._len_max)
                if reply == _sum :
                    _status = 'success'
                else:
                    _status = 'failed'
                    # resend while transport failed
                    # pass 
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
            _slice  = _data_pkg 
            _seq    = hex(index).encode('utf-8').rjust(self.hex_max, b'f')
            _max    = hex(index).encode('utf-8').rjust(self.hex_max, b'f')
            _sum    = hashlib.sha256(_seq + _data_pkg).hexdigest().encode('utf-8')
            _socket_obj.send( (_seq + _max + _sum + _slice + self._eof).ljust(self._len_max, b' '))
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
        _socket_obj.send(b'f'* self.hex_max*2)

        # send formated data_pkg 
    def _send_bin_data(self, data_pkg):
        _socket     = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self._server_ip, self._server_port))

        try:
            self._deliver_pkg(_socket, data_pkg)
            # the server replies only confirm status info 
            reply   = _socket.recv(self._len_max).decode('utf-8')
        #except:
        #    print('send failed')
        finally:
            # close socket
            _socket.send(b'exit')
            _socket.close()
            logging.debug('connection closed')
        return reply 

    # format and send
    def send_data(self, data, form='data'):
        # Data serialization
        if form in ['json', 'msg']:
            # get json text or str encoded 
            data_bin    = data.encode('utf-8') 
        else :
            # use pickle to get the bin data of others 
            data_bin    = pickle.dumps(data)

        # add hash info
        _marked_pkg   = self._mark_pkg(data_bin, _tag=form)

        # packing and sending hashed data 
        data_pkg    = pickle.dumps(_marked_pkg)

        reply       = self._send_bin_data(data_pkg)
        if reply == _marked_pkg['sum']:
            logging.debug(_join(
                _data_pkg, 'send success'
            ))
        else:
            logging.debug(_join('reply:', reply))

    def send_msg(self, _msg_str):
        self.send_data(_msg_str, form='msg')


###############################################################
# form tag:
# msg : str
# json: json str
# data: pickle bin
###############################################################
if __name__ == "__main__":
    # define a connection 
    connection_info = {
        # an encoded token
        'server_id'     : b'test_user_id',
        'server_ip'     : '192.168.59.252',
        'server_port'   : 9999,
        'msg_trans_unit': 512,
        'socket_timeout': 5,
    }

    g = {
        'grp_name'      :'grp0',
        'grp_ssh_info'  :{
            'port'      :22,
            'user'      :None,
            'password'  :None,
            'timeout'   :15,
            'hostkey'   :'~/.ssh/id_rsa'
        },
        'grp_ip_array'  : {
            'host' + str(x) : '192.168.59.' + str(x) for x in range(10, 30)
        }
    }

    if len(sys.argv) > 1:
        _msg        = ' '.join(sys.argv[1:])
        s = api_client(connection_info)
        s.send_msg(_msg)
        exit(0)
    else:
        #_msg = '^^^^----____'*128
        s = api_client(connection_info)
        s.send_data(g)
        print('fakedata wree sent, you can type some string to send to remote server')


