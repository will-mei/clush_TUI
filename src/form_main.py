import os
import time
import curses
import configparser
from datetime import timedelta

from src import npyscreen as npyscreen
from src import box_grouptree
from src import box_messages
from src import box_status
from src import box_input
from src import lib_cli_bash
from src import lib_ssh_paramiko

import sqlite3

terminal_db = './db/terminal.db'

# just some example test ip list
#ip_list1 = [ '192.168.100.' + str(x)  for x in range(201, 206)]
#ip_list2 = [ '192.168.100.' + str(x)  for x in range(206, 211)]
#ip_list3 = [ '192.168.59.11' ]
#host_key = '~/.ssh/id_rsa'
#_ssh_info1 = {
#            'prot':     10000,
#            'user':     'secure',
#            'password': None,
#            'timeout':  30,
#            'hostkey':  host_key
#        }
#_ssh_info2 = {
#            'port':     22,
#            'user':     None,
#            'password': None,
#            'timeout':  10,
#            'hostkey': host_key,
#}

class MainForm(npyscreen.FormBaseNewWithMenus):

    @property
    def shell_mode(self):
        return self._shell_mode
    
    @shell_mode.setter
    def shell_mode(self, mode):
        if mode in ['local', 'cluster']:
            self._shell_mode = mode 
        else:
            raise ValueError("shell_mode could only be a str 'local' or 'cluster'")

    def __init__(self, parentApp, *args, **keywords):
        super(MainForm, self).__init__(*args, **keywords)
        #super().__init__(*args, **keywords)
        self.menu_advert_text = ': Ctrl + x 打开菜单, q 退出菜单 '
        self.initialize_menus()

    #def draw_form(self):
    #    super(npyscreen.FormBaseNewWithMenus, self).draw_form()
    #    super().draw_form()
    #    menu_advert = " " + self.__class__.MENU_KEY + ': 使用 Ctrl + x 打开管理菜单 '
    #    if isinstance(menu_advert, bytes):
    #        menu_advert = menu_advert.decode('utf-8', 'replace')
    #    y, x = self.display_menu_advert_at()
    #    self.add_line(y, x, 
    #        menu_advert, 
    #        self.make_attributes_list(menu_advert, curses.A_NORMAL),
    #        self.columns - x - 1
    #        )

    def create(self):
        self.name = '集群作业管理器(TUI)'
        self.shell_mode = 'local'
        # menus 
        self.main_menu = self.new_menu(name='主菜单:')
        self.main_menu.addItemsFromList([
            ('切换命令行模式',          self.switch_cli_mode,   "^N"),
            ('发起IO测试(添加中)',      self.launch_IO_test,    "^I"),
            ('开启任务流(添加中)',      self.turn_on_taskflow,  "^R"),
            ('管理任务流(添加中)',      self.manage_taskflow,   "^M"),
            ('添加 新任务',             self.add_task,          "^A"),
            ('添加 新主机(组)',         self.add_group,         "^G"),
            ('删除 选中主机组',         self.del_group,             ),
            ('部署 ceph集群',           self.deploy_ceph,       "^D"),
            ('配置 ceph集群(不可用)',   self.config_ceph,       "^O"),
            ('销毁 ceph集群(不可用)',   self.purge_ceph,        "^P"),
            ('帮助',                    self.show_help,         "^H"),
            ('退出',                    self.exit_func,         "^Q"),
        ])
        # Events

        # import config settings
        config = configparser.ConfigParser()
        # load and parse config 
        msg_buffer = 5000

        # window size
        y, x = self.useable_space()

        # create ui form
        ny = self.nextrely
        nx = self.nextrelx
        self.GroupTreeBoxObj = self.add(
            box_grouptree.HostGroupTreeBox,
            name="主机组",
            max_width=28,
            scroll_exit=False) #, value=0, relx=1, max_width=x // 5, rely=2,

        # top , 28 right 
        self.nextrely = ny
        self.nextrelx = nx + 28
        x_half = int((x - 28) / 2 -5)
        self.taskflowInfoBoxObj = self.add(
            box_status.statusBox,
            #name="当前测试负载压力",
            #footer='正在运行作业主机数:0',
            #values=['测试负载 iops: 0000', '测试负载 吞吐: 0000(Mib/s)', '测试负载 延迟: 00.00(ms)'],
            name = "任务状态",
            footer = '运行中任务数: 0',
            values = ['队列任务数: 0', '已完成任务: 0'],
            max_height=5,
            max_width=x_half,
            contained_widget_arguments={'maxlen':3},
            exit_left=True,
            exit_right=True,
            scroll_exit=True,
            editable=False
        )
        self.nextrely = ny
        self.nextrelx = nx + 28 + x_half
        self.groupstatusInfoBoxObj = self.add(
            box_status.statusBox,
            name="主机状态",
            footer='运行中主机数: 0',
            values=['选中主机组: 0/0', '选中节点数: 0/0', '在线节点数: 0/0/0'], # 选中在线/所有在线/所有
            max_height=5,
            contained_widget_arguments={'maxlen':3},
            exit_left=True,
            exit_right=True,
            scroll_exit=True,
            editable=False
        )
        self.nextrelx = nx + 28
        self.msgInfoBoxObj = self.add(
            box_messages.InfoBox,
            name="滚动消息",
            max_height=-5,
            footer=' l 搜索并高亮显示, L 取消高亮显示'
        ) #, contained_widget_arguments={'maxlen':msg_buffer})
        self.inputBoxObj = self.add(
            box_input.InputBox,
            name="非交互命令行模式: local shell",
            footer='Tab/鼠标 切换窗口, Alt + Enter 换行',
            scroll_exit=False
        )

        self.reload_group_tree()

        # init handlers, if no widget handle this, they will be handled here
        new_handlers = {
            # exit
            "^Q":               self.exit_func, # doesn't work
            #"^C":              self.exit_func, # doesn't work
            #curses.KEY_EXIT:   self.exit_func, # doesn't work
            #curses.ascii.ESC:  self.exit_func, # doesn't work, cause it was captured by the widgets inside 
            #curses.ascii.CAN:  self.exit_func, # it's a chaos, so many side affects 
            #curses.ascii.DLE:  self.exit_func, # works fine, but not needed any more 
            155:                self.exit_func,
            curses.ascii.BEL:   self.abort_func, # works and safe
            # send command
            curses.ascii.CR:    self.send_user_commands,
            curses.ascii.NL:    self.send_user_commands,
            curses.KEY_ENTER:   self.send_user_commands,
            #
            "^T":               self.test_func,
            # send file
            #"^O":              self.file_distrbution,
            #"^D":              self._debug_msg,
        }
        self.add_handlers(new_handlers)

    def reload_group_tree(self):
        # get selected nodes info

        # 添加部分示例数据到主机列表
        npyscreen.notify('正在读取主机组...', title='消息')
        time.sleep(0.25)
        #self.GroupTreeBoxObj.add_grp(name='group1', nodes=ip_list1, ssh_info=_ssh_info1)
        #self.GroupTreeBoxObj.add_grp(name='group2', nodes=ip_list2, ssh_info=_ssh_info1)
        conn = sqlite3.connect(terminal_db)
        cursorObj = conn.cursor()
        self.GroupTreeBoxObj.purge_all_grp()
        #_existed_grps = self.get_tree_groups()
        for g in list(cursorObj.execute("select * from groups")):
            _group_name = g[1]
            #if _group_name in _existed_grps:
            #    continue
            _user = g[3]
            _port = g[4]
            _tout = g[5]
            _pwd  = g[6]
            _hkey = g[7]
            _grp_ssh_info = {
                'user':     _user,
                'port':     _port,
                'timeout':  _tout,
                'password': _pwd,
                'hostkey':  _hkey
            }
            _hostname_list = map(
                lambda x: x[0],
                cursorObj.execute("select HOSTNAME from HOST WHERE GROUP_NAME = '%s' " % _group_name)
            )
            self.GroupTreeBoxObj.add_grp(name=_group_name, nodes=_hostname_list, ssh_info=_grp_ssh_info)
        cursorObj.close()

#####################################################
# common functions
#####################################################
    def update_host_status(self):
        _selected_nodes = list(self.GroupTreeBoxObj.get_selected_objects())
        _offline_hosts = list(map(lambda x : self._tset_ssh(x.get_ssh_info()), filter(lambda x : x.marker == 'host', _selected_nodes)))
        #for host in _offline_hosts: 
        pass 

    def get_tree_groups(self, only_selected=False):
        if only_selected:
            return list(
                map(
                    #lambda x : str(x.get_content()) + str(x.ssh_info),
                    lambda x : str(x.get_content()),
                    self.GroupTreeBoxObj.get_selected_objects(node_type='group')
                )
            )
        else:
            return list(
                map(
                    lambda x: str(x.get_content()),
                    filter(
                        lambda x: x.marker == 'group',
                        self.GroupTreeBoxObj.values
                    )
                )
            )

    def get_tree_hosts(self, only_selected=False):
        if only_selected:
            return list(
                map(
                    lambda x : str(x.get_content()) + ' ' + str(x.get_parent().get_content()) + str(x.get_parent().ssh_info),
                    self.GroupTreeBoxObj.get_selected_objects(node_type='host')
                )
            )
        else:
            return list(
                map(
                    lambda x: str(x.get_content()),
                    filter(
                        lambda x: x.marker == 'host',
                        self.GroupTreeBoxObj.values
                    )
                )
            )

    def _debug_msg(self):
        self.msgInfoBoxObj.append_msg(self.get_tree_hosts(only_selected=True))
        self.msgInfoBoxObj.append_msg(self.get_tree_groups())

        #_selected_groups = list(map(lambda x : str(x.get_content()) + ' ' + str(x.ssh_info) , filter(lambda x : x.marker == 'group', _selected_nodes)))
        #self.msgInfoBoxObj.append_msg(_selected_groups)
        #self.msgInfoBoxObj.append_msg(list(_selected_nodes))

        #_tmp_list = list(map(lambda x : x.marker ,  self.GroupTreeBoxObj.get_selected_objects() ))
        #self.msgInfoBoxObj.append_msg(_tmp_list)
        #npyscreen.notify_confirm(str(_tmp_list), title='debug notification')

    def test_func(self, _input):
        # check ssh 
        self.msgInfoBoxObj.append_msg(self.inputBoxObj.entry_widget.parent.name)
        self._debug_msg()

    def _test_ssh(self, ssh_info):
        try:
            _host_ssh_connection = lib_ssh_paramiko.SSHConnection(ssh_info)
        except:
            return ssh_info['host']

    def ssh_cmd(self, cmd_list, ssh_info):
        try:
            _host_ssh_connection = lib_ssh_paramiko.SSHConnection(ssh_info)
        except:
            _result = [ ssh_info['host'] + ':' + ' unable to init Connection!' ]
            self.msgInfoBoxObj.append_msg(_result)
            return ssh_info['host']
        _result = [ ssh_info['host'] + ':', ]
        if isinstance(cmd_list, list):
            for cmd in cmd_list:
                ret = _host_ssh_connection.exec_command(cmd)
                _result += ret.split('\n')
        else:
            ret = _host_ssh_connection.exec_command(cmd_list)
            _result += ret.split('\n')
        self.msgInfoBoxObj.append_msg(_result)

#####################################################
# func for events
#####################################################
    def event_target_select(self, event):
        target_hosts = self.chatBoxObj.value
        #client.dialogs[current_user].unread_count = 0

##    def event_messagebox_change_cursor(self, event):
##        current_user = self.chatBoxObj.value
##        messages = self.messageBoxObj.get_messages_info(current_user)
##        date = messages[len(messages) - 1 - self.messageBoxObj.entry_widget.cursor_line].date
##
##        self.messageBoxObj.footer = str(date + (timedelta(self.timezone) // 24))
##        self.messageBoxObj.update()

    # handling methods

    def send_user_commands(self, event):
        _cmd_str = self.inputBoxObj.value 
        self.inputBoxObj.value = ""
        self.inputBoxObj.display()
        #current_user = self.chatBoxObj.value
        self.msgInfoBoxObj.append_msg(_cmd_str)

        if self.shell_mode == 'local':
            _return_str = lib_cli_bash.ez_cmd(_cmd_str).split('\n')
        else:
            _selected_nodes = list(self.GroupTreeBoxObj.get_selected_objects())
            _selected_hosts = list(
                filter(
                    lambda x : x.marker == 'host',
                    _selected_nodes
                )
            )
            if _selected_hosts:
                #
                _offline_hosts  = list(
                    filter(
                        lambda x: x != None,
                        map(
                            lambda x : self.ssh_cmd(_cmd_str, x.get_ssh_info()),
                            _selected_hosts
                        )
                    ) 
                )
                if len(_offline_hosts): #>0
                    self.msgInfoBoxObj.append_msg('failed: ' + str(_offline_hosts) )
                _return_str = ""
            else:
                _return_str = '没有目标主机'
            self.inputBoxObj.display()
        if _return_str :
            self.msgInfoBoxObj.append_msg(_return_str)
            self.inputBoxObj.display()

    def event_update_main_form(self, event):
        self.display()
        self.msgInfoBoxObj.display()

#####################################################
# menu functions
#####################################################
    def switch_cli_mode(self):
        if self.shell_mode == 'local':
            self.shell_mode = 'cluster'
        else:
            self.shell_mode = 'local'

        self.inputBoxObj.name = '非交互命令行模式: ' + self.shell_mode + ' shell'
        self.msgInfoBoxObj.append_msg('非交互命令行模式已切换到:' + self.shell_mode + ' shell')

    def launch_IO_test(self):
        pass
    
    def turn_on_taskflow(self):
        pass

    def manage_taskflow(self):
        pass

    def add_task(self):
        self.parentApp.switchForm('AddTaskForm')

    def add_group(self):
        self.parentApp.switchForm('AddHostGroupForm')

    def del_group(self):
        grp2del = self.get_tree_groups(only_selected=True)
        if grp2del:
            conn = sqlite3.connect(terminal_db)
            c = conn.cursor()
            for grp in grp2del:
                c.execute("DELETE FROM groups WHERE GROUP_NAME = '%s';" % grp)
                c.execute("DELETE FROM host WHERE GROUP_NAME = '%s';" % grp)
            conn.commit()
            c.close()
        self.reload_group_tree()

    def deploy_ceph(self):
        self.parentApp.switchForm('CephDeplyForm')

    def config_ceph(self):
        pass

    def purge_ceph(self):
        pass

    def show_help(self):
        self.parentApp.switchForm('HelpForm')

    def exit_func(self, *args):
        if npyscreen.notify_yes_no('确定要退出吗?', title='确认退出:'):
            self.safe_exit()

    def abort_func(self, _input):
        if npyscreen.notify_yes_no('确定要中断现有任务并退出吗?', title='终止退出:'):
            # some staff of killing sessions
            self.dump_grptree()
            self.dump_msginfo()
            exit(0)

    def _cancel_signal(self, *args, **keywords):
        # check wdget on editing
        # abort 
        self.safe_exit()

    def safe_exit(self):
        # some thing to check before exit 
        exit(0)
        pass

    def file_distrbution(self):
        pass 

    def file_collection(self):
        pass 

#####################################################
# update main window 
#####################################################
    # update loop
    def while_waiting(self):
        pass 

    #def while_editing(self,*args, **keywords):
    #    self.msgInfoBoxObj.display()

