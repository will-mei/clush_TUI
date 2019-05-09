#!/usr/bin/env python
# coding=utf-8

import paramiko
import threading

# transport
class GroupConectionDock(obj):
    # all hosts in a same group share the same login user and ssh port 
    def __init__(self, autoadd=True, port=22, username='root', host_list=[]):
        if host_list:
            map(self.docking(hostname), host_list)

    # check the accessablility of a host, like a quarantine 
    def inspect(self, hostname):
        pass 

    # add a new online host to connection pool 
    def docking(self, hostname):
        if self.inspect(hostnames):
            pass 

    # close the connection of a online host, but it's still in the host list 
    def cut_off(self, hostname):
        pass

    # drive out a offline host, remove form host_list 
    def expel(self, hostname):
        self.cut_off(hostname)
        pass

    @property 
    def online_hosts(self):
        return self._online_hosts
    @online_hosts.setter
    def online_hosts(self):
        try:
            _self._online_hosts.append(hostname)
            pass 

    # load command and put to threading pool 
    def load_cmd(self, cmd_list):
        #self.init_fleet()
        pass 

    # the output can be updated by any host in this group 
    def update_output(self):
        pass 


if __name__ == "__main__":
    pass 
