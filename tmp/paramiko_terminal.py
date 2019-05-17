#!/usr/bin/env python
# coding=utf-8


from wsgiref.simple_server import make_server


def paramiko_terminal(environ, start_response):
    #
    #setup_testing_defaults(environ)
    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    ret = [("%s: %s\n" % (key, value)).encode("utf-8") for key, value in environ.items()]
    return ret

with make_server('', 60000, paramiko_terminal) as httpd:
    print("Serving on port 60000...")
    httpd.serve_forever()
