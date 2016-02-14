# $Id: ircController.py,v 1.59 2002/04/21 20:49:23 ivo Exp $

from net import *
import model

from view import ircView, viewHandler

from serverDispatcher import serverDispatcher

from string import *
from util import casedict, Log
from util.debug import debug, DEBUG, NOTICE, ERROR
from util.cfg import getCfg

from twisted.internet import main
from twisted.python import delay
#
# The controller mediates between state (model), view (gui) and external
# sources (network)
#
# There is a small bit of duplication in the channels dictionary which contains
# references to the several channelViews and the serverState.channels. However,
# there references don't belong in the model, just as the queries don't.
#
# It's probably not that bad to make shortcuts to the state's channel structures
# through this class' own channeldict


version = "v0.1"
default_quit = "Most %s, http://vanderwijk.info/most/" % version

class ircController(serverDispatcher, viewHandler):
    def __init__(self, servername):
        viewHandler.__init__(self)
        serverDispatcher.__init__(self)
        self.model = model.ircModel()
        # local, view related state
        self.channels = casedict()
        self.queries = casedict()
        #
        # Add ourself to the model as a server
        self.serverState = model.server()
        # save serverid in case we ever need to refer to it
        self.serverid = self.model.addServer(self.serverState)
        self.view = ircView.getIrcView()
        self.viewtext = self.view.new_view(servername)
        self.viewtext.setname(servername)
        self.cfg = getCfg()
        self.logger = Log(servername)

        self.notify = self.cfg('servers.notify', [])
        for i in self.notify:
            self.viewtext.notify_offline(i)

        self.notify_delayer = delay.Delayed()
        self.notify_delayer.ticktime = 10 # 1 tick = 10 sec
        self.notify_delayer.loop(self.send_notify, 2)
        main.addDelayed(self.notify_delayer)

    def setcallback(self, cb):
        self.handler = cb

    def set_handler(self, handler):
        self.new_handler = handler

    def run(self, nick, name, host, port=6667):
        self.viewtext.announce("Welcome to Most %s" % version)
        self.viewtext.set_handler(self)

        self.connect(host, port)

        self.serverState.state = model.server.STATE_CONNECTING
        self.serverState.name = name
        self.serverState.nick = nick

    def quit(self, msg = None):
        """ invoked to terminate this connection / the entire client (?) """
	if self.serverState.state != model.server.STATE_NOTCONNECTED:
            self.irc.quit(msg or default_quit)
            self.close()
        
    def connect(self, host, port=6667):
        """ connect to a new server """
        # what about server.STATE_CONNECTING ?

        if self.serverState.state in (model.server.STATE_CONNECTED,
           model.server.STATE_CONNECTING):
            self.viewtext.announce("Changing to server %s %d" % (host, port))
            self.quit("Changing servers")
        self.serverState.reset()

        self.viewtext.announce("Connecting to server %s %d" % (host, port))
        serverDispatcher.connect(self, host, port)
        self.serverState.state = model.server.STATE_CONNECTING

        # connect to new server
        
    def disconnect(self, msg="User disconnect"):
        """ simple disconnect, no reconnect, no quit """
        if self.serverState.state in (model.server.STATE_CONNECTED, 
           model.server.STATE_CONNECTING):
            self.viewtext.announce("Disconnecting...")
            self.quit(msg)
            self.stop()
        self.serverState.reset()
        self.reset()

    def reset(self):
        """ adjust widgets, etc after connection is closed """
        self.serverState.reset() # resets notify, etc.
        self.viewtext.reset()

    def send_notify(self):
        """ send notifies. This method runs in a Delayed """
        str = ""
	if self.serverState.state == model.server.STATE_CONNECTED:
            for i in self.notify:
                if len(str) + len(i) + 1 + 4 <= 512:
                    str = "%s %s" % (str, i)
                else:
                    self.irc.ison(str)
                    str = ""
            if str != "":
                self.irc.ison(str)

    # utility methods
    def isme(self, nick):
        return lower(self.nick()) == lower(nick)

    def nick(self):
        """ a shortcut """
        return self.serverState.nick

    ##
    ## Methods that implement view handlers
    def view_winclose(self, source, target):
        if target == None:
            self.viewtext.close_msgwin()
        elif self.channels.has_key(target):
            # if we're active on the channel, part it which will indirectly
            # cause the window to close. 
            c = self.serverState.getChannel(target)
            if c and (c.getstate() == model.channel.STATE_ACTIVE):
                self.irc.part(target)
            else:
                # we're not active - remove the window
                self.channels[target].destroy()
                del self.channels[target]
                self.viewtext.delete_channel(target)
        elif self.queries.has_key(target):
            # queries can be destroyed
            self.queries[target].destroy()
            del self.queries[target]
            self.viewtext.delete_query(target)
        else:
            debug(ERROR, "Received WIN_CLOSE event for unknown" \
                  "window: %s" % target)

    ##
    ## The parsing done here should be done elsewhere...
    def view_new(self, source, text):
        # the parsing that's done here should be moved elsewhere
        if text == None:
            self.viewtext.announce("Please specify a hostname")
            return
        text = strip(text)
        if text == "":
            # use source appropriately?
            self.viewtext.announce("Please specify a hostname")

        idx = find(text, ' ')
        if idx > -1:
            host = strip(text[:idx])
            try:
                port = int(text[idx+1:])
            except ValueError:
                # use source appropriately?
                self.viewtext.announce("Invalid port specified")
                return
        else:
            host = text
            port = 6667
            
        self.new_handler.meta_new(source, (host, port))

    def view_newquery(self, source, nick):
        if not self.queries.has_key(nick):
            self.queries[nick]= self.viewtext.create_query(nick)

    def view_whois(self, source, nick):
        ## XXX todo: schedule reply handling, send (optionally) back to
        ## source window
        self.irc.whois(nick)

    def view_kick(self, nick, channel, reason):
        self.irc.kick(nick, channel, reason)

    def view_nick(self, source, nick):
        self.irc.nick(nick)

    def view_topic(self, source, topic):
        self.irc.topic(source, topic)

    def view_mode(self, target, change, args):
        self.irc.mode(target, change, args)

    def view_sendmsg(self, source, msg):
        """ 
            handle MSG events, i.e. the sending of a message to a target, and
            the proper displaying of this action in the UI
        """
        ##
        ## If target starts with = - use dcc?
        for line in filter(None, split(msg, "\n")): # \r\n for windows?
            # consult state.channels in stead of own dictionary?
            if self.channels.has_key(source):
                self.irc.privmsg(source, line)
                self.channels[source].msg(self.nick(), line, isme=1)
            elif self.queries.has_key(source):
                q = self.queries[source]
                use_dcc = q.use_dcc()
                if use_dcc:
                    print "USE DCC", line
                    self.dcc_chat_send(source, line)
                else:
                    self.irc.privmsg(source, line)
                self.queries[source].msg(self.nick(), line, isme=1, dcc=use_dcc)
            elif self.cfg('client.use_msg_win', 1):
                m = self.viewtext.get_msgwin()
                m.sendmsg(source, line)
                # how about dcc?
                self.irc.privmsg(source, line)
            else:
                self.queries[source] = self.viewtext.create_query(source)
                self.queries[source].msg(self.nick(), line, isme=1)
                self.irc.privmsg(source, line)

            # log the message. Log differently for dcc?
            self.logger.log(source, "<%s> %s" % (self.nick(), line))

    def view_msg(self, source, msg):
        if ' ' in msg:
            target, msg = split(msg, ' ', 1)
        else:
            target, msg = msg, ""
        self.view_sendmsg(target, msg)

    def view_join(self, source, rest):
        if ' ' in rest:
            channel, rest = split(rest, " ", 1)
        else:
            channel, rest = rest, None
        self.irc.join(channel, rest)

    def view_leave(self, source, rest):
        if ' ' in rest:
            channel, rest = split(rest, " ", 1)
        else:
            channel, rest = rest, None
        self.irc.part(channel, rest)

    def view_action(self, source, rest):
        # XXX
        # action is implemented by class ctcp, inherited from serverDispatcher
        self.action(source, rest)
        if self.channels.has_key(source):
            self.channels[source].action(self.nick(), rest, isme=1)
        elif self.queries.has_key(source):
            self.queries[source].action(self.nick(), rest, isme=1)
        else:
            m = self.viewtext.get_msgwin()
            m.sendaction(self.nick(), source, rest)
        self.logger.log(source, "-> %s %s" % (self.nick(), rest))

    def view_whois(self, source, rest):
        self.irc.whois(rest)

    def view_whowas(self, source, rest):
        self.irc.whowas(rest)

    def view_away(self, source, rest):
        self.irc.away(rest)

    def view_who(self, source, rest):
        self.irc.who(rest)

    def view_invite(self, source, rest):
        self.irc.invite(rest, source)

    def view_raw(self, source, rest):
        self.irc.raw(rest)

    def view_connect(self, host, port):
        ## XXX won't work anymore (?!)
        self.connect(host, port)
