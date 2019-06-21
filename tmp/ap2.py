import npyscreen

def myFunction(*args):
    F = npyscreen.Form(name='My Test Application')
    #F.add(npyscreen.TitleText, name="First Widget")
    myFW = F.add(npyscreen.TitleText, name="First Widget")
    F.edit()
    return myFW.value 

class myEmployeeForm(npyscreen.Form):
    def create(self):
        super(myEmployeeForm, self).create #for later code 
        self.myName       = self.add(npyscreen.TitleText, name='Name of a lone iterm', begin_entry_at=32)
        #self.myDepartment = self.add(npyscreen.TitleText, name='Department')
        self.myDate       = self.add(npyscreen.TitleDateCombo, name='Date Employed')
        self.test1      = self.add(npyscreen.Checkbox, name='选框1', value=True)
        self.myDepartment = self.add(npyscreen.TitleSelectOne, max_height=4, 
                                     name='Department',
                                     values = ['Department_A', 'Department_B', 'Department_C'],
                                     scroll_exit = True 
                                    )


def myFunction2(*args):
    F = myEmployeeForm(name = "New Employee")
    F.edit()
    return "Create record for " + F.myName.value

if __name__ == '__main__':
    print(npyscreen.wrapper_basic(myFunction2))
    #print "Blink and you missed it!"
