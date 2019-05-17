#!/usr/bin/env python
# coding=utf-8

import os
import re 
import time
import curses
from src import npyscreen

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

#class TitleEditBox(npyscreen.BoxTitle):
#    _contained_widget = npyscreen.MultiLineEdit
#    def add_tx(self, text):
#        self.entry_widget.value = text

class HostGroupForm(npyscreen.ActionFormV2):
    def create(self):
        self.name = '配置并添加新的主机组:'
        # record y
        self.ny = self.nextrely
        self.add_mode = self.add(npyscreen.TitleMultiSelect, begin_entry_at=15, name='添加选项', max_height=4, field_width=40,
                                 value=[0,1,2,3,],
                                 values=["从文件加载 ip  列表", "从文件加载 磁盘列表", "指定ssh连接私钥文件", "执行 网络连接预检测"],
                                 value_changed_callback=self.value_changed_callback,
                                 exit_right=True,
                                 scroll_exit=True)
        # recover y, move right: + x
        self.nextrely = self.ny
        self.nextrelx += 45
        self.grp_conf = self.add(npyscreen.TitleFilenameCombo,  begin_entry_at=15, name="grp_conf:", exit_left=True)
        self.blk_conf = self.add(npyscreen.TitleFilenameCombo,  begin_entry_at=15, name="blk_conf:", exit_left=True)
        self.grp_key  = self.add(npyscreen.TitleFilenameCombo,  begin_entry_at=15, name="Identity:", exit_left=True)
        # pre check 
        self.conTimeout = self.add(npyscreen.TitleSlider, field_width=55, begin_entry_at=15, lowest=10, out_of=90, step=10, name="超时时间:", exit_left=True)
        self.conTimeout.value = 10
        self.nextrely += 1
        # recover x
        self.grp_name = self.add(npyscreen.TitleText, begin_entry_at=18, name='组名称 (必填):')
        self.grp_user = self.add(npyscreen.TitleText, begin_entry_at=18, name='ssh 用户:')
        self.grp_port = self.add(npyscreen.TitleText, begin_entry_at=18, name='ssh 端口(必填):')
        self.grp_pswd = self.add(npyscreen.TitleText, begin_entry_at=18, name='ssh 口令:')
        self.nextrely += 1
        # record y
        self.nextrelx += -30
        self.ny = self.nextrely
        self.ip_list   = self.add(npyscreen.MultiLineEditableBoxed, max_width=40,
                                  name='主机IP列表:',
                                  values=['0.0.0.0'],
                                  footer='按下 i 或 o 开始编辑')
        #self.ip_list.add_tx('你可以在此手动粘贴 IP 列表,\n使用 ^R 查看格式化结果,\n添加前请务必删除此处注释文本.\n')
        self.nextrely  = self.ny
        self.nextrelx += 45
        self.blk_list  = self.add(npyscreen.MultiLineEditableBoxed, max_width=40, 
                                  name='块设备列表:',
                                  values=['/dev/sdx', '/dev/sdy','/dev/sdz'],
                                  footer='使用tab切换到其他控件')
        #self.blk_list.add_tx('你可以在此手动编辑磁盘列表,\n使用 ^R 查看格式化结果,添加前请务必删除此处注释文本.\n')

        self._conf_refreshed = None
        self._loadable_conf_status = {
            'grp':self.grp_conf.value,
            'blk':self.blk_conf.value,
        }
        self.add_handlers({
            #curses.ascii.ESC: self.exit_func,
            "^Q":             self.exit_func,
            155:              self.exit_func,
            curses.ascii.BEL: self.exit_func2,
        })

    def exit_func(self,  _input):
        self.on_cancel()

    def exit_func2(self,  _input):
        if npyscreen.notify_yes_no('程序需要先退回主界面才能完全退出,\n确定要放弃添加新组并退回主界面吗?', title='任务中断:'):
            self.on_cancel()

    def value_changed_callback(self, widget=None):
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
        # hidden blk_conf 
        if 1 in _target_value :
            self.blk_conf.hidden = False
        else:
            self.blk_conf.hidden = True
        if 2 in _target_value :
            self.grp_key.hidden = False
        else:
            self.grp_key.hidden = True
        # hidden conTimeout 
        if 3 in _target_value :
            self.conTimeout.hidden = False
        else:
            self.conTimeout.hidden = True

    def check_loadable_conf_status(self):
        if self.grp_conf.value != self._loadable_conf_status['grp']:
            self._loadable_conf_status['grp'] = self.grp_conf.value
            self._conf_refreshed = True
        if self.blk_conf.value != self._loadable_conf_status['blk']:
            self._loadable_conf_status['blk'] = self.blk_conf.value 
            self._conf_refreshed = True

    def when_conf_refreshed(self):
        #load config file
        if self.grp_conf.value :
            if conf_loadable(self.grp_conf.value):
                self.ip_list.values = load_conf_content(self.grp_conf.value)
                self.grp_name.value =get_file_name(self.grp_conf.value)[1]
        if self.blk_conf.value:
            if conf_loadable(self.blk_conf.value):
                self.blk_list.values = load_conf_content(self.blk_conf.value)

    #def while_editing(self, z):
    def adjust_widgets(self):
        self.check_loadable_conf_status()
    # the value somehow will be uneditable any more  
    # the will be reload everytime a key was pressed!!
    # don't load conf here. 
        if self._conf_refreshed:
            self.when_conf_refreshed()
            self._conf_refreshed = None

    def check_grp_value(self):

        self.grp_name.value = str(self.grp_name.value).strip().replace(' ', '_')

        # ip list 
        if isinstance(self.ip_list.value, str):
            # to be changed  when  new contained widget is ready  
            self.ip_list.values = _nodes_to_add = self.ip_list.values.split()
            if not npyscreen.notify_yes_no('请注意IP地址使用换行符进行分割, 请确认格式化结果!' + '\n'.join(_nodes_to_add), title='IP格式异常:'):
                return False
        else:
            _nodes_to_add = self.ip_list.values 

        if not self.grp_user.value or len(self.grp_user.value.strip()) == 0:
            self.grp_user.value = None
        if not self.grp_pswd.value or len(self.grp_pswd.value.strip()) == 0:
            self.grp_pswd.value = None
        if not self.grp_key.value or len(self.grp_key.value.strip()) == 0:
            self.grp_key.value = None 

        _port_str = self.grp_port.value.strip()
        if len(_port_str) == 0 or not _port_str.isdigit() or int(_port_str) >65535 :
            npyscreen.notify_confirm("无效的端口号信息,请重新填写端口号", title="端口号无效:")
            return False 

        # group name 
        if not self.grp_name.value:
            npyscreen.notify_confirm('请填写组名!', title='组名无效:')
            return False 

        # ip list 
        if not _nodes_to_add:
            npyscreen.notify_confirm('请填写主机IP!', title='IP无效:')
            return False

        # ip ping / ssh check 
        if 2 in self.add_mode.value:
            _valid_ip_list = list(filter(ip_reachable, _nodes_to_add))
        else:
            _valid_ip_list = _nodes_to_add 

        # after check 
        if _valid_ip_list:
            if len(_valid_ip_list) == len(_nodes_to_add) :
                if 2 in self.add_mode.value:
                    npyscreen.notify('IP 正常', title='检查完成')
                    time.sleep(0.5)
                return True
            else:
                if not npyscreen.notify_yes_no( '\n'.join(_nodes_to_add), title='确认IP 检查结果:'):
                    return False 
        else:
            if 2 in self.add_mode.value:
                npyscreen.notify_confirm('没有可用的IP地址!\n请注意检查网络.', title='无法添加:')
            else:
                npyscreen.notify_confirm('没有可用的IP地址!\n请注意检查格式.', title='无法添加:')
            return False

    def auto_add_grp(self):
        npyscreen.notify('正在检查信息', title='正在添加:')
        time.sleep(0.5)
        if self.check_grp_value():
            _ssh_info = {
                'prot':     int(self.grp_port.value),
                'user':     self.grp_user.value,
                'password': self.grp_pswd.value,
                'timeout':  int(self.conTimeout.value),
                'hostkey':  self.grp_key.value
            }
            self.parentApp.MainForm.GroupTreeBoxObj.add_grp(name=self.grp_name.value, nodes=self.ip_list.values, ssh_info=_ssh_info)
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
