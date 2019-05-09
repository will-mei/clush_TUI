#!/usr/bin/env python
# coding=utf-8
import curses
from . import npyscreen


help_info = {
    "切换到下一控件:":'Tab', #  或  ^I (Ctrl + i)',
    "切换到上一控件:":'Shift +Tab',
    "刷新当前的屏幕:":'Ctrl + l',
    "退出应用程序  :":'Esc  或  Ctrl + c  或 Ctrl + g',
    "折叠主机组列表:":'<  或  [  或 h',
    "展开主机组列表:":'>  或  ]  或 l',
    "折叠全部主机组:":'{',
    "展开全部主机组:":'}',
    "转到下一行文本:":'j  或  <下方向键>',
    "转到上一行文本:":'k  或  <上方向键>',
    "转到文本页开头:":'g',
    "转到文本页末尾:":'G',
    "搜索文本页内容:":'l',
    "清空搜索筛选项:":'L',
    "转到下一匹配项:":'n',
    "转到上一匹配项:":'N  或 p',
    "编辑当前行文本:":'a  或  <空格>  或  <Enter>  或  <Insert>',
    "插入新行到文本:":'i (插入到上一行)  或  o (插入到下一行)',
    "删除当前行文本:":'D  或  <Delete>  或  <Backspace> (删除键)'
}

#class HelpForm(npyscreen.ActionFormV2):
class HelpForm(npyscreen.ActionFormMinimal):
    def create(self):
        # Attribute 
        self.name = '帮助'
        #self.DEFAULT_X_OFFSET = 0
        #self.BLANK_COLUMNS_RIGHT = 0

        n = 0
        for i, j in help_info.items():
            self.help = self.add(npyscreen.TitleText, begin_entry_at=20, editable=False, name=i, value=j)
            self.nextrely += 1
    def afterEditing(self):
        self.parentApp.setNextForm('MAIN')


