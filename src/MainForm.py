import os
import time
import curses
import configparser
from datetime import timedelta

from src import npyscreen as npyscreen
from src import treeBox
from src import msgInfoBox
from src import statusInfoBox
from src import inputBox

# just some example test ip list
ip_list1 = [ '192.168.100.' + str(x)  for x in range(201, 206)]
ip_list2 = [ '192.168.100.' + str(x)  for x in range(206, 211)]
ip_list3 = [ '192.168.100.' + str(x)  for x in range(211, 216)]

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
            ('添加新的主机组',  self.add_grp,       "^A"),
            ('显示帮助页面',    self.show_help,     "^H"),
            ('切换命令行模式',  self.mode_switch,   "^N"),
            #('临时debug消息',   self._debug_msg,    "^D"),
            ('中断任务并退出',  self.confirm_abort, "^I"),
            ('正常关闭退出',    self.safe_exit,     "^Q")
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
        self.GroupTreeBoxObj = self.add(treeBox.HostGroupTreeBox, name="主机组", max_width=28, scroll_exit=True) #, value=0, relx=1, max_width=x // 5, rely=2,

        # top , 28 right 
        self.nextrely = ny
        self.nextrelx = nx + 28
        x_half = int((x - 28) / 2 -5)
        self.statusInfoBoxObj = self.add(statusInfoBox.statusBox, name="状态", footer='正在运行作业主机数:0', values=['状态临时信息1', '状态临时信息2', '状态临时信息3'], max_height=5, max_width=x_half, contained_widget_arguments={'maxlen':3}, exit_left=True, exit_right=True, scroll_exit=True, editable=False)
        self.nextrely = ny
        self.nextrelx = nx + 28 + x_half
        self.statusInfoBoxObj2 = self.add(statusInfoBox.statusBox, name="负载", footer='命令行模式: 本地shell', values=['主机负载1 xx xx xx ', '主机负载2 xx xx xx ', '主机负载3 xx xx xx'], max_height=5, contained_widget_arguments={'maxlen':3}, exit_left=True, exit_right=True, scroll_exit=True, editable=False)
        self.nextrelx = nx + 28
        self.msgInfoBoxObj = self.add(msgInfoBox.InfoBox, name="滚动消息", max_height=-5, footer=' l 搜索并高亮显示, L 取消高亮显示') #, contained_widget_arguments={'maxlen':msg_buffer})
        self.inputBoxObj = self.add(inputBox.InputBox, name="输入", footer='Tab/鼠标 切换窗口, Alt + Enter 换行', scroll_exit=False)

        # 添加部分示例数据到主机列表
        npyscreen.notify('添加示例主机组', title='测试消息')
        time.sleep(0.5)
        self.GroupTreeBoxObj.add_grp(name='group1', nodes=ip_list1)
        self.GroupTreeBoxObj.add_grp(name='group2', nodes=ip_list2)
        self.GroupTreeBoxObj.add_grp(name='group3', nodes=ip_list3)

        # init handlers, if no widget handle this, they will be handled here
        new_handlers = {
            # exit
            #curses.ascii.CAN: self.exit_func, # chaos 
            curses.ascii.BEL: self.exit_func,
            #curses.ascii.DLE: self.exit_func, # works fine, but not needed any more 
            curses.ascii.ESC: self.exit_func,
            #"^C": self.exit_func, #doesn't work
            155: self.exit_func,
            # send command
            curses.ascii.CR: self.send_command,
            curses.ascii.NL: self.send_command,
            curses.KEY_ENTER : self.send_command,
            # send file
            #"^O": self.file_distrbution,
            "^T": self.test_func,
        }
        self.add_handlers(new_handlers)


    #def while_editing(self,*args, **keywords):
    #    self.msgInfoBoxObj.display()

    # events
    def event_target_select(self, event):
        target_hosts = self.chatBoxObj.value
        #client.dialogs[current_user].unread_count = 0

##        self.chatBoxObj.update_chat()
##        self.messageBoxObj.update_messages(current_user)
##        client.read_all_messages(current_user)

##    def event_messagebox_change_cursor(self, event):
##        current_user = self.chatBoxObj.value
##        messages = self.messageBoxObj.get_messages_info(current_user)
##        date = messages[len(messages) - 1 - self.messageBoxObj.entry_widget.cursor_line].date
##
##        self.messageBoxObj.footer = str(date + (timedelta(self.timezone) // 24))
##        self.messageBoxObj.update()

    # handling methods
    def mode_switch(self):
        if self.shell_mode == 'local':
            self.shell_mode = 'cluster'
        else:
            self.shell_mode = 'local'

        self.statusInfoBoxObj2.footer = '命令行模式: ' + self.shell_mode 
        self.msgInfoBoxObj.append_msg('模式切换到:' + self.shell_mode)

    #def message_send(self, event):
    def send_command(self, event):
        #current_user = self.chatBoxObj.value
        message = self.inputBoxObj.value.strip()
        if message is not "":
            #client.message_send(message, current_user)
            #self.messageBoxObj.update_messages(current_user)
            self.msgInfoBoxObj.append_msg(message)

            self.inputBoxObj.value = ""
            self.inputBoxObj.display()
            self.msgInfoBoxObj.display()

    def event_update_main_form(self, event):
        self.display()
        self.msgInfoBoxObj.display()

    def _debug_msg(self):
        _selected_nodes = list(self.GroupTreeBoxObj.get_selected_objects())

        _selected_hosts = list(map(lambda x : str(x.get_content()) + ' ' + str(x.get_parent().get_content()), filter(lambda x : x.marker == 'host', _selected_nodes)))
        self.msgInfoBoxObj.append_msg(_selected_hosts)

        _selected_groups = list(map(lambda x : str(x.get_content()) + ' ' + str(x.ssh_info) , filter(lambda x : x.marker == 'group', _selected_nodes)))
        self.msgInfoBoxObj.append_msg(_selected_groups)
        #self.msgInfoBoxObj.append_msg(list(_selected_nodes))

        #_tmp_list = list(map(lambda x : x.marker ,  self.GroupTreeBoxObj.get_selected_objects() ))
        #self.msgInfoBoxObj.append_msg(_tmp_list)
        #npyscreen.notify_confirm(str(_tmp_list), title='debug notification')


    def confirm_abort(self):
        if npyscreen.notify_yes_no('确定要取消任务并退出吗?', title='确认终止:'):
            # some staff of killing sessions
            exit(0)

    def safe_exit(self):
        if npyscreen.notify_yes_no('确定要退出吗?', title='确认退出:'):
            # some thing to check before exit 
            exit(0)

    def exit_func(self, _input):
        self.safe_exit()

    def _cancel_signal(self, *args, **keywords):
        # check wdget on editing
        # abort 
        self.safe_exit()

    def show_help(self):
        self.parentApp.switchForm('HelpForm')

    def add_grp(self):
        self.parentApp.switchForm('HostGroupForm')

    #def send_command(self, _input):
    #    pass 

    def search_message(self, _input):
        pass

    def file_distrbution(self):
        pass 

    def file_collection(self):
        pass 

    def test_func(self, _input):
        #l = self.inputBoxObj.handlers
        #for i,j in l.items():
        #    self.msgInfoBoxObj.append_msg(str(i) + str(j))
        #for i in dir(self.inputBoxObj):
        #    self.msgInfoBoxObj.append_msg(str(i))
        self.msgInfoBoxObj.append_msg(self.inputBoxObj.entry_widget.parent.name)
        self._debug_msg()
        self.msgInfoBoxObj.append_msg(self._widgets__)
        #self.msgInfoBoxObj.display()

    # update loop
    def while_waiting(self):
        pass 

##        current_user = self.chatBoxObj.value
##
##        client.client.sync_updates()
##        if client.need_update_message:
##            if client.need_update_current_user == current_user:
##                self.messageBoxObj.update_messages(current_user)
##                client.read_all_messages(current_user)
##                client.dialogs[current_user].unread_count = 0
##
##            self.chatBoxObj.update_chat()
##            client.need_update_message = 0
##            client.need_update_current_user = -1
##
##        if client.need_update_online:
##            if client.need_update_current_user == current_user:
##                self.messageBoxObj.update_messages(current_user)
##            self.chatBoxObj.update_chat()
##            client.need_update_current_user = -1
##            client.need_update_online = 0
##
##        if client.need_update_read_messages:
##            if client.need_update_current_user == current_user:
##                self.messageBoxObj.update_messages(current_user)
##            client.need_update_current_user = -1
##            client.need_update_read_messages = 0
