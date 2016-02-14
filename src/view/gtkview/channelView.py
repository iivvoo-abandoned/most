"""
    Implementation of the channel (1-n communication) view
"""

# $Id: channelView.py,v 1.37 2002/02/22 16:50:35 ivo Exp $

from gtk import *
from GDK import *
from libglade import *

from string import *

from genericView import genericView
from msgSupport import msgSupport

from util import casedict
from ui import UserList, HistoryEntry
from util.debug import debug, DEBUG, NOTICE, ERROR
from detachSupport import detachSupport

from nestable import nestable
from nestingArrowSupport import nestingArrowSupport

#
# TODO:
#
# - sorted (asc,desc) / random userlist
#
# use some shared configstate to fetch 'highlight' words?

class channelView(genericView, msgSupport, nestingArrowSupport, nestable, detachSupport):
    def __init__(self, name, container, state):
        genericView.__init__(self, "channel_detach_container")
        nestable.__init__(self, self.window, container, state)
        nestingArrowSupport.__init__(self)
        #
        # Does this belong here?
        container.add(self.window)

        self.name = name
        self.entry = HistoryEntry(self.get_widget("entry"))
        self.list = UserList(self.get_widget("list"))
        self.topicentry = self.get_widget("topicentry")
        self.limitentry = self.get_widget("limitentry")
        self.keyentry = self.get_widget("keyentry")
        self.modelabel = self.get_widget("modelabel")
        font = self.limitentry.get_style().font
        width = font.width('555555')
        self.limitentry.set_usize(width, -1)
        font = self.keyentry.get_style().font
        width = font.width('MMMMMMMMMM')
        self.keyentry.set_usize(width, -1)
        
        self.setname(name)
        self.modestr = []

        self.closeonleave = 0
        self.active = 1 # by default
        self.tree = None
        self.treeitems = casedict() # XXX TODO: merge with self.list/self.users

        #
        # Perform bindings
        bindings = { 'input_activate':self.input_activate,
                     'window_close':self.window_close,
                     'detach_toggled':self.handle_detach_toggle,
                     'on_topicentry_activate':self.on_topicentry_activate,
                     'on_keyentry_activate':self.on_keyentry_activate,
                     'on_limitentry_activate':self.on_limitentry_activate
                   }
        self.bindings(bindings)

        self.text = self.get_widget("text")
        self.text.set_word_wrap(1)

    def set_handler(self, handler):
        self.handler = handler

    def setname(self, name=None):
        if name:
            self.name = name
        self.set_title("Channel %s" % self.name)

    def adduser(self, nick, mode=None):
        # TODO: Take model + view of UserList apart so we can store treeitems 
        # in it as well.
        i = self.list.adduser(nick, mode) # XXX No, no GtkItems here!
        i.connect("button-press-event", self.item_handler, nick)
        #
        # tmp
        treeitem = GtkTreeItem(nick)
        self.tree.append(treeitem)
        treeitem.show()
        self.treeitems[nick] = treeitem
        treeitem.connect("button-press-event", self.item_handler, nick)

    def deluser(self, nick):
        self.list.deluser(nick)
        if self.treeitems.has_key(nick):
            self.tree.remove_item(self.treeitems[nick])
            del self.treeitems[nick]
        else:
            debug(ERROR, "Attempting to remove missing user %s from channel " \
                         "%s from tree" % (nick, self.name))

    def userjoin(self, nick, userhost):
        self.announce("%s (%s) has joined channel %s" % \
                      (nick, userhost, self.name))
        self.adduser(nick)

    def userquit(self, nick, userhost, reason):
        self.announce("%s has quit (%s)" % (nick,  reason))
        self.deluser(nick)

    # add: isself
    def userleave(self, nick, userhost, reason):
        self.announce("%s (%s) has left channel %s (%s)" % \
                      (nick, userhost, self.name, reason))
        self.deluser(nick)

    def userkick(self, nick, userhost, target, reason, isself=0):
        if isself:
            self.announce("You have been kicked from channel %s by " \
                          "%s (%s) (%s)" % (self.name, nick, userhost, reason))
        else:
            self.announce("%s has been kicked from channel %s by " \
                          "%s (%s) (%s)" % (target, self.name, nick, 
                                            userhost, reason))
        self.deluser(target)

    def modechange(self, nick, modechange, notice=1):
        """ handle channelmode changes """
        modestr = ""
        plusmodes = modechange.plusmodes()
        minmodes = modechange.minmodes()
        plusparams = modechange.plusparams()
        minparams = modechange.minparams()

        if plusmodes != "":
            modestr = modestr + "+" + plusmodes
        if minmodes != "":
            modestr = modestr + "-" + minmodes
        if plusmodes != []:
            modestr = modestr + " " + join(plusparams, ' ')
        if minmodes != []:
            modestr = modestr + " " + join(minparams, ' ')

        if notice:
            self.announce("%s sets mode %s" % (nick, modestr))

        if 'k' in minmodes:
            self.keyentry.set_text("")
        if 'l' in minmodes:
            self.limitentry.set_text("")
        if 'k' in plusmodes:
            i = find(plusmodes, 'k')
            self.keyentry.set_text(plusparams[i])
        if 'l' in plusmodes:
            i = find(plusmodes, 'l')
            self.limitentry.set_text(plusparams[i])
        ##
        ## XXX move to class, along with serverView
        for i in minmodes:
            if i not in "ovbeI" and i in self.modestr:
                self.modestr.remove(i)
        for i in plusmodes:
            if i not in "ovbeI" and i not in self.modestr:
                self.modestr.append(i)
        self.modelabel.set_text("+"+join(self.modestr, ""))

    def usermodechange(self, nick, mode):
        """ Handle a usermode change on a channel """
        # do we want to work with GtkItems on this level?
        i = self.list.modechange(nick, mode)
        i.connect("button-press-event", self.item_handler, nick)

    def topic(self, topic, changed_by = None):
        print "Topic is nu", topic
        self.topicentry.set_text(topic)
        if changed_by:
            self.announce("%s sets the topic to %s" % (changed_by, topic))

    def nickchange(self, oldnick, newnick):
        if self.list.hasuser(oldnick):
            self.announce("%s is now known as %s" % (oldnick, newnick))
            # move connect to UserList
            i = self.list.nickchange(oldnick, newnick)
            i.connect("button-press-event", self.item_handler, newnick)

            # update tree
            item = self.treeitems[oldnick]
            del self.treeitems[oldnick]
            item.children()[0].set_text(newnick)
            self.treeitems[newnick] = item

    def window_close(self, item, extra):
        """ Invoked when someone closes the window. 
        
            Todo: what does 'extra' do? Is it a gdk event?
        """

        # If our state is "inactive" then PARTING won't have any use -
        # explicitly destroy the window.

        print "CLOSE"
        if not self.active:
            print "not active"
            # we need to inform handler anyway (so it can clean up references)
            # self.destroy()
            # ignore for now
            return 1
            
        self.closeonleave = 1  # so window gets closed after PART
        if self.handler:
            self.handler.view_winclose(self.name, self.name)
        return 1  # don't close window for us

    def part(self):
        """ invoked when *I* leave this channel. I.e. after explicit /leave
            or after kick. Closing a window implicitly triggers a /leave,
            but also sets the self.closeonleave flag to true

            Todo (?): add type (type of parting: kick, part, ..)
        """
        #
        # This gives us a (harmless?) 
        # Gtk-WARNING **: gtk_signal_disconnect_by_data(): 
        #    could not find handler containing data (0x8271940)
        # Perhaps because we didn't install any handler, yet?
        #self.list.remove_items(self.users.values())
        self.list.clear()
        self.topicentry.set_text("")

        if self.closeonleave:
            self.destroy()
            return 1
        return 0

    # create baseclass for generic (sub)tree support?
    def set_tree(self, tree):
        self.tree = tree
        # add dummy item - see serverView.set_tree why
        self.tree.append(GtkTreeItem())

    # nickmenu handling/implementation should be in a separate class
    def item_handler(self, item, event, nick):
        """ handle events from tree and userlist items """
        if event.type == BUTTON_PRESS and event.button == 3:
            foo = GladeXML("glade/most.glade", "nick_menu")
            bar = foo.get_widget("nick_menu")
            bar.popup(None, None, None, event.button, event.time)
            bar.connect("button-release-event", self.menu_handler, nick)
            foo.signal_autoconnect(
                  {'whois_activate': (self.handle_whois, nick)}
            )

            return 0
        if event.type == GDK._2BUTTON_PRESS:
            if self.handler:
                self.handler.view_newquery(self.name, nick)
        return 1

    def menu_handler(self, item, event, nick):
        pass

    def handle_whois(self, a, nick):
        if self.handler:
            self.handler.view_whois(self.name, nick)

    def reset(self, propagate=1, level=0):
        """ clear userlist, clear tree """
        self.list.clear()
        for (name, item) in self.treeitems.items():
            self.tree.remove_item(item)
            del self.treeitems[name]

    ## 
    ## widget handlers
    def on_topicentry_activate(self, entry):
        text = entry.get_text()
        self.handler.view_topic(self.name, text)
        self.entry.grab_focus()

    ##
    ## Sending the modechanges as strings somewhat breaks the abstraction
    def on_keyentry_activate(self, entry):
        text = strip(entry.get_text())
        if text == "":
            self.handler.view_mode(self.name, "-k")
        else:
            self.handler.view_mode(self.name, "-k+k %s" % text)
        self.entry.grab_focus()

    def on_limitentry_activate(self, entry):
        text = strip(entry.get_text())
        # check if empty or number
        if text == "":
            self.handler.view_mode(self.name, "-l")
        else:
            self.handler.view_mode(self.name, "+l %s" % text)
        self.entry.grab_focus()

    def input_activate(self, item):
        text = item.get_text()
        item.set_text("")
        self.handler.handle_input(self.name, text)
