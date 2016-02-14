"""
    support for DCC

    Things to consider/remember:

    - it may be difficult/impossible to properly track nickchanges (?)
    - will dcc chats work with the message window?
"""

# $Id: dccSupport.py,v 1.13 2002/04/21 20:49:23 ivo Exp $

from twisted.internet.tcp import Client, Port
from twisted.protocols.protocol import Factory

from net.dcc import *
from net import getnick
from util import net, casedict
from string import *

##
## move this factory to dcc.py?
##
## close listening socket after a while
## optionally only accept from certain hosts

class dccFactory(Factory):
    def __init__(self, handler, session, protocol):
        self.handler = handler
        self.session = session
        self.protocol = protocol
        
    def buildProtocol(self, addr):
        prot = self.protocol(self.handler, self.session)
        self.session.chat = prot
        return prot

class dccSession:
    DCCSESSION_CHAT = 1
    DCCSESSION_FILESEND = 2
    DCCSESSION_FILEGET = 3

    def __init__(self, type, nick):
        self.nick = nick
        self.type = type
        self.connected = 0
        self.chat = None
        self.conn = None
        
class dccSend(dccSession):
    def __init__(self, nick, file):
        dccSession.__init__(self, dccSession.DCCSESSION_FILESEND, nick)
        self.file = file
        self.filehandle = open(file, "r")

    def getBlock(self):
        data = self.filehandle.read(1024)
        print "Sending block for %s" % self.file
        if data:
            return data
        self.filehandle.close()
        return None

class dccGet(dccSession):
    def __init__(self, nick, file):
        dccSession.__init__(self, dccSession.DCCSESSION_FILEGET, nick)
        self.file = file
        self.filehandle = open("/tmp/%s" % file, "w")

    def dcc_dataReceived(self, data, blahXXX):
        self.filehandle.write(data)

    def dcc_connectionLost(self, data):
        self.filehandle.close()
##
## Idea: create dcc state object (that contains dcc state info, connection,
## etc, and pass this (always) to newly created query views.
class dccSupport:
    def __init__(self):
        self.dccsessions = []

    def dcc_start_chat(self, nick):
        """ 
            start a dcc chat with 'nick' - i.e. open local socket,
            send appropriate ctcp message, update model
        """
        s = dccSession(dccSession.DCCSESSION_CHAT, nick)
        factory = dccFactory(self, s, dcc_chat)
        conn = Port(0, factory, backlog=1)
        conn.startListening()
        
        (prot, dcchost, dccport) = conn.getHost()

        #
        # don't trust the host reported by dcc_chat - it's unconnected,
        # so it's not clear on which interface the connection will be
        serverhost = self.irc.getHost()[1]
        self.ctcp(nick, "DCC", "CHAT chat %lu %u" % \
                             (net.inet_aton(serverhost), dccport))

        self.dccsessions.append(s) # move to factory?
        if self.queries.has_key(nick):
            target = self.queries[nick]
        else:
            target = self.viewtext
        target.announce("Starting dcc chat with %s" % nick)

    def dcc_chat_send(self, nick, msg):
        """ 
            send a line of text through a dcc chat 

            return false if no chat is available
        """
        for i in self.dccsessions:
            if lower(i.nick) == lower(nick):
                ## chat may not be established
                i.chat.send(msg)
                return 1
        return 0

    def dcc_send_file(self, nick, file):
        s = dccSend(nick, file)
        factory = dccFactory(self, s, dcc_fileoffer)
        conn = Port(0, factory, backlog=1)
        conn.startListening()
        
        (prot, dcchost, dccport) = conn.getHost()

        #
        # don't trust the host reported by dcc_chat - it's unconnected,
        # so it's not clear on which interface the connection will be
        serverhost = self.getHost()[1]
        self.ctcp(nick, "DCC", "SEND %s %lu %u" % \
                             (file, net.inet_aton(serverhost), dccport))
        self.dccsessions.append(s)
        self.viewtext.announce("Waiting for %s to accept %s" % (nick, file))

    def dcc_accept_chat(self, nick, host, port):
        """ 
            accept an offered chat. What about checking ports, etc? Is that
            done here or elsewhere?

            Also, make the chat pending - we don't want to accept chats
            immediately (unless the users explicitly configures this so)
        """
        print "Accepting", nick, host, port
        s = dccSession(dccSession.DCCSESSION_CHAT, nick)
        chat = dcc_chat(self, s)
        conn = Client(host, port, chat)
        s.connected = 1
        s.chat = chat
        s.conn = conn
        self.dccsessions.append(s)
        
    def dcc_accept_file(self, nick, host, port, file, size):
        print "Accepting", nick, host, port, file
        s = dccGet(nick, file)
        file = dcc_filereceipt(s, s) # XXX handler inconsistent!
        conn = Client(host, port, file)
        s.connected = 1
        s.file = file
        s.conn = conn
        self.dccsessions.append(s)

    def dcc_connectionMade(self, data=None):
        nick = data.nick
        data.connected = 1
        print "Connection made", nick
        if self.queries.has_key(nick):
            self.queries[nick].dcc_established()
        else:
            ## enforce that dcc is always done per query
            msg = self.viewtext.get_msgwin(create=0)
            if msg:
                msg.announce("DCC chat connection with %s established" % nick)
            else:
                self.viewtext.announce("DCC chat connection with %s established" % nick)

    def getBlock(self, data):
        return data.getBlock()

    def dcc_connectionLost(self, data):
        nick = data.nick
        data.connected = 0
        print "Connection lost", nick
        if self.queries.has_key(nick):
            self.queries[nick].dcc_lost()
        else:
            ## enforce that dcc is always done per query
            msg = self.viewtext.get_msgwin(create=0)
            if msg:
                msg.announce("DCC chat connection with %s lost" % nick)
            else:
                self.viewtext.announce("DCC chat connection with %s lost" % nick)

    def dcc_connectionFailed(self, data=None):
        print "Connection failed"

    def dcc_lineReceived(self, line, data=None):
        self.handle_message(data.nick, self.nick(), line, dcc=1)

    ##
    ## handling of dcc commands
    def dcc_handle_input(self, source, rest):
        if ' ' in rest:
            cmd, rest = split(rest, ' ', 1)
        else:
            cmd, rest = rest, ""

        if cmd == 'chat' and rest:
            self.dcc_start_chat(rest)

        if cmd == 'send' and rest:
            nick, file = split(rest, " ")
            self.dcc_send_file(nick, file)
            

    ##
    ## handling of view events
    def view_startdcc(self, nick):
        print "DCC", nick
        self.dcc_start_chat(nick)
