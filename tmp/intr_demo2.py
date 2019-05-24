#!/usr/bin/env python
# encoding: utf-8

import npyscreen
class TestApp(npyscreen.NPSApp):
    def main(self):
        # These lines create the form and populate it with widgets.
        # A fairly complex screen in only 8 or so lines of code - a line for each control.
        F  = npyscreen.Form(name = "Welcome to Npyscreen",)
        t  = F.add(npyscreen.TitleText, name = "Text:",)
        fn = F.add(npyscreen.TitleFilename, name = "Filename:")
        fn2 = F.add(npyscreen.TitleFilenameCombo, name="Filename2:")
        dt = F.add(npyscreen.TitleDateCombo, name = "Date:")
        ml = F.add(npyscreen.MultiLineEdit,
               value = """try typing here!\nMutiline text, press ^R to reformat.\n""",
               max_height=5)# , rely=9)
        s  = F.add(npyscreen.TitleSlider, out_of=12, name = "Slider")
        me = F.add(npyscreen.MultiLineEditableBoxed, name="MultiLineEditableBoxed", max_height=5 )
        ry = F.nextrely 
        ms = F.add(npyscreen.TitleSelectOne, max_height=4, value = [1,], name="Pick One",
                values = ["Option1","Option2","Option3"], scroll_exit=True, field_width=40, exit_left=True)
        F.nextrelx += 40 
        F.nextrely =ry
        ms2= F.add(npyscreen.TitleMultiSelect, max_height =9, value = [1,], name="Pick Several",
                values = ["Option1","Option2","Option3"], scroll_exit=True)
        co = F.add(npyscreen.ComboBox,value=[0,], values=['001', '002'] )

        # This lets the user interact with the Form.
        F.edit()

        print(str(ms.get_selected_objects()))
        print(str(co.value))

if __name__ == "__main__":
    App = TestApp()
    App.run()
