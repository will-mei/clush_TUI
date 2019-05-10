#!/usr/bin/env python
# coding=utf-8

import time
import curses
from src import npyscreen

_tmp_fake_data = ['接口类型 sata/sas',
                  '磁盘类型 hdd',
                  '容量大于(GB) xx',
                  '容量小于(GB) xx',
                  '设备名不含 xx',
                  '设备名包含 xx',
                  '厂商信息包含 xx',
                  '产品型号包含 xx',
                 ]

class _tag_host(npyscreen.Textfield):

    def set_up_handlers(self):
        super().set_up_handlers()
        self.handlers[curses.KEY_LEFT] = self.h_switch_host_tag_osd
        self.handlers[curses.KEY_RIGHT] = self.h_switch_host_tag_mon

    def h_switch_host_tag_osd(self, _input):
        if self.editable:
            self.value = self.value.split(' ')[0] + ' osd'
    def h_switch_host_tag_mon(self, _input):
        if self.editable:
            self.value = self.value.split(' ')[0] + ' MONITOR'

class MultiLineEditable_tag_host(npyscreen.MultiLineEditable):
    _contained_widgets      = _tag_host 

class MultiLineEditableBoxed_tag_host(npyscreen.BoxTitle):
    _contained_widget = MultiLineEditable_tag_host 

class CephDeplyForm(npyscreen.ActionFormV2):
    def create(self):
        self.name = '部署新的ceph集群:'
        # record y
        self.ny = self.nextrely
        self.add_mode = self.add(npyscreen.TitleMultiSelect, begin_entry_at=15, name='部署选项', max_height=2, field_width=40,
                                 value=[0,],
                                 values=["加载往期集群部署配置", "自动使用已选主机节点"],
                                 value_changed_callback=self.value_changed_callback,
                                 exit_right=True,
                                 scroll_exit=True)
        # recover y, move right: + x
        self.nextrely = self.ny
        self.nextrelx += 45
        self.deploy_conf        = self.add(npyscreen.TitleFilenameCombo, begin_entry_at=19, name="deploy_conf:", exit_left=True)
        # recover x
        self.start_osd_index    = self.add(npyscreen.TitleText, begin_entry_at=19, name='起始OSD ID:')
        self.ntp_server         = self.add(npyscreen.TitleText, begin_entry_at=19, name='ntp 服务器:')
        self.public_network     = self.add(npyscreen.TitleText, begin_entry_at=19, name='存储外网网段:')
        self.cluster_network    = self.add(npyscreen.TitleText, begin_entry_at=19, name='存储内网网段:')
        self.nextrely += 1
        # record y
        self.nextrelx += -30
        self.ny = self.nextrely
        self.data_blk    = self.add(npyscreen.MultiLineEditableBoxed, max_height=11, max_width=40,
                                    name = '数据盘匹配规则:',
                                    values = _tmp_fake_data,
                                    footer = 'OSD blk'
                                   )
        self.nextrely  = self.ny
        self.nextrelx += 45
        self.journal_blk = self.add(npyscreen.MultiLineEditableBoxed, max_height=11, max_width=40,
                                    name = '日志盘匹配规则:',
                                    values = _tmp_fake_data,
                                    footer = 'journal blk'
                                   )
        self.nextrelx -= 45
        self.ip_list   = self.add(MultiLineEditableBoxed_tag_host, max_width=85,
                                  name='monitor主机分布列表:',
                                  values=['0.0.0.0 osd'],
                                  footer='按下 i 或 o 开始编辑')

        self._conf_refreshed = None
        self._loadable_conf_status = {
            'deploy_conf':self.deploy_conf.value,
            'add_mode':   [] + self.add_mode.value,
        }
        self.add_handlers({
            #curses.ascii.ESC: self.exit_func,
            "^Q":             self.exit_func,
            #155:              self.exit_func,
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
        # hidden deploy_conf 
        _target_value = _target_widget.value 
        if 0 in _target_value :
            self.deploy_conf.hidden = False
        else:
            self.deploy_conf.hidden = True

    def check_loadable_conf_status(self):
        if self.deploy_conf.value != self._loadable_conf_status['deploy_conf']:
            self._loadable_conf_status['deploy_conf'] = self.deploy_conf.value
            self._conf_refreshed = True
        #npyscreen.notify(str(self.add_mode.value), title="add_mode")
        #time.sleep(0.25)
        if self.add_mode.value != self._loadable_conf_status['add_mode']:
            self._loadable_conf_status['add_mode'] = [] + self.add_mode.value
            self._conf_refreshed = True

    def when_conf_refreshed(self):
        # load host list along with load deploy config file 
        if 1 in self.add_mode.value:
            _selected_host_list = list(
                map(
                    lambda x : str(x.get_content()) + ' osd',
                    self.parentApp.MainForm.GroupTreeBoxObj.get_selected_objects(node_type='host')
                )
            )
            if npyscreen.notify_yes_no("加载主机.." + str(_selected_host_list), title="自动加载"):
                self.ip_list.values = _selected_host_list
        # load config file 
        pass

    #def while_editing(self, z):
    def adjust_widgets(self):
        self.check_loadable_conf_status()
        if self._conf_refreshed:
            self.when_conf_refreshed()
            self._conf_refreshed = None

    def check_deploy_settings(self):
        npyscreen.notify('检查 部署配置', title='检查函数正常:')

        pass
        #self.grp_name.value = str(self.grp_name.value).strip().replace(' ', '_')

        ## ip list 
        #if isinstance(self.ip_list.value, str):
        #    # to be changed  when  new contained widget is ready  
        #    self.ip_list.values = _nodes_to_add = self.ip_list.values.split()
        #    if not npyscreen.notify_yes_no('请注意IP地址使用换行符进行分割, 请确认格式化结果!' + '\n'.join(_nodes_to_add), title='IP格式异常:'):
        #        return False
        #else:
        #    _nodes_to_add = self.ip_list.values 

        #if len(self.grp_user.value.strip()) == 0:
        #    self.grp_user.value = None
        #if len(self.grp_pswd.value.strip()) == 0:
        #    self.grp_pswd.value = None
        #if len(self.grp_key.value.strip()) == 0:
        #    self.grp_key.value = None 

    def auto_deploy(self):
        npyscreen.notify('正在检查信息...', title='准备部署:')
        time.sleep(0.5)
        if self.check_deploy_settings():
            pass 
        #    _ssh_info = {
        #        'prot':     int(self.grp_port.value),
        #        'user':     self.grp_user.value,
        #        'password': self.grp_pswd.value,
        #        'timeout':  int(self.conTimeout.value),
        #        'hostkey':  self.grp_key.value
        #    }
        #    self.parentApp.MainForm.GroupTreeBoxObj.add_grp(name=self.grp_name.value, nodes=self.ip_list.values, ssh_info=_ssh_info)
        #    self.parentApp.setNextForm('MAIN')

    def on_ok(self):
        self.auto_deploy()

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
