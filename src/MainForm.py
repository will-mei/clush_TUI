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
#from src import functionalBox


ip_list1 = [ '192.168.100.' + str(x)  for x in range(201, 204)]
ip_list2 = [ '192.168.100.' + str(x)  for x in range(205, 214)]

class MainForm(npyscreen.FormBaseNewWithMenus):

    #def __init__(self, *args, **keywords):
    #    super().__init__(*args, **keywords)
    #    super().__init__(*args, **keywords)
    #    self.menu_advert_text = ': 使用 Ctrl + x 打开管理菜单 '
    #    self.initialize_menus()
    
    def draw_form(self):
        super(npyscreen.FormBaseNewWithMenus, self).draw_form()
        super().draw_form()
        menu_advert = " " + self.__class__.MENU_KEY + ': 使用 Ctrl + x 打开管理菜单 '
        if isinstance(menu_advert, bytes):
            menu_advert = menu_advert.decode('utf-8', 'replace')
        y, x = self.display_menu_advert_at()
        self.add_line(y, x, 
            menu_advert, 
            self.make_attributes_list(menu_advert, curses.A_NORMAL),
            self.columns - x - 1
            )

    def create(self):
        self.name = '集群作业管理器(TUI)'
        # menus 
        self.main_menu = self.new_menu(name='主菜单:')
        self.main_menu.addItemsFromList([
            ('添加新组', self.add_grp, "^A"),
            ('显示帮助', self.show_help, "^H"),
            ('debug消息', self._debug_msg, "^D"),
            ('中断退出', self.confirm_exit, "^I"),
            ('正常退出', self.exit_app, "^Q")
        ])
        # Events

##        # import config settings
##        config = configparser.ConfigParser()

        # window size
        y, x = self.useable_space()

        # create ui form
        ny = self.nextrely
        nx = self.nextrelx
        self.GroupTreeBoxObj = self.add(treeBox.HostGroupTreeBox, name="主机组", max_width=28) #, value=0, relx=1, max_width=x // 5, rely=2,

        self.nextrely = ny
        self.nextrelx = nx + 28
        self.statusInfoBoxObj = self.add(statusInfoBox.statusBox, name="状态", max_height=5, footer='正在运行作业主机数:0') #, value=0, relx=1, max_width=x // 5, rely=2,
        self.msgInfoBoxObj = self.add(msgInfoBox.InfoBox, name="滚动消息", max_height=-5) #, value=0, relx=1, max_width=x // 5, rely=2,
        self.InputBoxObj = self.add(inputBox.InputBox, name="输入") #, value=0, relx=1, max_width=x // 5, rely=2,

        # 添加部分示例数据到主机列表
        npyscreen.notify('添加示例主机组', title='测试消息')
        time.sleep(0.5)
        self.GroupTreeBoxObj.add_grp(name='group1', nodes=ip_list1)
        self.GroupTreeBoxObj.add_grp(name='group2', nodes=ip_list2)
##                                   max_height=-5)
##        self.chatBoxObj.create(emoji=self.emoji)
##
##        self.messageBoxObj = self.add(messageBox.MessageBox, rely=2, relx=(x // 5) + 1, max_height=-5, editable=True,
##                                      custom_highlighting=True, highlighting_arr_color_data=[0])
##        self.messageBoxObj.create(emoji=self.emoji, aalib=self.aalib)
##
##        self.FunctionalBox = self.add(functionalBox.FunctionalBox, name="Other", value=0, relx=1, max_width=x // 5,
##                                      max_height=-5, )
##        self.FunctionalBox.values = ["🕮  Contacts"] if self.emoji else ["Contacts"]
##
##        self.inputBoxObj = self.add(inputBox.InputBox, name="Input", relx=(x // 5) + 1, rely=-7)
##
        # inti handlers
        new_handlers = {
            # exit
            #"^Q": self.exit_func,
##            155: self.exit_func,
            curses.ascii.ESC: self.confirm_exit,
##            # send message
            "^C": self.confirm_exit,
##            curses.ascii.alt(curses.ascii.NL): self.message_send,
##            curses.ascii.alt(curses.KEY_ENTER): self.message_send,
##            # forward message
##            "^F": self.forward_message,
##            # delete message
##            "^R": self.remove_message,
##            # delete message
##            "^D": self.download_file,
##            # send file
##            "^O": self.file_send
        }
##        self.add_handlers(new_handlers)
##
##        # fill first data
##        self.messageBoxObj.update_messages(0)
##        self.chatBoxObj.update_chat()
##
##    # events
##    def event_chat_select(self, event):
##        current_user = self.chatBoxObj.value
##        client.dialogs[current_user].unread_count = 0
##
##        self.chatBoxObj.update_chat()
##        self.messageBoxObj.update_messages(current_user)
##
##        client.read_all_messages(current_user)
##
##    def event_messagebox_change_cursor(self, event):
##        current_user = self.chatBoxObj.value
##        messages = self.messageBoxObj.get_messages_info(current_user)
##        date = messages[len(messages) - 1 - self.messageBoxObj.entry_widget.cursor_line].date
##
##        self.messageBoxObj.footer = str(date + (timedelta(self.timezone) // 24))
##        self.messageBoxObj.update()
##
##    # handling methods
##    def message_send(self, event):
##        current_user = self.chatBoxObj.value
##        message = self.inputBoxObj.value.strip()
##        if message is not "":
##            client.message_send(message, current_user)
##            self.messageBoxObj.update_messages(current_user)
##
##            self.inputBoxObj.value = ""
##            self.inputBoxObj.display()
##    def download_file(self, event):
##        pass
##
##    def event_update_main_form(self, event):
##        self.display()
##        self.messageBoxObj.display()
##        self.chatBoxObj.display()
##
##    def exit_func(self, _input):
##        exit(0)

    def exit_app(self):
        exit(0)

    def confirm_exit(self):
        if npyscreen.notify_yes_no('确定要取消任务并退出吗?', title='确认退出:'):
            self.exit_app()

    def add_grp(self):
        self.parentApp.switchForm('HostGroupForm')

    def show_help(self):
        self.parentApp.switchForm('HelpForm')

    def _debug_msg(self):
        _tmp_info = list(self.GroupTreeBoxObj.get_selected_objects())
        npyscreen.notify_confirm(str(_tmp_info), title='debug notification')

##    # update loop
##    def while_waiting(self):
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
