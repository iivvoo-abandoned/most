"""
"""

from gtk import *
from GDK import *
from libglade import *

from util import casedict
from msnSession import msnSession

class msnView:
    def __init__(self):
        self.handles = casedict()
        self.handler = None

    def set_handler(self, handler):
        self.handler = handler

    def set_tree(self, item, tree):
        self.item = item
        self.tree = tree

    def add_online(self, handle, state):
        treeitem = GtkTreeItem(handle)
        self.tree.append(treeitem)
        treeitem.connect("button-press-event", self.tree_handler, handle)
        treeitem.show()
        self.handles[handle] = treeitem

    def change_online(self, handle, state):
        """ state can be offline as well """
        if handle == "offline": # whatever
            if self.handles.has_key(state):
                item = self.handles[handle]
                self.tree.remove_item(item)

    def createSession(self):
        return msnSession()

    ## gui events
    def tree_handler(self, item, event, name):
        if event.type == GDK._2BUTTON_PRESS:
            print "2", name
            self.handler.start_session(name)
        elif event.type == GDK.BUTTON_PRESS:
            print "1", name
        else:
            print "Dunno", name

