#!/usr/bin/python2.1

from twisted.internet.ingtkernet import install

from gtk import *
from GDK import *
from libglade import *
from string import *

from clientlayer import *

class gtksession(client_sessioncallback):
    """ 
    """

    def __init__(self, myhandle, session=None):
        self.myhandle = myhandle
        self.session = session
        self.chatwin = GladeXML("msn.glade", "chat")
        self.chatwin.signal_autoconnect({'on_in_activate':self.text_typed})
        self.out = self.chatwin.get_widget("out")
        if session:
            self.session.sethandler(self)
        self.connected = 0
        self.msgqueue = []
        self.toinvite = None
        
    def setsession(self, session):
        self.session = session
        self.session.sethandler(self)

    def connectionMade(self):
        if self.toinvite:
            self.session.invite(self.toinvite)

    def invite(self, handle):
        """ invote 'handle' after session in realized """
        self.toinvite = handle

    def text_typed(self, item):
        msg = item.get_text()
        item.set_text("")
        self.insert("<%s> %s" % (self.myhandle, msg))
        self.session.sendmessage(msg)

    def insert(self, msg):
        self.out.insert_defaults(msg + "\n")  

    def message_received(self, handle, headers, body):
        """ parse and handle a mime message """
        self.insert("<%s> %s" % (handle, body))

    def handle_by(self, handle):
        self.insert("*** %s has left" % handle)

class gtkapp(client_callback):
    def __init__(self, handle, passwd):
        self.handle = handle
        self.passwd = passwd
        self.mainwin = GladeXML("msn.glade", "main")
        self.online = self.mainwin.get_widget("online")
        self.forward = self.mainwin.get_widget("forward")
        self.reverse = self.mainwin.get_widget("reverse")
        self.allow = self.mainwin.get_widget("allow")
        self.ban = self.mainwin.get_widget("ban")
        self.handle_entry = self.mainwin.get_widget('handle')
        self.password_entry = self.mainwin.get_widget('password')

        self.handle_entry.set_text(handle)
        self.password_entry.set_text(passwd)

        self.mainwin.signal_autoconnect({'on_button_clicked':self.start})
        self.contacts = {}
        self.messenger = None
        self.sessions = {}
        self.pending = {}

    def start(self, button):
        handle = self.handle_entry.get_text()
        passwd = self.password_entry.get_text()
        self.messenger = client(handle, passwd)
        self.messenger.sethandler(self)

    def handle_onlinechange(self, substate, handle, friendly):
        if not self.contacts.has_key(lower(handle)):
            i = GtkListItem(handle)
            self.contacts[lower(handle)] = i
            i.show()
            self.online.append_items([i])
            i.connect("button-press-event", self.handle_button_event, handle)

    def handle_online(self, substate, handle, friendly):
        if not self.contacts.has_key(lower(handle)):
            i = GtkListItem(handle)
            self.contacts[lower(handle)] = i
            i.show()
            self.online.append_items([i])
            i.connect("button-press-event", self.handle_button_event, handle)
    

    def handle_offline(self, handle):
        i = self.contacts[lower(handle)]
        self.online.remove_items([i])
        del self.contacts[lower(handle)]

    def handle_invite(self, session):
        ## all appropriate info is in session
        s = gtksession(self.handle, session)
        self.messenger.accept_session(session) # may become session.accept()

    def handle_sbcreated(self, id, session):
        s = self.pending[id]
        s.setsession(session)
        self.messenger.accept_session(session) # may becomde session.accept()

    def list_complete(self, type):
        fl, rl, al, bl = self.messenger.getlists()
        for widget, list in ((self.forward, fl), (self.reverse, rl), (self.allow, al), (self.ban, bl)):
            for entry in list:
                i = GtkListItem("%s (%s)" % (entry[0], entry[1]))
                i.show()
                widget.append_items([i])

    def handle_button_event(self, item, event, handle):
        if event.type == BUTTON_PRESS:
            pass
        if event.type == GDK._2BUTTON_PRESS:
            # check if chat already present
            id = self.messenger.create_session()
            print "ID", id, type(id)
            c = gtksession(self.handle)
            c.invite(handle)
            self.pending[id] = c
        return 1

if __name__ == '__main__':
    import os, sys

    handle = ""
    password = ""

    if os.environ.has_key('MSNHANDLE'):
        handle = os.environ['MSNHANDLE']
    if os.environ.has_key('MSNPASSWORD'):
        password = os.environ['MSNPASSWORD']
        
    if len(sys.argv) == 3:
        handle = sys.argv[1]
        password = sys.argv[2]

    a = gtkapp(handle, password)

    install() # install twisted gtk thingy
    mainloop()

