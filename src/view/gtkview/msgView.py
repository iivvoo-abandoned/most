"""
    Implementation of a message View, a window that receives messages
    from multiple sources
"""

# $Id: msgView.py,v 1.18 2002/02/01 16:41:40 ivo Exp $

from gtk import *
from GDK import *
import GDK
from libglade import *

from genericView import genericView
from util import casedict
from msgSupport import msgSupport
from detachSupport import detachSupport
from ui import HistoryEntry

class msgView(genericView, msgSupport, detachSupport):
    def __init__(self):
        genericView.__init__(self, "msgwindow")
        self.text = self.get_widget("text")
        self.entry = HistoryEntry(self.get_widget("entry"))
        self.text.set_word_wrap(1)
        self.list = self.get_widget("list")
        self.targetlabel = self.get_widget("targetlabel")
        container = self.get_widget("detach_container")
        self.window = self.get_widget("msgwindow")
        bindings = { 'input_activate':self.input_activate,
                     'window_close':self.window_close,
                     'detach_toggled':self.handle_detach_toggle 
                   }
        self.bindings(bindings)
        self.users = casedict()
        self.lastclicked = 0
        self.name = None
        self.handler = None
        detachSupport.__init__(self, container, self.window)
        
    def set_handler(self, handler):
        self.handler = handler

    def setname(self, name=None):
        self.window.set_title("Incoming messages")

    def msg(self, nick, msg, isme=0):
        """ insert a message from someone """
        msgSupport.msg(self, nick, msg, isme)
        self.adduser(nick)

    def notice(self, nick, msg, isme=0):
        """ insert a message from someone """
        msgSupport.notice(self, nick, msg, isme)
        self.adduser(nick)

    def sendmsg(self, nick, msg):
        """ insert a message *to* someone. this is always done by me """
        msgSupport.sendmsg(self, nick, msg)
        self.adduser(nick)

    def action(self, nick, msg, isme=0):
        """ insert an action from someone """
        msgSupport.action(self, nick, msg, isme)
        self.adduser(nick)
    
    def adduser(self, nick):
        """ add nick to userlist if not already present """
        # add user
        if not self.users.has_key(nick):
            i = GtkListItem(nick)
            i.show()
            self.list.append_items([i])
            self.users[nick] = i
            if len(self.users) == 1:
                # select the user if it's the first / only in the list
                self.setselection(nick)
            i.connect("button-press-event", self.item_handler, nick)

    def deluser(self, nick):
        """ remove nick from the userlist """
        if self.users.has_key(nick):
            self.list.remove_items([self.users[nick]])
            if self.name == nick:
                self.name = None
                self.targetlabel.set_text("No target")
            del self.users[nick]
            # select first entry we find (?)
            if len(self.users) > 0:
                self.setselection(self.users.keys()[0])

    def nickchange(self, oldnick, newnick):
        """ check if we can do anything with the nickchange. If so, report
            it and change the nickname """
        if self.users.has_key(oldnick):
            #
            # Add new before deleting old so we don't lose the selection
            self.adduser(newnick)
            if self.name == oldnick:
                self.setselection(newnick)
            self.deluser(oldnick)
            self.announce("%s is now known as %s" % (oldnick, newnick))

    #
    # XXX The routines below are quite similair: display something if the nickname
    #     is in our userlist. Perhaps refactor into single method?

    def notonline(self, nick):
        """ 
            check if nick is in our userlist, if so, notify user that nick
            is not online 
        """
        if self.users.has_key(nick):
            self.announce("%s is not online" % nick)

    def isaway(self, nick, message):
        """ 
            check if nick is in our userlist, if so, notify user that nick
            is away
        """
        if self.users.has_key(nick):
            self.announce("%s is away: %s" % (nick, message))

    def hasquit(self, nick, uhost, msg):
        """ check if we can do anything with the quit. If so, report
            it. Don't remove the nick though. """
        if self.users.has_key(nick):
            self.announce("%s (%s) has quit (%s)" % (nick, uhost, msg))

    def setselection(self, nick):
        """ make 'nick' the current selection """
        # if type(nick) == type([]) ?
        self.name = nick
        i = self.users[nick]
        i.select()
        self.targetlabel.set_text(nick)

    def item_handler(self, item, event, nick):
        if event.type == BUTTON_PRESS:
            self.setselection(nick)
        if event.type == GDK._2BUTTON_PRESS:
            if self.handler:
                self.handler.view_newquery(nick)
        return 1

    def window_close(self, item, extra):
        if self.handler:
            self.handler.view_winclose(None, None)
        return 1 # don't destroy

    def input_activate(self, item):
        text = item.get_text()
        item.set_text("")
        self.handler.handle_input(self.name, text)
