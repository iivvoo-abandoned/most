""" 
    a view for a single server. This view must be wrapped in some container,
    i.e. window or notebook
"""

# $Id: serverView.py,v 1.2 2001/10/09 22:19:58 ivo Exp $

from threading import Thread
from string import *

from msgSupport import msgSupport
from genericView import genericView
from channelView import channelView
from queryView import queryView
from msgView import msgView

from view import guiMessage

from util import casedict
from util.debug import debug, DEBUG, NOTICE, ERROR

#
# a serverView is a single tab in the ircView notebook.
# It does some trickery because glade creates the first tab for us
# by default, and we add the next ones (this is done in ircView.poolfactory

class serverView(msgSupport, genericView, Thread):
    def __init__(self, name=None):
        Thread.__init__(self)
        self.handler = None
        self.name = None
        self.channels = casedict()
        self.queries = casedict()
        self.online = casedict()
        self.offline = casedict()
        self.msgwin = msgView()

        if name:
            self.setname(name)

    def get_container(self):
        return self.container

    def setcallback(self, cb):
        self.handler = cb

    def setlabel(self, w):      # XXX Remove
        pass

    def setname(self, name):
        self.name = name

    def create_channel(self, name):
        newchan = channelView(name)
        newchan.setcallback(self.view_handler)
        self.name = name
        return newchan

    def create_query(self, name):
        newquery = queryView(name)
        self.queries[name] = newquery
        newquery.setcallback(self.view_handler)
        return newquery

    def delete_channel(self, name):
        if self.channels.has_key(name):
            c = self.channels[name]
            del self.channels[name]
        else:
            debug(ERROR, "Attempt to remove non existing channel %s" % name)

    def delete_query(self, name):
        if self.queries.has_key(name):
            q = self.queries[name]
            del self.queries[name]
        else:
            debug(ERROR, "Attempt to remove non existing query %s" % name)

    def view_handler(self, item, event, data=None):
        """ handler invoked by view-components """
        # forward everything
        self.handler(item, event, data)

    def get_msgwin(self, create=1):
        """ return the messagewindow, create one if necessary """
        #return self.msgwin
        return None

    def close_msgwin(self):
        pass

    def notify_online(self, name):
        if self.offline.has_key(name):
            self.announce("Signon by %s detected" % name)
            item = self.offline[name]
            del self.offline[name]
        self.online[name] = 1

    def notify_offline(self, name):
        if self.online.has_key(name):
            self.announce("Signoff by %s detected" % name)
            del self.online[name]
        self.offline[name] = 1

    def run(self):
        while 1:
            text = raw_input()
            event = None
            if strip(text) != "":
                if text[0] == '/':
                    event = guiMessage.guiMessage(text[1:])
                    # if event.type == guiMessage.UNKNOWN ...
                else:
                    event = guiMessage.guiMessage()
                    event.type = guiMessage.MSG
                    if hasattr(self, 'name'):
                        event.source = self.name
                        event.target = self.name # This should invoke some method
                    event.data = text
            
                if self.handler:
                    self.handler(self, event)
