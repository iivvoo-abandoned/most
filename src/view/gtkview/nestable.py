"""
    a nestable component can be nested in any sort of container widget,
    be moved to another widget later, etc.
"""

# $Id: nestable.py,v 1.9 2002/02/07 23:48:51 ivo Exp $

from gtk import *

##
## This can probably be merged with genericView (as it does stuff like that
## anyway

## nestableContainer?

class nestable:
    STATE_NOTNESTED = 0
    STATE_TAB = 1
    STATE_WINDOW = 2

    def __init__(self, container=None, outer_container=None, state=STATE_NOTNESTED):
        self.container = container
        self.outer_container = outer_container
        self.state = state
        self.active_tab = 0
        ##
        ## Make sure prober bindings for window deletion are installed
        if state == nestable.STATE_WINDOW:
            self.outer_container.connect("delete-event", self.window_close)
            self.outer_container.connect("destroy-event", self.window_close)

    def nest(self, container):
        """ "nest" the widget in the (optional) container, create an 
            appropriate container of none is given """
        ##
        ## TODO:
        ## After 'renesting', certain attributes must be reset (i.e. the title)
        if self.outer_container:
            self.outer_container.remove(self.container)
            if hasattr(self.outer_container, "destroy") and \
               callable(self.outer_container.destroy):
                self.outer_container.destroy() # perhaps define a proper interface

        if container:
            self.outer_container = container
        else:
            self.outer_container = GtkWindow()
            self.outer_container.show()
        self.outer_container.add(self.container)


    def nestTab(self, notebook, container, label):
        self.nest(container)
        self.notebook = notebook
        # create new tab ourself?
        self.label = label

        s= self.label.get_style().copy()
        s.fg[STATE_NORMAL] = GdkColor(0, 0, -1)
        self.label.set_style(s)

        self.state = nestable.STATE_TAB
        self.nesting_changed(self.state)

    def nestWindow(self, container=None):
        self.nest(container)
        self.label = None
        self.state = nestable.STATE_WINDOW
        print self.outer_container
        self.outer_container.connect("delete-event", self.window_close)
        self.outer_container.connect("destroy-event", self.window_close)
        self.nesting_changed(self.state)

    def window_close(self, item, extra):
        pass # to be overriden

    # move to different, container-aware, class
    def set_title(self, title):
        # short, long version?
        if self.state == nestable.STATE_TAB:
            self.label.set_text(title)
        else:
            self.outer_container.set_title(title)

    def raisewin(self):
        if self.state == nestable.STATE_WINDOW:
            self.outer_container.get_window()._raise()
        ## 
        ## XXX
        ## to raise a tab, we probably need the entire notebook widget...
        
    def destroy(self):
        """ destroy outer container """
        ##
        ## Only if window?
        if self.state == nestable.STATE_WINDOW:
            self.outer_container.destroy()

    def activate(self):
        """ invoked when this page becomes the active_tab tab """
        self.active_tab = 1
        # de-colorize tab
        if self.state == nestable.STATE_TAB:
            s = self.label.get_style().copy()
            #
            # this may not work correctly, as the theme may use a different
            # color. Actually, we need to save the previous style.
            s.fg[STATE_NORMAL] = GdkColor(0, 0, 0)
            self.label.set_style(s)

    def deactivate(self):
        self.active_tab = 0

    def updated(self):
        """ invoked when the text in this container is updated """
        if self.state == nestable.STATE_TAB and not self.active_tab:
            s = self.label.get_style().copy()
            s.fg[STATE_NORMAL] = GdkColor(-1, 0, 0)
            self.label.set_style(s)

    def get_container(self):
        """ return the inner container """
        return self.container

    def get_outer_container(self):
        """ return the outer container """
        return self.outer_container

    def nesting_changed(self, state):
        pass

    def window_close(self, *args):
        print "Boom"
