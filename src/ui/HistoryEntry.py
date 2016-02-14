""" 
    Implementation of a GtkEntry with history capabilities 
    (and appropriate bindings)
"""

# $Id: HistoryEntry.py,v 1.6 2001/10/07 23:50:45 ivo Exp $

import GDK
import gtk

from util import Extender

#
# Optionally set max size of history? Add shared history?

class HistoryEntryExtender:
    def __init__(self):
        #self.entry = entry
        self.postinit()

    def postinit(self):
        self.connect("key_press_event", self.entry_handler)
        self.history = []
        self.index = 0
        # max size?

    def entry_handler(self, entry, event):
        """ Handle special events from the entry """
        #
        # This code based on pygtk's examples/ide/gtcons.py
        if event.keyval == GDK.Return:
            self.emit_stop_by_name("key_press_event")
            self.entry_activate()
        elif event.keyval in (GDK.KP_Up, GDK.Up):
            self.history_up()
            self.emit_stop_by_name("key_press_event")
            return 1
        elif event.keyval in (GDK.KP_Down, GDK.Down):
            self.history_down()
            self.emit_stop_by_name("key_press_event")
            return 1

    def history_up(self):
        if self.index == 0:
            gtk.gdk_beep()
        else:
            self.index = self.index - 1
            #self.history.append(self.entry.get_text())
            self.set_text(self.history[self.index])
            
    def history_down(self):
        if self.index == len(self.history):
            self.set_text("")
            gtk.gdk_beep()
        else:
            self.set_text(self.history[self.index])
            self.index = self.index + 1

    def entry_activate(self):
        self.history.append(self.get_text())
        #self.entry.set_text("")
        self.index = len(self.history)

def HistoryEntry(base):
    return Extender(HistoryEntryExtender, base, "HistoryExtender")
