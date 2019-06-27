#!/usr/bin/env python
# coding=utf-8

import os
import re 
import time
import curses
from src import npyscreen

import sqlite3
terminal_db = './db/terminal.db'

def conf_loadable(file_name=None):
    if file_name:
        cmd = 'file ' + file_name + ' |grep text -q'
        ret = os.system(cmd)
        if ret == 0:
            return True
        else:
            return False
    else:
        raise NameError

 # ('./abc', 'def', '.h')
def get_file_name(_path_filename):
    (filepath,tmpfilename) = os.path.split(_path_filename)
    (shortname,extension)  = os.path.splitext(tmpfilename)
    return filepath,shortname,extension

def line_available(line_in_conf):
    if line_in_conf.strip()[0] == '#':
        return False
    else:
        return True 

def get_line_content(line_in_conf):
    return re.split(',|#', line_in_conf.strip().split()[0])[0]

def load_conf_content(file_name):
    with open(file_name) as _conf_file:
        _conf_lines = _conf_file.readlines()
    _conf_content = list(map(get_line_content, filter(line_available, _conf_lines)))
    return _conf_content

def ip_reachable(_ipaddr):
    #    cmd = 'ping -c1 ' + ip + '&>/dev/null'
    #    cmd_stat = os.system(cmd)
    #    if cmd_stat == 0:
    return True 

#MultiLineEditableBoxed
class TitleEditBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    def add_tx(self, text):
        self.entry_widget.value = text

class AddHostGroupForm(npyscreen.ActionFormV2):
    def create(self):
        self.name = '配置并添加新的主机组:'
        # record y
        self.ny = self.nextrely
        self.add_mode = self.add(
            npyscreen.TitleMultiSelect,
            name='添加选项',
            begin_entry_at=15,
            max_height=4,
            field_width=45,
            value=[0,1,],
            values=[
                "从文件加载 ip  列表",
                "指定ssh连接私钥文件",
                "执行 网络连接预检测",
            ],
            exit_right=True,
            scroll_exit=True,
            # add a callback for this widget when its value changed
            value_changed_callback  =   self.add_mode_value_changed_callback
        )

        # recover y     vertically
        # move x + 45   horizontally
        self.nextrely = self.ny
        self.nextrelx += 45
        self.grp_conf = self.add(npyscreen.TitleFilenameCombo, name="grp_conf:", exit_left=True)
        self.ssh_key  = self.add(npyscreen.TitleFilenameCombo, name="Identity:", exit_left=True)
        # pre check 
        self.conTimeout = self.add(npyscreen.TitleSlider, name="超时时间:", exit_left=True, field_width=55, lowest=10, out_of=90, step=10)
        self.conTimeout.value = 10
        self.conTimeout.hidden = True

        self.nextrely += 1
        # recover x
        self.nextrelx += -30
        self.grp_name = self.add(npyscreen.TitleText, begin_entry_at=22, name='主机组名称(必填):')
        self.ssh_user = self.add(npyscreen.TitleText, begin_entry_at=22, name='ssh 用户:')
        self.grp_port = self.add(npyscreen.TitleText, begin_entry_at=22, name='ssh 端口  (必填):')
        self.ssh_pswd = self.add(npyscreen.TitleText, begin_entry_at=22, name='ssh 口令:')

        self.nextrely += 1
        # record y
        self.ny = self.nextrely
        self.host_list   = self.add(
            npyscreen.MultiLineEditableBoxed,
            max_width=40,
            name='主机地址预览:',
            values=['0.0.0.0'],
            footer='空格:修改, i:插入, o:新行'
        )

        self.nextrely  = self.ny
        self.nextrelx += 45
        self.host_list_tmp  = self.add(
            TitleEditBox,
            name='手动编辑区:',
            footer='使用 ^r 格式化换行, ^e 预览结果')
        self.host_list_tmp.add_tx('example-hostname1 example-hostname2 example-hostname3')

        # record cof value status
        self._conf_refreshed = None
        self._loadable_conf_status = {
            'grp':self.grp_conf.value,
        }
        # key binding
        self.add_handlers({
            "^Q":               self.exit_func,
            155:                self.exit_func,
            curses.ascii.BEL:   self.exit_func2,
            "^E":               self.reformat_hostname,
        })

    def exit_func(self,  _input):
        self.on_cancel()

    def exit_func2(self,  _input):
        if npyscreen.notify_yes_no('程序需要先退回主界面才能完全退出,\n确定要放弃添加新组并退回主界面吗?', title='任务中断:'):
            self.on_cancel()

    def reformat_hostname(self, _input):
        self.host_list_tmp.entry_widget.full_reformat()
        self.host_list.values = self.host_list_tmp.value.split()
        self.display()

    # callback for add_mode widget 
    def add_mode_value_changed_callback(self, widget=None):
        if widget:
            _target_widget = widget
        else:
            return 

        # hidden grp_conf 
        _target_value = _target_widget.value 
        if 0 in _target_value :
            self.grp_conf.hidden = False
        else:
            self.grp_conf.hidden = True
        if 1 in _target_value :
            self.ssh_key.hidden = False
        else:
            self.ssh_key.hidden = True
        # hidden conTimeout 
        if 2 in _target_value :
            self.conTimeout.hidden = False
        else:
            self.conTimeout.hidden = True

    def check_loadable_conf_status(self):

        if self.grp_conf.value != self._loadable_conf_status['grp']:
            self._loadable_conf_status['grp'] = self.grp_conf.value
            self._conf_refreshed = True

    def when_conf_refreshed(self):
        #load config file
        if self.grp_conf.value :
            if conf_loadable(self.grp_conf.value):
                self.host_list.values = load_conf_content(self.grp_conf.value)
                self.grp_name.value =get_file_name(self.grp_conf.value)[1]

    def adjust_widgets(self):
        self.check_loadable_conf_status()
    # the value somehow will be uneditable any more  
    # the will be reload everytime a key was pressed!!
    # don't load conf here. 
        if self._conf_refreshed:
            self.when_conf_refreshed()
            self._conf_refreshed = None

    #def while_editing(self, z):
    #    # the value suppose to be updated after edting status is false, not while editing
    #    self.add_mode_value_changed_callback(widget=self.add_mode)


    # check value format
    def check_grp_value(self):

        # group name reformat
        self.grp_name.value = str(self.grp_name.value).strip().replace(' ', '_')

        # ip/hostname list 
        if isinstance(self.host_list.value, str):
            # to be changed  when  new contained widget is ready  
            self.host_list.values = _nodes_to_add = self.host_list.values.split()
            if not npyscreen.notify_yes_no('请注意主机地址使用换行符进行分割, 请确认格式化结果!' + '\n'.join(_nodes_to_add), title='主机信息格式异常:'):
                return False
        else:
            _nodes_to_add = self.host_list.values 

        # empty value 
        if not self.ssh_user.value or len(self.ssh_user.value.strip()) == 0:
            self.ssh_user.value = None
        if not self.ssh_pswd.value or len(self.ssh_pswd.value.strip()) == 0:
            self.ssh_pswd.value = None
        if not self.ssh_key.value or len(self.ssh_key.value.strip()) == 0:
            self.ssh_key.value = None 

        # port value check
        _port_str = self.grp_port.value.strip()
        if len(_port_str) == 0 or not _port_str.isdigit() or int(_port_str) >65535 :
            npyscreen.notify_confirm("无效的端口号信息,请重新填写端口号", title="登录信息不全:")
            return False 

        # group name 
        if not self.grp_name.value:
            npyscreen.notify_confirm('请填写组名!', title='组名无效:')
            return False 

        # ip/hostname list 
        if not _nodes_to_add:
            npyscreen.notify_confirm('请填写主机地址!', title='地址无效:')
            return False

        # id key or user+password
        if not self.ssh_key.value:
            if not self.ssh_user.value:
                npyscreen.notify_confirm('请指定登录秘钥或者填写该组登录用户!', title='登录信息不全:')
                return False
            if not self.ssh_pswd.value:
                npyscreen.notify_confirm('请指定登录秘钥或者填写该组登录口令!', title='登录信息不全:')
                return False
        else:
            npyscreen.notify_confirm(str(self.ssh_key.value), 'ssh_key')


        # ip ping / ssh check 
        if 2 in self.add_mode.value:
            _valid_host_list = list(filter(ip_reachable, _nodes_to_add))
        else:
            _valid_host_list = _nodes_to_add 

        # after check 
        if _valid_host_list:
            if len(_valid_host_list) == len(_nodes_to_add) :
                if 2 in self.add_mode.value:
                    npyscreen.notify('主机正常', title='检查完成')
                    time.sleep(0.5)
                return True
            else:
                if not npyscreen.notify_yes_no( '\n'.join(_nodes_to_add), title='确认主机检查结果:'):
                    return False 
        else:
            if 2 in self.add_mode.value:
                npyscreen.notify_confirm('没有可用的主机地址!\n请注意检查网络.', title='无法添加:')
            else:
                npyscreen.notify_confirm('没有可用的主机地址!\n请注意检查格式.', title='无法添加:')
            return False

    def auto_add_grp(self):
        npyscreen.notify('正在检查信息', title='正在添加:')
        time.sleep(0.5)
        if self.check_grp_value():
            # add group info to db 
            conn = sqlite3.connect(terminal_db)
            cursor = conn.cursor()
            # groups 
            cursor.execute(
                "INSERT INTO groups (GROUP_NAME, SSH_USER, SSH_PORT, SSH_TIMEOUT, SSH_PASSWORD, SSH_HOSTKEY) \
                VALUES ('%s', '%s', %s, %s, '%s', '%s')" \
                % (self.grp_name.value, self.ssh_user.value, self.grp_port.value, self.conTimeout.value, self.ssh_pswd.value, self.ssh_key.value)
            )
            # host 
            for hostname in self.host_list.values:
                #cursor.execute("INSERT INTO host (HOSTNAME, GROUP_NAME, BOARD_SN, TAG) VALUES ('%s', '%s', '%s', '%s')" % (hostname, self.grp_name.value, sn, tag))
                cursor.execute("INSERT INTO host (HOSTNAME, GROUP_NAME) VALUES ('%s', '%s')" % (hostname, self.grp_name.value))
            conn.commit()
            cursor.close()

            self.parentApp.MainForm.reload_group_tree()
            self.parentApp.setNextForm('MAIN')

    def on_ok(self):
        self.auto_add_grp()

    def on_cancel(self):
        self.parentApp.setNextForm('MAIN')
        self.exit_editing()


if __name__ == "__main__":

    class testApp(npyscreen.NPSAppManaged):
        #npyscreen.ThemeManager.default_colors['LABEL'] = 'YELLOW_BLACK' 
        def onStart(self):
            self.MainForm = self.addForm("MAIN", HostGroupForm)

    App = testApp()
    App.run()
