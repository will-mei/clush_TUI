#!/usr/bin/python
import curses
import curses.ascii
import sys
import locale
#import curses.wrapper
from . import wgwidget as widget
from . import npysGlobalOptions as GlobalOptions

# tools to calculate the right width of characters 
from . import char_width_tools


class TextfieldBase(widget.Widget):
    ENSURE_STRING_VALUE = True

    def __init__(self, screen, value='', highlight_color='CURSOR', highlight_whole_widget=False,
        invert_highlight_color=True,
        **keywords):

        # need to be rewrite 
        self.char_dic_of_cursor = {0:0}
        self.multiline_text = False 
        try:
            if isinstance(value, str):
                self.update_value_text(value)
            else:
                self.value = value or ""
        except:
            self.value = ""

        super(TextfieldBase, self).__init__(screen, **keywords)

        if GlobalOptions.ASCII_ONLY or locale.getpreferredencoding() == 'US-ASCII':
            self._force_ascii = True
        else:
            self._force_ascii = False
        
        self.cursor_position = False
        
        self.highlight_color = highlight_color
        self.highlight_whole_widget = highlight_whole_widget
        self.invert_highlight_color = invert_highlight_color
        self.show_bold = False
        self.highlight = False
        self.important = False
        
        self.syntax_highlighting = False
        self._highlightingdata   = None
        self.left_margin = 0
        
        self.begin_at = 0   # Where does the display string begin?
                            # string offset on column 
    
        self.cal_text_width()
        self.check_text_width()
        self.update()

    def update_value_text(self, tx):
        # remove unprintable char 
        self.value = char_width_tools.get_printable(tx)
        self.char_dic_of_cursor = char_width_tools.gen_tx_cursor_array(self.value)

    def check_text_width(self):
        if isinstance(self.value, str) and char_width_tools.get_str_width(self.value) > self.maximum_content_width :
            self.multiline_text = True 
        else:
            self.multiline_text = False 

    def cal_text_width(self):
        if self.on_last_line:
            # available width for str 
            #self.maximum_content_width = self.width - 2  # Leave room for the cursor
            self.maximum_content_width = self.max_width - 2  # Leave room for the cursor
        else:   
            #self.maximum_content_width = self.width - 1  # Leave room for the cursor at the end of the string.
            self.maximum_content_width = self.max_width - 1  # Leave room for the cursor at the end of the string.

    def resize(self):
        self.cal_text_width()
        self.check_text_width()

    
    def calculate_area_needed(self):
        "Need one line of screen, and any width going"
        return 1,0

    def update(self, clear=True, cursor=True):
        """Update the contents of the textbox, without calling the final refresh to the screen"""
        # cursor not working. See later for a fake cursor
        #if self.editing: pmfuncs.show_cursor()
        #else: pmfuncs.hide_cursor()

        # Not needed here -- gets called too much!
        #pmfuncs.hide_cursor()
        
        if clear: self.clear()
        
        if self.hidden:
            return True
        
        value_to_use_for_calculations = self.value        
        
        if self.ENSURE_STRING_VALUE:
            if value_to_use_for_calculations in (None, False, True):
                value_to_use_for_calculations = ''
                self.value = ''

        if self.begin_at < 0: self.begin_at = 0
        
        if self.left_margin >= self.maximum_content_width:
            raise ValueError( str(self.left_margin) + str(self.maximum_content_width ))
        
        if self.editing:
            if self.value:
                if isinstance(self.value, str):
                    _str_with = char_width_tools.get_str_width(self.value)
                elif isinstance(self.value, bytes):
                    # use a unicode version of self.value to work out where the cursor is.
                    # not always accurate, but better than the bytes
                    value_to_use_for_calculations = self.get_printable(self.value).decode(self.encoding, 'replace')
                    # it's accurate now. 
                    _str_with = char_width_tools.get_str_width(value_to_use_for_calculations)
                else:
                    _str_with = len(value_to_use_for_calculations)
            else:
                _str_with = 0

            # if focused 
            if cursor:
                # set cursor_position to the end of text, get ready to add new 
                if self.cursor_position is False:
            #        self.cursor_position = len(value_to_use_for_calculations)
                    self.cursor_position = _str_with

            #    elif self.cursor_position > len(value_to_use_for_calculations):
                elif self.cursor_position > _str_with:
                    self.cursor_position = _str_with
            #        self.cursor_position = len(value_to_use_for_calculations)

                elif self.cursor_position < 0:
                    self.cursor_position = 0

                if self.cursor_position < self.begin_at:
                    self.begin_at = self.cursor_position

                while self.cursor_position > self.begin_at + self.maximum_content_width - self.left_margin: # -1:
                    self.begin_at += 1
            # set theme when not selected 
            else:
                if self.do_colors():
                    self.parent.curses_pad.bkgdset(' ', self.parent.theme_manager.findPair(self, self.highlight_color) | curses.A_STANDOUT)
                else:
                    self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)



        # Do this twice so that the _print method can ignore it if needed.
        if self.highlight:
            if self.do_colors():
                if self.invert_highlight_color:
                    attributes=self.parent.theme_manager.findPair(self, self.highlight_color) | curses.A_STANDOUT
                else:
                    attributes=self.parent.theme_manager.findPair(self, self.highlight_color)
                self.parent.curses_pad.bkgdset(' ', attributes)
            else:
                self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)
            

        if self.show_bold:
            self.parent.curses_pad.attron(curses.A_BOLD)
        if self.important and not self.do_colors():
            self.parent.curses_pad.attron(curses.A_UNDERLINE)


        self._print()
        
        
        

        # reset everything to normal
        self.parent.curses_pad.attroff(curses.A_BOLD)
        self.parent.curses_pad.attroff(curses.A_UNDERLINE)
        self.parent.curses_pad.bkgdset(' ',curses.A_NORMAL)
        self.parent.curses_pad.attrset(0)
        if self.editing and cursor:
            self.print_cursor()
    
    # define this for update cursor position 
    def get_value_char_under_cursor(self):
        if isinstance(self.value, str):
            for i, cur in self.char_dic_of_cursor.items() :
                if self.cursor_position >= cur:
                    return value[i] 
        else:
            char = ' '
            return char 

    # print char based on cursor_position 
    def print_cursor(self):
        # This needs fixing for Unicode multi-width chars.

        # Cursors do not seem to work on pads.
        #self.parent.curses_pad.move(self.rely, self.cursor_position - self.begin_at)
        # let's have a fake cursor
        _cur_loc_x = self.cursor_position - self.begin_at + self.relx + self.left_margin
        # The following two lines work fine for ascii, but not for unicode
        #char_under_cur = self.parent.curses_pad.inch(self.rely, _cur_loc_x)
        #self.parent.curses_pad.addch(self.rely, self.cursor_position - self.begin_at + self.relx, char_under_cur, curses.A_STANDOUT)
        #The following appears to work for unicode as well.
    #    try:
    #        #char_under_cur = self.value[self.cursor_position] #use the real value
    #        char_under_cur = self._get_string_to_print()[self.cursor_position]
    #        char_under_cur = self.safe_string(char_under_cur)
    #    except IndexError:
    #        char_under_cur = ' '
    #    except TypeError:
    #        char_under_cur = ' '

        # adjust double width characters 
        # this code works fine with double width characters (eg. chinese)
        char_under_cur = self.get_value_char_under_cursor()
        char_under_cur_width = char_width_tools.get_width_of_char(char_under_cur)
        if self.begin_at == 0:
            _double_width_adjust = 0
        elif char_under_cur_width == 2:
            _double_width_adjust = 1 
        else:
            _double_width_adjust = 0
        if self.do_colors():
            self.parent.curses_pad.addstr(self.rely,
                                          self.cursor_position - self.begin_at + self.relx + self.left_margin + _double_width_adjust,
                                          char_under_cur,
                                          self.parent.theme_manager.findPair(self, 'CURSOR_INVERSE'))
        else:
            self.parent.curses_pad.addstr(self.rely,
                                          self.cursor_position - self.begin_at + self.relx + self.left_margin + _double_width_adjust,
                                          char_under_cur,
                                          curses.A_STANDOUT)
            

    def print_cursor_pre_unicode(self):
        # Cursors do not seem to work on pads.
        #self.parent.curses_pad.move(self.rely, self.cursor_position - self.begin_at)
        # let's have a fake cursor
        _cur_loc_x = self.cursor_position - self.begin_at + self.relx + self.left_margin
        # The following two lines work fine for ascii, but not for unicode
        #char_under_cur = self.parent.curses_pad.inch(self.rely, _cur_loc_x)
        #self.parent.curses_pad.addch(self.rely, self.cursor_position - self.begin_at + self.relx, char_under_cur, curses.A_STANDOUT)
        #The following appears to work for unicode as well.
        try:
            char_under_cur = self.get_printable(self.value)[self.cursor_position]
        except:
            char_under_cur = ' '
        # adjust double width characters 
        # this code works fine with double width characters (eg. chinese)
        char_under_cur_width = char_width_tools.get_width_of_char(char_under_cur)
        if self.begin_at == 0:
            _double_width_adjust = 0
        elif char_under_cur_width == 2:
            _double_width_adjust = 1 
        else:
            _double_width_adjust = 0

        self.parent.curses_pad.addstr(self.rely,
                                      self.cursor_position - self.begin_at + self.relx + self.left_margin + _double_width_adjust,
                                      char_under_cur,
                                      curses.A_STANDOUT)
        

    # return the value to display 
    #def display_value(self, value):
    def get_printable(self, value):
        if value == None:
            return ''
        else:
            try:
                str_value = value 
            except UnicodeEncodeError:
                str_value = self.safe_string(value)
                return str_value
            except ReferenceError:                
                return ">*ERROR*ERROR*ERROR*<"
            return self.safe_string(str_value)

    
    def find_width_of_char(self, ch):
        return char_width_tools.get_char_width(ch)
    
    def _print_unicode_char(self, ch):
        # return the ch to print.  For python 3 this is just ch
        if self._force_ascii:
            return ch.encode('ascii', 'replace')
        elif sys.version_info[0] >= 3:
            return ch
        else:
            return ch.encode('utf-8', 'strict')
    
    # based on self.begin_at  and width limitation
    def _get_string_to_print(self):
        string_to_print = self.get_printable(self.value)
        if not string_to_print:
            return None
        # to be changed based on scale,  height and width 

        string_to_print = string_to_print[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin]
        
        if sys.version_info[0] >= 3:
            string_to_print = self.get_printable(self.value)[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin]
        else:
            # ensure unicode only here encoding here.
            dv = self.get_printable(self.value)
            if isinstance(dv, bytes):
                dv = dv.decode(self.encoding, 'replace')
            string_to_print = dv[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin]
        return string_to_print
    
    
    def _print(self):
        string_to_print = self._get_string_to_print()
        if not string_to_print:
            return None
        string_to_print = string_to_print[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin]
        
        if sys.version_info[0] >= 3:
            string_to_print = self.get_printable(self.value)[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin]
        else:
            # ensure unicode only here encoding here 
            dv = self.get_printable(self.value)
            if isinstance(dv, bytes):
                dv = dv.decode(self.encoding, 'replace')
            string_to_print = dv[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin]
        
        # the start point of range 
        used_column = 0
        # reset loop index  
        index_of_char = 0
        if self.syntax_highlighting:
            # calculate highlight range 
            # TTTT##xxx|----     (start, end) #:letf_margin x:char |:begin_at _:maximum_string_length T:title
            # TTTT__|_______     begin_at: absolute in global, relative in widget  
            # TTTT|_________  
            self.update_highlighting(start=self.begin_at, end=self.maximum_content_width + self.begin_at - self.left_margin)
            # diskplay each char on available space 
            while used_column <= (self.maximum_content_width - self.left_margin):
                if not string_to_print or index_of_char > len(string_to_print)-1:
                    break
                width_of_char_to_print = self.find_width_of_char(string_to_print[index_of_char])
                # no enough space for more char except the border line 
                if used_column - 1 + width_of_char_to_print > self.maximum_content_width:
                    break 
                try:
                    highlight = self._highlightingdata[self.begin_at + index_of_char]
                except:
                    highlight = curses.A_NORMAL
                # the display action
                self.parent.curses_pad.addstr(self.rely,self.relx + used_column+self.left_margin, 
                    self._print_unicode_char(string_to_print[index_of_char]), 
                    highlight )
                used_column += self.find_width_of_char(string_to_print[index_of_char])
                # update char index, the step must be 1
                index_of_char += 1
        else:
            if self.do_colors():
                if self.show_bold and self.color == 'DEFAULT':
                    color = self.parent.theme_manager.findPair(self, 'BOLD') | curses.A_BOLD
                elif self.show_bold:
                    color = self.parent.theme_manager.findPair(self, self.color) | curses.A_BOLD
                elif self.important:
                    color = self.parent.theme_manager.findPair(self, 'IMPORTANT') | curses.A_BOLD
                else:
                    color = self.parent.theme_manager.findPair(self)
            else:
                if self.important or self.show_bold:
                    color = curses.A_BOLD
                else:
                    color = curses.A_NORMAL

            # print all char 
            while used_column <= (self.maximum_content_width - self.left_margin):
                if not string_to_print or index_of_char > len(string_to_print)-1:
                    if self.highlight_whole_widget:
                        self.parent.curses_pad.addstr(self.rely,self.relx + used_column+self.left_margin, 
                            ' ', 
                            color
                            )
                        used_column += width_of_char_to_print
                        index_of_char += 1
                        continue
                    else:
                        break
                # get the right width 
                width_of_char_to_print = self.find_width_of_char(string_to_print[index_of_char])
                if used_column - 1 + width_of_char_to_print > self.maximum_content_width:
                    break 
                self.parent.curses_pad.addstr(self.rely,self.relx + used_column + self.left_margin, 
                    self._print_unicode_char(string_to_print[index_of_char]), 
                    color
                    )
                used_column += width_of_char_to_print
                index_of_char += 1
    
    
    
    
    
    def _print_pre_unicode(self):
        # This method was used to print the string before we became interested in unicode.
        
        #string_to_print = wide_str(self.get_printable(self.value))
        string_to_print = self.get_printable(self.value)
        if string_to_print == None: return
        
        if self.syntax_highlighting:
            self.update_highlighting(start=self.begin_at, end=self.maximum_content_width + self.begin_at - self.left_margin)
            # 
            for index in range(len(string_to_print[self.begin_at:self.maximum_content_width + self.begin_at-self.left_margin])):
                try:
                    highlight = self._highlightingdata[self.begin_at + index]
                except:
                    highlight = curses.A_NORMAL
                self.parent.curses_pad.addstr(self.rely, self.relx + index + self.left_margin, 
                    string_to_print[self.begin_at + index], 
                    highlight )
        
        elif self.do_colors():
            coltofind = 'DEFAULT'
            if self.show_bold and self.color == 'DEFAULT':
                coltofind = 'BOLD'
            if self.show_bold:
                self.parent.curses_pad.addstr(self.rely,self.relx + self.left_margin,
                                              string_to_print[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin],
                                              self.parent.theme_manager.findPair(self, coltofind) | curses.A_BOLD)
            elif self.important:
                coltofind = 'IMPORTANT'
                self.parent.curses_pad.addstr(self.rely,self.relx + self.left_margin,
                                              string_to_print[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin], 
                                              self.parent.theme_manager.findPair(self, coltofind) | curses.A_BOLD)
            else:
                self.parent.curses_pad.addstr(self.rely,self.relx + self.left_margin,
                                              string_to_print[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin], 
                                              self.parent.theme_manager.findPair(self))
        else:
            if self.important:
                self.parent.curses_pad.addstr(self.rely,self.relx + self.left_margin, 
                        string_to_print[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin], curses.A_BOLD)
            elif self.show_bold:
                self.parent.curses_pad.addstr(self.rely,self.relx + self.left_margin, 
                        string_to_print[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin], curses.A_BOLD)

            else:
                self.parent.curses_pad.addstr(self.rely,self.relx + self.left_margin, 
                    string_to_print[self.begin_at:self.maximum_content_width + self.begin_at - self.left_margin])
    
    def update_highlighting(self, start=None, end=None, clear=False):
        if clear or (self._highlightingdata == None):
            self._highlightingdata = []
        
        string_to_print = self.get_printable(self.value)


class Textfield(TextfieldBase):
    def show_brief_message(self, message):
        curses.beep()
        keep_for_a_moment = self.value
        self.value = message
        self.editing=False
        self.display()
        curses.napms(1200)
        self.editing=True
        self.value = keep_for_a_moment
        

    def edit(self):
        self.editing = 1
        if self.cursor_position is False:
            self.cursor_position = char_width_tools.str_width(self.value or '')
        self.parent.curses_pad.keypad(1)
        
        self.old_value = self.value
        
        self.how_exited = False

        while self.editing:
            self.display()
            self.get_and_use_key_press()

        self.begin_at = 0
        self.display()
        self.cursor_position = False
        return self.how_exited, self.value

    ###########################################################################################
    # Handlers and methods

    def set_up_handlers(self):
        super(Textfield, self).set_up_handlers()    
    
        # For OS X
        del_key = curses.ascii.alt('~')
        
        self.handlers.update({curses.KEY_LEFT:    self.h_cursor_left,
                            curses.KEY_RIGHT:     self.h_cursor_right,
                            curses.KEY_DC:        self.h_delete_right,
                            curses.ascii.DEL:     self.h_delete_left,
                            curses.ascii.BS:      self.h_delete_left,
                            curses.KEY_BACKSPACE: self.h_delete_left,
                            # mac os x curses reports DEL as escape oddly
                            # no solution yet                   
                            "^K":                 self.h_erase_right,
                            "^U":                 self.h_erase_left,
                            })

        self.complex_handlers.extend((
                        (self.t_input_isprint, self.h_addch),
                        # (self.t_is_ck, self.h_erase_right),
                        # (self.t_is_cu, self.h_erase_left),
                        ))

    def t_input_isprint(self, inp):
        if self._last_get_ch_was_unicode and inp not in '\n\t\r':
            return True
        if curses.ascii.isprint(inp) and \
        (chr(inp) not in '\n\t\r'): 
            return True
        else: 
            return False
        
        
    def h_addch(self, inp):
        if self.editable:
            #self.value = self.value[:self.cursor_position] + curses.keyname(input) \
            #   + self.value[self.cursor_position:]
            #self.cursor_position += len(curses.keyname(input))
            
            # workaround for the metamode bug:
            if self._last_get_ch_was_unicode == True and isinstance(self.value, bytes):
                # probably dealing with python2.
                ch_adding = inp
                self.value = self.value.decode()
            elif self._last_get_ch_was_unicode == True:
                ch_adding = inp
            else:
                try:
                    ch_adding = chr(inp)
                except TypeError:
                    ch_adding = input
            #self.value = self.value[:self.cursor_position] + wide_str(ch_adding) \
            self.value = self.value[:self.cursor_position] + ch_adding \
                + self.value[self.cursor_position:]
            self.cursor_position += char_width_tools.str_width(ch_adding)

            # or avoid it entirely:
            #self.value = self.value[:self.cursor_position] + curses.ascii.unctrl(input) \
            #   + self.value[self.cursor_position:]
            #self.cursor_position += len(curses.ascii.unctrl(input))

    def h_cursor_left(self, input):
        # calculate width for current char and move right. 
        #_step = char_width_tools.get_width_of_char(self.get_value_char_under_cursor())
        try:
            _step = char_width_tools.get_width_of_char(self.value[self.cursor_position -1])
        except:
            _step = 1

        #self.cursor_position -= 1
        self.cursor_position -= _step

    def h_cursor_right(self, input):
        # calculate width for current char and move right. 
        #_step = char_width_tools.get_width_of_char(self.get_value_char_under_cursor())
        try:
            _step = char_width_tools.get_width_of_char(self.value[self.cursor_position +1])
        except:
            _step = 1

        #self.cursor_position += 1
        self.cursor_position += _step

    def h_delete_left(self, input):
        # calculate width for current char and move right. 
        _step = char_width_tools.get_width_of_char(self.get_value_char_under_cursor())

        if self.editable and self.cursor_position > 0:
            self.value = self.value[:self.cursor_position-1] + self.value[self.cursor_position:]
        
        #self.cursor_position -= 1
        #self.begin_at -= 1
        self.cursor_position -= _step 
        self.begin_at -= _step 

    
    def h_delete_right(self, input):
        if self.editable:
            self.value = self.value[:self.cursor_position] + self.value[self.cursor_position+1:]

    def h_erase_left(self, input):
        if self.editable:
            self.value = self.value[self.cursor_position:]
            self.cursor_position=0
    
    def h_erase_right(self, input):
        if self.editable:
            self.value = self.value[:self.cursor_position]
            #self.cursor_position = len(self.value)
            self.cursor_position = char_width_tools.str_width(self.value)
            self.begin_at = 0
    
    def handle_mouse_event(self, mouse_event):
        #mouse_id, x, y, z, bstate = mouse_event
        #rel_mouse_x = x - self.relx - self.parent.show_atx
        mouse_id, rel_x, rel_y, z, bstate = self.interpret_mouse_event(mouse_event)
        self.cursor_position = rel_x + self.begin_at
        self.display()

    
class FixedText(TextfieldBase):
    def set_up_handlers(self):
        super(FixedText, self).set_up_handlers()
        self.handlers.update({curses.KEY_LEFT:  self.h_cursor_left,
                              curses.KEY_RIGHT: self.h_cursor_right,
                              ord('k'):         self.h_exit_up,
                              ord('j'):         self.h_exit_down,
                              })
    
    
    def h_cursor_left(self, input):
        # calculate width for current char and move right. 
        #_step = char_width_tools.get_width_of_char(self.get_value_char_under_cursor())
        try:
            _step = char_width_tools.get_width_of_char(self.value[self.cursor_position -1])
        except:
            _step = 1

        if self.begin_at > 0:
        #    self.begin_at -= 1
            self.begin_at -= _step

    def h_cursor_right(self, input):
        # calculate width for current char and move right. 
        #_step = char_width_tools.get_width_of_char(self.get_value_char_under_cursor())
        try:
            _step = char_width_tools.get_width_of_char(self.value[self.cursor_position +1])
        except:
            _step = 1

        #if len(self.value) - self.begin_at > self.maximum_content_width:
        #    self.begin_at += 1
        #if char_width_tools.str_width(self.value) - self.begin_at > self.maximum_content_width:
        if len(self.value) - self.begin_at > self.maximum_content_width:
            self.begin_at += _step

    def update(self, clear=True,):
        super(FixedText, self).update(clear=clear, cursor=False)
    
    def edit(self):
        self.editing = 1
        self.highlight = False
        self.cursor_position = 0
        self.parent.curses_pad.keypad(1)
        
        self.old_value = self.value
        
        self.how_exited = False

        while self.editing:
            self.display()
            self.get_and_use_key_press()

        self.begin_at = 0
        self.highlight = False
        self.display()

        return self.how_exited, self.value

