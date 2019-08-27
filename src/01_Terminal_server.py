#!/usr/bin/env python
# coding=utf-8

import lib_terminal



# communicate wiht other app 
# here defines what you can do to a group 
class ClusterTerminal(api_server):

    def create(self):
        self._groups  = {}

    def parse_call(self, _data):
        if _data['tag'] == 'msg':
            self.parse_msg(_data['data'])
        else:
            self.perform_task(_data)

    def perform_task(self, _data):
        print('call with tag:', _data['tag'])
        print('data content:', _data['data'])

    def parse_msg(self, _msg):
        print('recived msg:', _msg)

    # run command list on all groups 
    def brodcast_cmd(self, cmd_list):
        print('broadcast cmd:', cmd_list)

#    def __contains__(self, grp_name):
#        return self.has_grp(grp_name)
#    def has_key(self, grp_name):
#        return self.has_grp(grp_name)
#    def has_grp(self, grp_name):
#        return self._host_group_array.__contains__(grp_name)
#
    def __getitem__(self):
        pass

    def __delitem__(self):
        # close all connections on that group
        map(lambda con : con.close(), self._groups[key].connections())
        # remove name and info
        del self._groups[key]

#    def __len__(self):
#        pass

    # key: grp_name
    # value: grp_connections
#    def __setitem__(self, grp, grp_con):
#        self._host_group_array[grp] = grp_con
#        pass

#    def __str__(self):
#        return list(map(lambda grp : grp.name, self.con_groups))
#        pass

#    def clear(self):
#        map(lambda con_grp : con_grp.close(self.name), self.con_groups)
#        self._host_group_array.clear()

#    def items(self):
#        pass
#
#    def keys(self):
#        return self.groups()
#    def groups(self):
#        pass
#
#    def pop(self):
#        pass
#
#    def popitem(self):
#        pass
#
#    def setdefault(self):
#        pass

#    def update(self):
#    def update_connection(self):
#        pass 
#    def values(self):
#        return self.connections()
#    def connections(self):
#        pass

if __name__ == "__main__":

    # one server 
    server_info = {
        'server_id'     :b'test_user_id',
        'server_ip'     :'192.168.59.102',
        'server_port'   :9999,
        'msg_trans_unit':512,
        'connection_max':32,
        'socket_timeout':5,
        'msg_timeout'   :15,
    }

    ## one group 
    #group_info  = {
    #    'grp_name':'grp0',
    #    'grp_ssh_info':{
    #        'port':22,
    #        'user':None,
    #        'password':None,
    #        'timeout':15,
    #        'hostkey':'~/.ssh/id_rsa'
    #    },
    #    'grp_ip_array': {'host' + str(x) : '192.168.59.' + str(x) for x in range(10, 130)}
    #}

    server1     = ClusterTerminal(server_info)
    #server1.add_grp(group_info)
    server1.run_forever()


test_server()

