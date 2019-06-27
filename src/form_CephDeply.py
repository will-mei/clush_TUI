#!/usr/bin/env python
# coding=utf-8

import time
import curses
from src import npyscreen

_tmp_fake_data = ['接口类型 sata/sas/nvme',
                  '磁盘类型 hdd/ssd',
                  '容量大于(GB) xx',
                  '容量小于(GB) xx',
                  '设备名包含 xx',
                  '设备名排除 xx',
                  '厂商信息包含 xx',
                  '产品型号包含 xx',
                  '磁盘数量 xx',
                 ]

_tmp_fake_blk_info_set = {
    'interface': ['sata', 'sas', 'nvme'],
    'disk_type': ['hdd', 'ssd'],
    'disk_size': ['447.1', '558.9','1843.2', '5632'],
    'vendor':    ['Intel Corporation','Vendor 0x1c5f Device 0x0540', 'sugon', 'huawei'],
    'product_version':['HGST HUS726040AL', 'INTEL SSDSC2KB48', 'P45C7016D22', 'ST6000NM0115-1YZ'],
}


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
        self.name = '预配置新的ceph集群:'
        # record y
        self.ny = self.nextrely
        self.add_mode = self.add(npyscreen.TitleMultiSelect, begin_entry_at=16, name='部署选项', max_height=3, field_width=42,
                                 value=[0,],
                                 values=["加载集群部署配置", "加载已选主机节点", "连接到已有集群并扩容"],
                                 value_changed_callback=self.value_changed_callback,
                                 exit_right=True,
                                 scroll_exit=True)
        # recover y, move right: + x
        self.nextrely = self.ny
        self.nextrelx += 50
        self.deploy_conf        = self.add(npyscreen.TitleFilenameCombo, begin_entry_at=19, name="deploy_conf:", exit_left=True)
        # recover x
        self.start_osd_index    = self.add(npyscreen.TitleText, begin_entry_at=19, name='起始OSD ID:')
        self.ntp_server         = self.add(npyscreen.TitleText, begin_entry_at=19, name='ntp 服务器:')
        self.public_network     = self.add(npyscreen.TitleText, begin_entry_at=19, name='存储外网网段:')
        self.cluster_network    = self.add(npyscreen.TitleText, begin_entry_at=19, name='存储内网网段:')
        self.nextrely += 1
        # record y
        self.nextrelx -= 40
        self.filter = self.add(npyscreen.GridColTitles,
                               column_width=36,
                               width=80,
                               col_titles = ['数据磁盘匹配项','日志盘匹配项'], max_height=2, editable=False)
        self.ny = self.nextrely
    #    self.data_blk    = self.add(npyscreen.MultiLineEditableBoxed, max_height=12, max_width=40,
    #                                name = '数据盘匹配规则:',
    #                                values = _tmp_fake_data,
    #                                footer = 'OSD blk'
    #                               )
        self.data_blk_size_ge = self.add(npyscreen.TitleText, name='容量下限', max_width=40)
        self.data_blk_size_le = self.add(npyscreen.TitleText, name='容量上限', max_width=40)
        self.data_blk_count  = self.add(npyscreen.TitleText, name='磁盘数量', max_width=40, value='12')
        self.data_blk_name   = self.add(npyscreen.TitleText, name='匹配名称', max_width=40, value='/dev/sd')
        self.data_blk_ex     = self.add(npyscreen.TitleText, name='排除名称', max_width=40, value='/dev/sda')
        self.data_blk_if     = self.add(npyscreen.TitleCombo, name='类型描述', max_width=40, values=['SCSI Disk', 'ATA Disk'], value=1) # value, values  
        self.data_blk_type   = self.add(npyscreen.TitleCombo, name='磁盘类型', max_width=40, values=['机械硬盘', '固态硬盘'], value=0) # value, values  
        #self.data_blk_vendor = self.add(npyscreen.TitleCombo, name='设备厂商', max_width=40)
        #self.data_blk_model  = self.add(npyscreen.TitleCombo, name='产品型号', max_width=40) # value, values  
        self.nextrely  = self.ny
        self.nextrelx += 40
        #self.journal_blk = self.add(npyscreen.MultiLineEditableBoxed, max_height=12, max_width=40,
        #                            name = '日志盘匹配规则:',
        #                            values = _tmp_fake_data,
        #                            footer = 'journal blk'
        #                           )
        self.journal_blk_size_ge = self.add(npyscreen.TitleText, name='容量下限') #, begin_entry_at=11)
        self.journal_blk_size_le = self.add(npyscreen.TitleText, name='容量上限')
        self.journal_blk_count  = self.add(npyscreen.TitleText, name='磁盘数量', value='2')
        self.journal_blk_name   = self.add(npyscreen.TitleText, name='匹配名称', value='/dev/nvme')
        self.journal_blk_ex     = self.add(npyscreen.TitleText, name='排除名称')
        self.journal_blk_if     = self.add(npyscreen.TitleCombo, name='类型描述', values=['ATA Disk', 'SCSI Disk'], value=0) # value, values  
        self.journal_blk_type   = self.add(npyscreen.TitleCombo, name='磁盘类型', values=['机械硬盘', '固态硬盘'], value=1) # value, values  
        #self.journal_blk_vendor = self.add(npyscreen.TitleCombo, name='设备厂商')
        #self.journal_blk_model  = self.add(npyscreen.TitleCombo, name='产品型号') # value, values  
        self.nextrely += 2
        self.ny =self.nextrely 

        self.nextrelx -= 45
        self.ip_list   = self.add(MultiLineEditableBoxed_tag_host,
                                  max_width=45,
                                  name='monitor主机分布列表:',
                                  values=['0.0.0.0 osd'],
                                  footer='使用空格开始编辑, 使用左右键调整节点类型')
        self.nextrely = self.ny 
        self.nextrelx += 45
        self.check_list = self.add(MultiLineEditableBoxed_tag_host,
                                  max_width=45,
                                  name='自动检测结果:',
                                  values=['0.0.0.0 ok'],
                                  footer='使用 Ctrl + t 刷新检测结果')

        self._opt_refreshed = None
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
        self.deploy_settings_ready = None

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
    def check_deploy_opt_status(self):
        #npyscreen.notify(str(self.add_mode.value), title="add_mode")
        #time.sleep(0.25)
        if self.add_mode.value != self._loadable_conf_status['add_mode']:
            self._loadable_conf_status['add_mode'] = [] + self.add_mode.value
            self._opt_refreshed = True

    def when_conf_refreshed(self):
        # load config file 
        import os
        import configparser
        if os.path.isfile(self.deploy_conf.value):
            try:
                config = configparser.ConfigParser()
                config.read(self.deploy_conf.value)
                self.ntp_server.value       = config['deploy']['ntp_server']
                self.start_osd_index.value  = config['deploy']['start_osd_id']
                self.public_network.value   = config['deploy']['public_network']
                self.cluster_network.value  = config['deploy']['cluster_network']
                self.display()
            except:
                npyscreen.notify_confirm('无法加载配置文件:\n' + str(self.deploy_conf.value) + '...', title="读取失败")
        pass

    def when_opt_refreshed(self):
        # load host list along with load deploy config file 
        if 1 in self.add_mode.value:
            _selected_host_list = list(
                map(
                    lambda x : str(x.get_content()) + ' osd',
                    self.parentApp.MainForm.GroupTreeBoxObj.get_selected_objects(node_type='host')
                )
            )
            if len(_selected_host_list):
                if npyscreen.notify_yes_no("加载主机:\n" + str(_selected_host_list), title="确认加载"):
                    self.ip_list.values = _selected_host_list
                    self.display()
            else:
                npyscreen.notify_confirm("没有选中的节点,\n你可以退回主界面重新选取需要的主机.", title="未能加载")

    #def while_editing(self, z):
    def adjust_widgets(self):

        self.check_loadable_conf_status()
        if self._conf_refreshed:
            self.when_conf_refreshed()
            self._conf_refreshed = None

        self.check_deploy_opt_status()
        if self._opt_refreshed:
            self.when_opt_refreshed()
            self._opt_refreshed = None

    def check_deploy_settings(self):
        npyscreen.notify('检查 部署配置', title='检查函数正常:')
        time.sleep(2)

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
