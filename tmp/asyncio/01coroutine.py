#!/usr/bin/env python
# coding=utf-8

def consumer():
    r = ''
    while True:
        # recive content form yield
        n = yield r
        # end when nothing to produce
        if not n:
            return
        print('[CONSUMER] Consuming %s...' % n)
        r = '200 OK'

def produce(c):
    # active c
    c.send(None)

    # produce num 0 - 5
    n = 0
    while n < 5:
        n = n + 1
        print('[PRODUCER] Producing %s...' % n)
        # send n for yield expr which c will capture
        r = c.send(n)
        print('[PRODUCER] Consumer return: %s' % r)
    c.close()

c = consumer()
# generator c

produce(c)

