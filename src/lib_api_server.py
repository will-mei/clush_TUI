#!/usr/bin/env python
# coding=utf-8
import socket
import time
import threading 

import json
import hashlib

import logging 
logging.basicConfig(
    #filename= '/var/log/messages',
    filename= '../log/server_socket.log',
    #level   = logging.INFO,
    level   = logging.DEBUG,
    format  = '%(asctime)s %(name)s %(process)d - %(thread)d:%(threadName)s - %(levelname)s - %(pathname)s %(funcName)s line: %(lineno)d - %(message)s',
    datefmt = '%Y/%m/%d %I:%M:%S %p'
)

import pickle

def _join(*args):
    return ' '.join(map(str, args))

#return_code = {
#    000:'success',
#    001:'failed',
#    002:'hash fail',
#    003:'data incomplete',
#    004:'data incorrect',
#    005:'pkg format error',
#    006:'pkg hash failed',
#    007:'msg out of date',
#    008:'broken pipe'
#    009:'server failure',
#    010:'client unreachable',
#}


class api_server():
    def __init__(self, con_info):
        self.hex_max    = 8
        self.sum_length = 64
        self._prefix        = con_info['server_id']
        self._server_ip     = con_info['server_ip']
        self._server_port   = con_info['server_port']
        self._timeout       = con_info['socket_timeout']
        self._mtimeout      = con_info['msg_timeout']
        self._len_max       = con_info['msg_trans_unit']
        self._con_max       = con_info['connection_max']
        # create a socket
        self._socket        = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(
            (self._server_ip, 
             self._server_port)
        )
        self._socket.listen(self._con_max)
        self.status         = 'on'
        logging.debug(_join(
                self._server_ip, self._server_port, "waiting for connection .."
            ))
        self.create()

    # subclass
    def create(self):
        pass

    def parse_call(self, _final_pkg):
        pass 

    #def perform_task(self, _data):
    #    pass 

    def _check_msg(self, _stream_bytes):
        logging.debug(_join(b'try to load data form pkg:',  _stream_bytes))
        try:
            _data   = pickle.loads(_stream_bytes)
            _stat   = True
            logging.debug('data loading success')
        except:
            _data   = None
            _stat   = False 
            logging.warn('data pkg format abnormal, load failed')
        return (_data, _stat)

    def parse_client_data(self, _data):
        # parse msg format 
        try:
            _sum        = _data['sum']
            _bin_id     = _data['bin_id']
            _bin_data   = _data['bin_data']
            # 
            _time_stamp = _bin_id.split(b'_')[0]
            _form_tag   = _bin_id.split(b'_')[1]
            _sent_time  = time.mktime(time.strptime(_time_stamp.decode('utf-8'), "%Y/%m/%d-%H:%M:%S")) 
            logging.debug(_join(
                'data info:',
                '\ndata sum:',      _sum,
                '\ndata id:',       _bin_id,
                '\ndata tag:',      _form_tag,
                '\ndata sent time:',_time_stamp,
                '\ndata content:',  _bin_data,
            ))
        except:
            logging.warn(_join(b'fail to parse msg content:', _data))
            reply   = b'info status: wrong format, droped'
            return reply

        # msg timeout
        _time_now = time.time()
        if _time_now - _sent_time > self._mtimeout:
            reply   = ('task %s recived and abandent, cause the timestamp is out of date' % _tid).encode('utf-8')
            logging.debug(_join('reply:', reply))
            return reply

        # task_id existence status check (sqlite)

        # hash validation
        _sum_confirm = hashlib.sha256(self._prefix + _bin_data + _bin_id).hexdigest()
        if _sum_confirm == _sum:
            # reply 
            reply   = ('data %s  recived and confirmed' % _bin_id.decode('utf-8')).encode('utf-8')
            logging.info(_join('reply:', reply))

            # add tag into data and exec task 
            _data['id']         = _data['bin_id'].decode('utf-8')
            _tag = _data['tag'] = _form_tag.decode('utf-8') 
            if _tag in ['msg', 'json']:
                _data['data']   = _data['bin_data'].decode('utf-8')
            else:
                _data['data']   = pickle.loads(_data['bin_data'])
            self.parse_call(_data)
            #self.perform_task(_data)
        else:
            reply   = ('task %s hash failed, task invalid' % _bin_id.decode('utf-8')).encode('utf-8')
            logging.warn(_join(
                'hash info:',
                '\nprefix:',        self._prefix,
                '\ndata id:',       _bin_id,
                '\nsum origin:',    _sum,
                '\nsum confirm:',   _sum_confirm,
                '\ndat content:',   _bin_data,
            ))
            logging.debug(_join('reply:', reply))

        return reply

    def thread_tcplink(self, sock, addr):
        # welcome
        logging.debug("Accept new connection from %s:%s..." % addr)

        #sock.send(b'Welcom!')
        _slice_dict = {}
        _slice_max  = hex(0)
        while True:
            _stream_bytes = sock.recv(self._len_max)
            time.sleep(0)
            
            # end and exit 
            if not _stream_bytes or _stream_bytes == b'exit':
                break
            #sock.send(('Hello,%s!' % _stream_bytes.decode('utf-8')).encode('utf-8'))

            # confirmed stop 
            if _stream_bytes == b'f'* self.hex_max*2:
                logging.debug(_join('confirm stop reciving slices:\n', 'seq_max:', _slice_max))
                # check every slice of data pkg 
                i = 0 
                _data_pkg = b''
                # check and splicing sequnces, seq num base 16
                while i <= int(_slice_max.lstrip(b'f'), 16):
                    logging.debug('check slice num %s' % i)
                    try:
                        _data_pkg += _slice_dict[i]
                    except:
                        logging.debug('slice number %s is missing, Retransmission error!' % i)
                        _data_pkg = None
                        break
                    i = i+1

                # check msg and confirm
                _client_data_info = self._check_msg(_data_pkg) # pkg content, stat 
                _client_data_pkg  = _client_data_info[0]
                _client_data_stat = _client_data_info[1]
                if _client_data_stat:
                    logging.debug(_join('the complete msg data:\n', _client_data_pkg))
                    # reply transportation result info to client 
                    reply = self.parse_client_data(_client_data_pkg)
                    sock.send(reply)
                else:
                    sock.send(b'data incorrect,  transportation failed')

            # continue recive the rest 
            else:
                _seq    = _stream_bytes[:self.hex_max]
                _max    = _stream_bytes[self.hex_max:self.hex_max*2]
                _sum    = _stream_bytes[self.hex_max*2:(self.hex_max*2+self.sum_length)]
                if _seq == _max:
                    _slice  = _stream_bytes[(self.hex_max*2+self.sum_length):self._len_max].rstrip()[:-1]
                else:
                    _slice  = _stream_bytes[(self.hex_max*2+self.sum_length):self._len_max][:-1]

                # hash result 
                _sum_confirm  = hashlib.sha256(_seq + _slice).hexdigest().encode('utf-8')
                logging.debug(_join(
                    'recived slice info:'
                    '\nslice seq num:', str(_seq),
                    '\nslice seq max:', str(_max),
                    '\nslice sum origin:', str(_sum),
                    '\nslice sum confirm:', str(_sum_confirm),
                    '\nslice content:', str(_slice),
                ))
                # check individual data package
                if _sum_confirm == _sum :
                    _slice_max = _max
                    index = int(_seq.lstrip(b'f'), self.hex_max*2)
                    if not index in _slice_dict:
                        logging.debug('store slice data num %s to buffer dict:\n' % index)
                        _slice_dict[index] = _slice
                        logging.debug(_join('buffer dict:\n', _slice_dict))
                    # confirm
                    sock.send(_sum)
                else:
                    # send return code error for checking sum info failed
                    sock.send(b'01') 
        # end 
        sock.close()
        logging.debug('Connection from %s:%s closed.' % addr)

    def run_forever(self):
        #i = 0
        #while i<2 :
        while self.status == 'on':
            sock, addr = self._socket.accept()
            task = threading.Thread(target=self.thread_tcplink, args=(sock, addr))
            task.start()
            #i = i+1
            #print('socket number:', i)
            #time.sleep(0.5)

    def close(self):
        self.status = 'off'
        pass

if __name__ == "__main__":
    server_info = {
        'server_id'     :b'test_user_id',
        'server_ip'     :'192.168.59.252',
        'server_port'   :9999,
        'msg_trans_unit':512,
        'connection_max':32,
        'socket_timeout':5,
        'msg_timeout'   :15,
    }
    s   = api_server(server_info)
    s.run_forever()


