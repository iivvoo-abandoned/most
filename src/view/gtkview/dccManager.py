#!/usr/bin/python

"""
    Graphical representation of all dcc sessions
"""

from gtk import *
from GDK import *
from libglade import *

class session:
    def __init__(self):
        pass

class dccManager:
    def __init__(self):
        self.tree = GladeXML("../../glade/most.glade", "dccwindow")
        self.table = self.tree.get_widget('table')

    def addTransfer(self, nick, file, size):
        typelabel = GtkLabel('File Transfer')
        flags = GtkLabel('Dunno')
        state = GtkLabel('In Progres')
        nick = GtkLabel(nick)
        statistics = GtkProgressBar()
        arg = GtkLabel(file)

        row = 1
        self.table.attach(typelabel, 0, 1, row, row+1)
        self.table.attach(flags, 1, 2, row, row+1)
        self.table.attach(state, 2, 3, row, row+1)
        self.table.attach(nick, 3, 4, row, row+1)
        self.table.attach(statistics, 4, 5, row, row+1)
        self.table.attach(arg, 5, 6, row, row+1)
        typelabel.show()
        flags.show()
        state.show()
        nick.show()
        statistics.show()
        arg.show()
        


if __name__ == '__main__':
    d = dccManager()
    d.addTransfer('VladDrac', '/etc/passwd', 1234)
    mainloop()
