# $Id: genericView.py,v 1.9 2001/12/11 09:43:06 ivo Exp $

from gtk import *
from GDK import *
from libglade import *

class genericView:
    def __init__(self, toplevel_name, bindings = None):
	self.widgetTree = GladeXML("glade/most.glade", toplevel_name)
        self.window = self.widgetTree.get_widget(toplevel_name)
        self.window.show()
	if bindings:
	    self.bindings(bindings)

    def get_widget(self, name):
        return self.widgetTree.get_widget(name)

    def bindings(self, b):
        self.widgetTree.signal_autoconnect(b)

    def mainquit(self):
        mainquit()



