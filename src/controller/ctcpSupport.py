from string import *
import re
from util import net
from net.irc import getnick
from dccSupport import dccSupport

class ctcpSupport(dccSupport):
    def __init__(self):
        dccSupport.__init__(self)

    def ctcp_ACTION(self, type, sender, target, rest, dcc=0):
        nick = getnick(sender)
        if self.channels.has_key(target):
            self.channels[target].action(nick, rest)
        elif self.queries.has_key(nick):
            self.queries[nick].action(nick, rest, dcc=dcc)
        elif self.cfg('client.use_msg_win'):
            msg = self.viewtext.get_msgwin()
            # assert: self.isme(target) ?
            msg.action(nick, rest, dcc=dcc)
        else:
            self.queries[nick] = self.viewtext.create_query(nick)
            self.queries[nick].action(nick, rest, dcc=dcc)
        self.logger.log(target, "-> %s %s" % (nick, rest))

    def ctcp_VERSION(self, type, sender, target, rest):
        self.ctcpreply(getnick(sender), "VERSION", 
                               "MOST irc %s, %s" % (self.cfg("client.version"),
                               self.cfg("client.home")))

    def ctcp_DCC(self, type, sender, target, rest):
        ##
        ## rest looks like: <type> <argument> <host> <port> [size]
        ## <argument> is a filename, or 'CHAT' for dcc chat
        dcc_args = re.split("\s+", rest)
        nick = getnick(sender)
        if len(dcc_args) < 4:
            print "Invalid number of args for dcc chat"
            # report? XXX
            return
        type, file, dcchost, strport = dcc_args[:4]
        type = lower(type)
        try:
            port = atoi(strport)
        except ValueError:
            print "Invalid port for dcc"
            # report, reply, XXX
            return
        try:
            host = net.inet_ntoa(long(dcchost))
        except:
            print "Invalid host for dcc"
            # report, reply, XXX
            return
  
        if type == 'chat':
            if len(dcc_args) < 4:
                print "Invalid number of args for dcc chat"
                # report? XXX
                return

            ##
            ## check if 1024 < port < 65536
            ## perhaps deny multicast range.
            ## local ip's are okay, basically.
            ## also, usually host and senders host must match, right?
            ## we could enfore this in a strict mode
            ##
            ## this invokes a method from dccSupport, which is inherited 
            ## elsewhere..
            ##
            ## More checks on parameters to avoid exceptions
            self.dcc_accept_chat(nick, host, port)
        elif type == 'send':
            print dcc_args
            if len(dcc_args) >= 5:
                strsize = dcc_args[4]
            elif len(dcc_args) == 4:
                size = 0
            else:
                print "Invalid number of args for dcc send"
                # report? XXX
                return
            try:
                size = int(strsize)
            except ValueError:
                size = 0 # why not...
            ##
            ## check type of 'size'
            self.dcc_accept_file(nick, host, port, file, size)
        else:
            self.ctcpreply(nick, "ERROR", "I don't support DCC %s" % type)

    def ctcp_unknown(self, type, sender, target, rest):
        ##
        ## XXX we may not want to do this with public ctcp's
        self.ctcpreply(getnick(sender), "ERROR", "WHAT YOU SAY?")

    def ctcp_reply_unknown(self, type, sender, target, rest):
        self.view.announce("Received a CTCP %s reply from %s: %s" % \
                           (type, getnick(sender), rest))
