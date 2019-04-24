#!/usr/bin/env python
# coding=utf-8
import curses
from . import npyscreen

#class HelpForm(npyscreen.ActionFormV2):
class HelpForm(npyscreen.ActionFormMinimal):
    def create(self):
        # Attribute 
        self.name = '帮助'
        #self.DEFAULT_X_OFFSET = 0
        #self.BLANK_COLUMNS_RIGHT = 0

        self.help1 = self.add(npyscreen.TitleText, begin_entry_at=20, editable=False, name="折叠主机组列表:", value='<  或  [  或 h')
        self.help2 = self.add(npyscreen.TitleText, begin_entry_at=20, editable=False, name="展开主机组列表:", value='>  或  ]  或 l')
        self.help2 = self.add(npyscreen.TitleText, begin_entry_at=20, editable=False, name="折叠全部主机组:", value='{')
        self.help2 = self.add(npyscreen.TitleText, begin_entry_at=20, editable=False, name="展开全部主机组:", value='}')
        self.help2 = self.add(npyscreen.TitleText, begin_entry_at=20, editable=False, name="切换到下一控件:", value='Tab  或  ^I (Ctrl + i)')
        self.help2 = self.add(npyscreen.TitleText, begin_entry_at=20, editable=False, name="切换到上一控件:", value='Shift +Tab')
        self.help2 = self.add(npyscreen.TitleText, begin_entry_at=20, editable=False, name="刷新当前的屏幕:", value='Ctrl + l')
    def afterEditing(self):
        self.parentApp.setNextForm('MAIN')


