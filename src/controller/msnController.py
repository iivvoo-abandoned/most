"""
    msnController - mediate between UI and msn
"""

from view import ircView

from msn.clientlayer import *
from util import casedict

##
## Store state in model?

class msnSessionController(client_sessioncallback):
    def __init__(self, myhandle, view):
        self.toinvite = None
        self.myhandle = myhandle
        self.view = view
        self.view.set_handler(self)

    def setsession(self, session):
        self.session = session
        self.session.sethandler(self)

    def invite(self, toinvite):
        self.toinvite = toinvite

    def connectionMade(self):
        if self.toinvite:
            self.view.announce("Inviting %s" % self.toinvite)
            self.session.invite(self.toinvite)

    def message_received(self, handle, headers, body):
        """ parse and handle a mime message """
        self.view.msg(handle, body)

    ## gui events
    def handle_input(self, text):
        self.view.msg(self.myhandle, text, isme=1)
        self.session.sendmessage(text)

class msnController(client_callback):
    def __init__(self, myhandle, password):
        self.myhandle = myhandle
        self.password = password
        self.view = ircView.getIrcView()
        self.msnview = self.view.new_msnview(self.myhandle)
        self.msnview.set_handler(self)
        self.sessions = []
        self.pending = {}
        
    def run(self):
        self.messenger = client(self.myhandle, self.password)
        self.messenger.sethandler(self)

    def handle_onlinechange(self, substate, handle, friendly):
        self.msnview.change_online(handle, substate)

    def handle_online(self, substate, handle, friendly):
        self.msnview.add_online(handle, substate)
    
    def handle_offline(self, handle):
        self.msnview.change_online(handle, "offline") # XXX

    def handle_invite(self, session):
        ## auto accept, at this moment (change!) XXX
        self.messenger.accept_session(session) # may become session.accept()
        view = self.msnview.createSession()
        s = msnSessionController(self.myhandle, view)
        s.setsession(session)
        self.sessions.append(s)

    def handle_sbcreated(self, id, session):
        s = self.pending[id]
        s.setsession(session)
        self.messenger.accept_session(session) # may becomde session.accept()
        del self.pending[id]
        self.sessions.append(s)

    ## handler methods
    def start_session(self, handle):
        id = self.messenger.create_session()
        view = self.msnview.createSession(handle)
        s = msnSessionController(self.myhandle, view)
        s.invite(handle)
        self.pending[id] = s
        print "Request to start session with", handle
