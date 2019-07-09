#!/usr/bin/env python
# coding=utf-8

import time
import curses
from src import npyscreen
from src import box_messages
from src import box_grouptree

import sqlite3
terminal_db = './db/terminal.db'

def conf_loadable(file_name=None):
    if file_name:
        cmd = 'file ' + file_name + ' |grep text -q'
        if os.system(cmd): # return code != 0
            return False
        else:
            return True
    else:
        raise TypeError('it seemed that %s is not a loadable text file' % file_name)

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
    def set_tx(self, text):
        self.entry_widget.value = text

class HostGroupForm(npyscreen.ActionFormV2):

    group_list  = []
    group_editable  = False
    current_group   = None

    edit_status = 'select' # 'insert delete update'

    CANCEL_BUTTON_BR_OFFSET = (2, 24)
    OK_BUTTON_TEXT = '完成  '
    CANCEL_BUTTON_TEXT = '返回  '

    def create(self):
        self.name = '管理配置主机组:'

        # window size
        y, x = self.useable_space()
        ny = self.nextrely
        nx = self.nextrelx

        # host group tree
        self.GroupTreeBox   = self.add(
            box_grouptree.HostGroupTreeBox,
            name="主机组",
            max_width=28,
            editable=False,
            scroll_exit=False
        ) #, value=0, relx=1, max_width=x // 5, rely=2,
        self.GroupTreeBox.reload_group_tree()

        # select box ; back to topline
        self.nextrely = ny
        self.nextrelx = nx + 28
        self.group_select_box    = self.add(
            box_messages.InfoBox,
            name = "主机组 列表",
            footer = 'l 搜索主机组, L 取消搜索高亮, <Ctrls + x> / <空格> 选中条目, Ctrl + r 刷新列表',
            values = self.group_list,
            max_height = 8,
            editable=False,
            exit_left=True,
            exit_right=True,
            scroll_exit=True,
        )
        self.help0      = self.add(npyscreen.TitleText, name='组编辑:', value='Ctrl + a 添加, Ctrl + d 删除, Ctrl + u 更新, Ctrl + s 提交编辑结果', begin_entry_at=9, editable=False)
        self.group_id   = self.add(npyscreen.TitleText, name='组ID号:', value='-', begin_entry_at=9, editable=False)

        # group connection preset
        self.ny2 = self.nextrely
        self.nextrelx += 2
        self.add_mode = self.add(
            npyscreen.TitleMultiSelect,
            name='加载选项',
            begin_entry_at=1,
            max_height=4,
            field_width=24,
            value=[1,],
            values=[
                "加载主机地址列表",
                "指定 ssh连接私钥",
                "网络连接  预检测",
            ],
            editable=False,
            exit_right=True,
            scroll_exit=True,
            # add a callback for this widget when its value changed
            value_changed_callback  =   self.add_mode_value_changed_callback
        )

        # recover y     vertically
        # move x + 45   horizontally
        self.nextrely = self.ny2
        self.nextrely += 1
        self.nextrelx += 25
        self.ip_list_file           = self.add(npyscreen.TitleFilenameCombo, name="grp_conf:", begin_entry_at=12, max_width=40, editable=False, exit_left=True)
        self.ssh_private_key_file   = self.add(npyscreen.TitleFilenameCombo, name="Identity:", begin_entry_at=12, max_width=40, editable=False, exit_left=True)
        # pre check
        self.ssh_connect_timeout    = self.add(npyscreen.TitleSlider, name="超时时间:", exit_left=True, field_width=35, lowest=10, out_of=90, step=10, max_width=40, editable=False)
        self.ssh_connect_timeout.value = 10
        self.ssh_connect_timeout.hidden = True

        # recover x
        self.nextrelx -= 25
        self.nextrely += 1
        self.ny = self.nextrely
        self.grp_name = self.add(npyscreen.TitleText, name='* 组名称  :', begin_entry_at=14, max_width=40, editable=False)
        self.ssh_port = self.add(npyscreen.TitleText, name='* ssh 端口:', begin_entry_at=14, max_width=40, editable=False)

        self.nextrely = self.ny
        self.nextrelx += 45
        self.ssh_user = self.add(npyscreen.TitleText, name='  ssh 用户:', begin_entry_at=14, max_width=40, editable=False)
        self.ssh_pswd = self.add(npyscreen.TitleText, name='  ssh 口令:', begin_entry_at=14, max_width=40, editable=False)
        self.nextrelx -= 45

        # record y
        self.ny = self.nextrely
        self.host_list_tmp  = self.add(
            TitleEditBox,
            name='手动编辑区:',
            footer='使用 ^r 格式化换行, ^e 预览结果',
            # host group tree 28, host list 32, margin 4 * 2
            max_width= x -28 -32 -8,
            editable=False,
        )
        self.host_list_tmp.set_tx('example-hostname1 example-hostname2 example-hostname3')

        self.nextrely  = self.ny2 +1
        self.nextrelx = -35
        self.host_list   = self.add(
            npyscreen.MultiLineEditableBoxed,
            max_width=32,
            name='主机地址:',
            values=['0.0.0.0'],
            footer='空格:修改, i:插入, o:新行',
            editable=False,
            scroll_exit=True,
            exit_left=True
        )

        # record cof value status
        self._conf_refreshed = None
        self._loadable_conf_status = {
            'grp':self.ip_list_file.value,
            'key':self.ssh_private_key_file.value,
        }

        self.add_handlers({
            "^Q":               self.exit_func,
            155:                self.exit_func,
            curses.ascii.BEL:   self.exit_func2,
            "^E":               self.reformat_hostname,
            "^P":               self.print_selected_group_index,
            "^R":               self.refresh_group_list,
            "^A":               self.add_new_group,
            "^D":               self.delete_selected_group,
            "^U":               self.update_selected_group,
            "^S":               self.commit_modified_group,
            "^W":               self.give_up_group_editing,
        })

    def exit_func(self,  _input):
        self.on_cancel()

    def exit_func2(self,  _input):
        if npyscreen.notify_yes_no('程序需要先退回主界面才能完全退出,\n确定要放弃并退回主界面吗?', title='任务中断:'):
            self.on_cancel()

    def refresh_group_lis(self, _input):
        self.dump_group_list()
        self.display()

    def dump_group_list(self):
        conn  = sqlite3.connect(terminal_db)
        cur = conn.cursor()
        self.group_list = list(cur.execute("SELECT * FROM groups ;"))
        cur.close()
        self.group_select_box.values = self.group_list

    # callback for add_mode widget 
    def add_mode_value_changed_callback(self, widget=None):
        if widget:
            _target_widget = widget
        else:
            return 
        # hidden grp_conf 
        _target_value = _target_widget.value 
        if 0 in _target_value :
            self.ip_list_file.hidden = False
        else:
            self.ip_list_file.hidden = True
        if 1 in _target_value :
            self.ssh_private_key_file.hidden = False
        else:
            self.ssh_private_key_file.hidden = True
        # hidden conTimeout 
        if 2 in _target_value :
            self.ssh_connect_timeout.hidden = False
        else:
            self.ssh_connect_timeout.hidden = True

    def check_loadable_conf_status(self):

        if self.ip_list_file.value != self._loadable_conf_status['grp']:
            self._loadable_conf_status['grp'] = self.ip_list_file.value
            self._conf_refreshed = True
        if self.ssh_private_key_file.value != self._loadable_conf_status['key']:
            self._loadable_conf_status['key'] = self.ssh_private_key_file.value
            self._conf_refreshed = True

    def when_conf_refreshed(self):
        #load config file
        if self.ip_list_file.value :
            if conf_loadable(self.ip_list_file.value):
                self.host_list.values = load_conf_content(self.grp_conf.value)
                self.grp_name.value =get_file_name(self.grp_conf.value)[1]

    # the will be reload everytime a key was pressed!!
    # don't load conf here. 
    def adjust_widgets(self):
        self.check_loadable_conf_status()
        if self._conf_refreshed:
            self.when_conf_refreshed()
            self._conf_refreshed = None

    def reformat_hostname(self, _input):
        self.host_list_tmp.entry_widget.full_reformat()
        self.host_list.values = self.host_list_tmp.value.split()
        self.display()

    def print_selected_group_index(self, _input):
        npyscreen.notify_confirm(str(self.group_select_box.value), title='current value')

    def load_group_preview(self):
        if self.current_group:
            current_group = self.current_group
        elif isinstance(self.group_select_box.value, int):
            current_group = self.group_list[self.group_select_box.value]
        else:
            return

        self.group_id.value = str(current_group[0])
        self.grp_name.value = current_group[1]
        # status
        # user
        # port
        # timeout
        # password
        # host_key 
        # tag

    # check value format
    def check_grp_value(self):
        # group name reformat
        self.grp_name.value = str(self.grp_name.value).strip().replace(' ', '_')
        _nodes_to_add = self.host_list.values

        # empty value 
        if not self.ssh_user.value or len(self.ssh_user.value.strip()) == 0:
            self.ssh_user.value = None
        if not self.ssh_pswd.value or len(self.ssh_pswd.value.strip()) == 0:
            self.ssh_pswd.value = None
        if not self.ssh_private_key_file.value or len(self.ssh_private_key_file.value.strip()) == 0:
            self.ssh_private_key_file.value = None 

        # port value check
        _port_str = self.ssh_port.value.strip()
        if len(_port_str) == 0 or not _port_str.isdigit() or int(_port_str) >65535 :
            npyscreen.notify_confirm("无效的端口号信息,请重新填写端口号", title="登录信息不全:")
            return False 

        # group name 
        if not self.grp_name.value:
            npyscreen.notify_confirm('请填写组名!', title='组名缺失:')
            return False 

        # ip/hostname list 
        if not _nodes_to_add:
            npyscreen.notify_confirm('请填写主机地址!', title='地址缺失:')
            return False

        # id key or user+password
        if not self.ssh_private_key_file.value:
            if not self.ssh_user.value:
                npyscreen.notify_confirm('请指定登录秘钥或者填写该组登录用户!', title='登录信息不全:')
                return False
            if not self.ssh_pswd.value:
                npyscreen.notify_confirm('请指定登录秘钥或者填写该组登录口令!', title='登录信息不全:')
                return False

        # ip network(ping) / ssh check 
        if 2 in self.add_mode.value:
            _valid_host_list = list(filter(ip_reachable, _nodes_to_add))
            if len(_valid_host_list) == len(_nodes_to_add) :
                npyscreen.notify('主机正常', title='检查完成')
                time.sleep(0.2)
            elif not len(_valid_host_list):
                npyscreen.notify_confirm('没有可用的主机地址!\n请注意检查网络.', title='无法添加:')
                return False
            elif not npyscreen.notify_yes_no( '\n'.join(_nodes_to_add), title='确认主机检查结果:'):
                return False

        # after check 
        return True

    def auto_add_grp(self):
        npyscreen.notify('正在检查信息', title='正在添加:')
        time.sleep(0.2)
        if self.check_grp_value():
            # add group info to db 
            conn = sqlite3.connect(terminal_db)
            cursor = conn.cursor()
            # groups 
            cursor.execute(
                "INSERT INTO groups (GROUP_NAME, SSH_USER, SSH_PORT, SSH_TIMEOUT, SSH_PASSWORD, SSH_HOSTKEY) \
                VALUES ('%s', '%s', %s, %s, '%s', '%s')" \
                % (self.grp_name.value, self.ssh_user.value, self.ssh_port.value, self.ssh_connect_timeout.value, self.ssh_pswd.value, self.ssh_private_key_file.value)
            )
            # host 
            for hostname in self.host_list.values:
                #cursor.execute("INSERT INTO host (HOSTNAME, GROUP_NAME, BOARD_SN, TAG) VALUES ('%s', '%s', '%s', '%s')" % (hostname, self.grp_name.value, sn, tag))
                cursor.execute("INSERT INTO host (HOSTNAME, GROUP_NAME) VALUES ('%s', '%s')" % (hostname, self.grp_name.value))
            conn.commit()
            cursor.close()

            self.parentApp.MainForm.GroupTreeBoxObj.reload_group_tree()
            self.parentApp.setNextForm('MAIN')

    def auto_update_grp(self):
        npyscreen.notify('正在检查信息', title='正在更新:')
        time.sleep(0.2)
        if self.check_grp_value():
            # add group info to db 
            conn = sqlite3.connect(terminal_db)
            cursor = conn.cursor()
            # groups 
            cursor.execute(
                "UPDATE groups SET GROUP_NAME = '%s', SSH_USER = '%s', SSH_PORT = '%s', SSH_TIMEOUT = %s, SSH_PASSWORD = '%s', SSH_HOSTKEY = '%s'" \
                % (self.grp_name.value, self.ssh_user.value, self.ssh_port.value, self.ssh_connect_timeout.value, self.ssh_pswd.value, self.ssh_private_key_file.value)
            )
            # host 
            for hostname in self.host_list.values:
                #cursor.execute("INSERT INTO host (HOSTNAME, GROUP_NAME, BOARD_SN, TAG) VALUES ('%s', '%s', '%s', '%s')" % (hostname, self.grp_name.value, sn, tag))
                cursor.execute("INSERT INTO host (HOSTNAME, GROUP_NAME) VALUES ('%s', '%s')" % (hostname, self.grp_name.value))
            conn.commit()
            cursor.close()

            self.parentApp.MainForm.GroupTreeBoxObj.reload_group_tree()
            self.parentApp.setNextForm('MAIN')

    def on_ok(self):
        self.parentApp.setNextFormPrevious()

    def on_cancel(self):
        self.parentApp.setNextFormPrevious()
        self.exit_editing()

#if __name__ == "__main__":
#    print('')
