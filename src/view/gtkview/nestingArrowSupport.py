# $Id: nestingArrowSupport.py,v 1.2 2002/02/07 23:48:51 ivo Exp $

from nestable import nestable

from gtk import *

class nestingArrowSupport:
    def __init__(self):
        self.arrow = self.get_widget("arrow")

    def nesting_changed(self, state):
        if state == nestable.STATE_TAB:
            self.arrow.set(ARROW_UP, SHADOW_ETCHED_IN)
        else:
            self.arrow.set(ARROW_DOWN, SHADOW_ETCHED_IN)
