#!/usr/bin/python

# $Id: ircView.py,v 1.29 2002/03/26 14:46:20 ivo Exp $

import sys

from GdkImlib import *
from gtk import *
from GDK import *
from libglade import *

from string import strip

from util.cfg import getCfg

from genericView import genericView
from aboutView import aboutView
from msgSupport import msgSupport
from serverView import serverView
from msnView import msnView

from nestable import nestable

from util.debug import debug, DEBUG, NOTICE, ERROR


class ircView(genericView): 
    def __init__(self):
        genericView.__init__(self, "most")
        self.tree = self.get_widget("tree")
        bindings = { 'switch_page':self.switch_page,
                     'window_close':self.window_close,
                     'menu_about':self.about }
        self.bindings(bindings)
        self.count = 0
        self.tabs = self.get_widget("tabs")
        self.tabmap = {}
        self.currentpage = None

        self.windows = [] # TO BE MOVED
        self.wincnt = 0
        self.handler = None
        self.about = None

    def set_handler(self, handler):
        self.handler = handler

    def window_close(self, item, e=None):
        # send quit message to handler, which does proper quitting
        if self.handler:
            self.handler.meta_close(None, None)
        return 1

    def about_handler(self, item, event):
        self.about.destroy()
        self.about = None

    def switch_page(self, item, page, num, data=None):
        if self.currentpage:
            self.currentpage.deactivate()
        p = self.tabs.get_nth_page(num)
        # p == item?
        q = self.tabmap[p]
        q.activate()
        self.currentpage = q

    def about(self, item, e=None):
        """ display the about dialog """
        if not self.about:
            self.about = aboutView()
            self.about.set_handler(self)

    def tree_handler(self, item, event, page):
        """ handles events from the tree widget """
        self.tabs.set_page(page)
        return 0

    def new_view(self, name):
        newview = serverView()
        newview.set_detach_handler(self.attach_detach)
        ##
        ## The initial tab that comes with the GtkNotebook creation seems to
        ## give too many problems. For example, it does not seem to be able
        ## to change the color of its label (a gtk bug?). Therefore this tab
        ## is immediately after creating the second tab (a GtkNotebook can't
        ## handle having 0 tabs very well).
        l = GtkLabel("tab %d" % self.count)
        l.set_name("label")

        container = GtkVBox()
        container.show()
        newview.nestTab(self.tabs, container, l)
        self.tabs.append_page(container, l)
        self.count = self.count + 1
        ##
        ## The tabmap must contain newview, because the (possible) deletion of
        ## the first tab may cause switch_page to be invoked.
        self.tabmap[container] = newview
        if len(self.tabmap.keys()) == 1:
            self.tabs.remove_page(0)

        self.currentpage = newview 
        newview.activate()

        serveritem = GtkTreeItem(name)
        servertree = GtkTree()
        self.tree.append(serveritem)
        serveritem.set_subtree(servertree)
        serveritem.show()
        serveritem.connect("button-press-event", self.tree_handler, self.count)
        # delegate subtree
        newview.set_tree(serveritem, servertree)
        return newview

    def new_msnview(self, handle):
        """ create msn gui component """
        m = msnView()
        serveritem = GtkTreeItem("msn:%s" % handle)
        servertree = GtkTree()
        self.tree.append(serveritem)
        serveritem.set_subtree(servertree)
        serveritem.show()
        serveritem.connect("button-press-event", self.tree_handler, self.count)
        # delegate subtree
        m.set_tree(serveritem, servertree)
        return m

    #
    # support to attach windows to notebooks or GtkWindows
    #
    # Eventually move this to 'WindowManager'? Singleton? Make sure
    # there is support for multiple notebooks
    def attach_detach(self, win):
        ctr = win.get_container()
        if win.state == nestable.STATE_WINDOW:  # windowed
            debug(DEBUG, "Moving %s from window to tab" % win.name)
            container = GtkVBox()
            self.tabmap[container] = win
            l = GtkLabel(win.name)
            l.set_name("label")
            l.show()

            win.nestTab(self.tabs, container, l)
            self.tabs.append_page(container, l)
            container.show()
            self.count = self.count + 1
        else: # tabbed
            if len(self.tabs.children()) == 1:
                return 1
            debug(DEBUG, "Moving %s from tab to window" % win.name)
            outer = win.get_outer_container()
            del self.tabmap[outer]
            win.nestWindow()

    ## these are already in genericview
    def mainloop(self):
        mainloop()

    def threads_enter(self):
        pass # not required with twisted

    def threads_leave(self):
        pass # not required with twisted
_view = None

def getIrcView():
    global _view
    if not _view:
        from twisted.internet.ingtkernet import install
        install() # install twisted bindings
        _view = ircView()
    return _view

def parse_config(file=None):
    if not file:
        cfg = getCfg()
        file = cfg("gtkview.rc", None)
    if file:
        rc_parse(file)
