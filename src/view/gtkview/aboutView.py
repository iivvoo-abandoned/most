from gtk import *
from GDK import *
from libglade import *

from genericView import genericView

class aboutView(genericView):
    def __init__(self):
        genericView.__init__(self, "about")
	self.window = self.get_widget("about")
	self.bindings({'window_close':self.window_close,
	               "ok_clicked":self.window_close})
        self.handler = None

    def set_handler(self, handler):
        self.handler = handler

    def window_close(self, item, e=None):
	""" It's very wrong to exit here, but for now it works """
	if self.handler:
            self.handler.win_close("about", None)
	return 1

