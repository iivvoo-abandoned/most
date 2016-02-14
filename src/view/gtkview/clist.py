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

class clist:
    def __init__(self):
        self.tree = GladeXML("clist.glade", "window1")
        self.clist = self.tree.get_widget('clist')

    def addTransfer(self, nick, file, size):
        nick = GtkLabel(nick)
        statistics = GtkProgressBar()
        arg = GtkLabel(file)

        self.clist.set_column_widget(4, nick)
        self.clist.set_column_widget(5, statistics)
        self.clist.set_column_widget(6, arg)
        nick.show()
        statistics.show()
        arg.show()
        


if __name__ == '__main__':
    d = clist()
    d.addTransfer('VladDrac', '/etc/passwd', 1234)
    mainloop()
