import curses
import curses.ascii 
from src import npyscreen

class message_sender(npyscreen.MultiLineEdit):
       
    ######################################################################
    def set_up_handlers(self):
        super().set_up_handlers()
    
        # For OS X
        #del_key = curses.ascii.alt('~')
        
        self.handlers.update({
                   curses.ascii.NL:      self.h_pesky,
                   curses.ascii.CR:      self.h_pesky,
                   #curses.ascii.CAN:     self.h_cancel_input,
                   curses.ascii.BEL:     self.h_cancel_input,
                   #curses.ascii.DLE:     self.h_cancel_input,
                   #23:                   self.h_add_nl,
                   #10:                   self.h_add_nl,
                   curses.ascii.alt(curses.ascii.NL): self.h_add_nl,
                   curses.ascii.alt(curses.KEY_ENTER):self.h_add_nl,
                   #"^\n":                self.h_add_nl, 
                   #"^\r":                self.h_add_nl, 
                   curses.KEY_LEFT:      self.h_cursor_left,
                   curses.KEY_RIGHT:     self.h_cursor_right,
                   curses.KEY_UP:        self.h_line_up,
                   curses.KEY_DOWN:      self.h_line_down,
                   curses.KEY_DC:        self.h_delete_right,
                   curses.ascii.DEL:     self.h_delete_left,
                   curses.ascii.BS:      self.h_delete_left,
                   curses.KEY_BACKSPACE: self.h_delete_left,
                   "^R":           self.full_reformat,
                   # mac os x curses reports DEL as escape oddly
                   # no solution yet                   
                   #"^K":          self.h_erase_right,
                   #"^U":          self.h_erase_left,
            })

        self.complex_handlers.extend((
                    (self.t_input_isprint, self.h_addch),
                    # (self.t_is_ck, self.h_erase_right),
                    # (self.t_is_cu, self.h_erase_left),
                        ))
    def h_pesky(self, _input):
        self.parent.send_command(_input)
        pass

    def h_cancel_input(self, _input):
        if self.value:
            self.value = '# ' + self.value + ' ^C  #取消编辑'
            #self.parent.send_command(_input)
            #self.value = str(self.parent)
            self.parent.msgInfoBoxObj.append_msg(self.value)
            self.value = ""

    #def unset_handler(self, key2del):
    #    try:
    #        del self.handlers[key2del]
    #    except:
    #        pass



class InputBox(npyscreen.BoxTitle):
    pass
    _contained_widget = message_sender
#    _contained_widget = npyscreen.MultiLineEdit 

