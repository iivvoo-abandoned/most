"""
    Implementation of the basic irc protocol
"""

# $Id: irc.py,v 1.12 2002/03/04 23:41:49 ivo Exp $

from twisted.protocols import basic
from twisted.internet import tcp

from string import *

def parsemsg(line):
    prefix = ''
    if line[0] == ':':
        prefix, line = split(line[1:], ' ', 1)
    args = []
    while len(line) > 0 and line[0] != ':' and ' ' in line:
        arg, line = split(line, ' ', 1)
        args.append(arg)
    if len(line) > 0:
        if line[0] == ':':
            args.append(line[1:])
        else:
            args.append(line)
    return prefix, args[0], args[1:]


##
## XXX define interface for handler

class irc(basic.LineReceiver):
    """
        This protocol level is just a python interface on top of the irc
        protocol - it provides appropriate methods and callback handling,
        but does not store any state or logic.
    """
    def __init__(self, handler):
        self.client = None
        self.running = 1
        self.errno = 0
        self.errstr = ""
        self.handler = None
        self.host = None
        self.port = -1
        self.handler = handler
        basic.LineReceiver.delimiter = "\n"

    def getHost(self):
        return self.transport.getHost()

    def close(self):
        if self.transport:
            self.transport.loseConnection()

    def connectionFailed(self):
        print "Connection failed"
        self.client = None
        self.errno = -1
        self.errstr = "Connection failed, Unknown error"
        self.handler.connectionFailed()

    def connectionLost(self):
        print "Connection lost"
        self.transport.loseConnection()
        self.client = None
        self.errno = -1
        self.errstr = "Connection lost, Unknown error"
        self.handler.connectionLost()

    def connectionMade(self):
        print "Connection established"
        self.handler.connectionMade()
        
    def lineReceived(self, line):
        if line[-1] == '\r':
            line = line[:-1]
        print "RECEIVED: ", line
        prefix, cmd, args = parsemsg(line)
        method = getattr(self.handler, "irc_%s" % cmd, None)
        if method is not None:
            method(cmd, prefix, args)
        else:
            self.handler.irc_unknown(cmd, prefix, args)

    def sendLine(self, msg):
        print "SENDING", msg
        self.transport.write(msg + "\r\n")
    ##
    ## methods for irc commands should be implemented by a deriving class
    ## - when available, the method will be invoked

    ##
    ## below are the methods to send irc messages. Perhaps all of these should
    ## be in a mix-in?

    def send(self, msg):
        """ low-level message sending with proper message termination """
        self.sendLine(msg)

    def privmsg(self, target, text):
        self.send("PRIVMSG %s :%s" % (target, text))

    def notice(self, target, text):
        self.send("NOTICE %s :%s" % (target, text))

    def join(self, target, key = None):
        if key:
            self.send("JOIN %s %s" % (target, key))
        else:
            self.send("JOIN %s" % target)

    def part(self, target, comment = None):
        if comment:
            self.send("PART %s :%s" % target, comment)
        else:
            self.send("PART %s" % target)

    def mode(self, target, change = None, args = []):
        """ for now, modes is a plain flat string. Perhaps replace with
            a dict or a list? """
        if args:
            self.send("MODE %s %s %s" % (target, change, join(args, " ")))

        elif change:
            self.send("MODE %s %s" % (target, change))
        else:
            self.send("MODE %s" % target)
        
    def invite(self, name, target):
        self.send("INVITE %s %s" % (name, target))

    def kick(self, name, channel, comment = None):
        if comment:
            self.send("KICK %s %s :%s" % (channel, name, comment))
        else:
            self.send("KICK %s %s" % (channel, name))

    def ison(self, names):
        if type(names) == type(""):
            self.send("ISON %s" % names)
        else:
            self.send("ISON %s" % string.join(names, " "))

    def nick(self, nick):
        self.send("NICK %s" % nick)

    def oper(self, nick, password):
        self.send("OPER %s %s" % (nick, password))

    def pong(self, to):
        self.send("PONG %s" % to)

    def topic(self, target, topic = None):
        if topic:
            self.send("TOPIC %s :%s" % (target, topic))
        else:
            self.send("TOPIC %s" % target)

    def quit(self, reason = None):
        if reason:
            self.send("QUIT :%s" % reason)
        else:
            self.send("QUIT")

    def whois(self, target, server = None):
        """ whois is a bit weird, you can specify an optional server (or a nick
            of someone on that server) and the whois will be performed on that
            server, resulting in slightly more info, such as away info """
        if server:
            self.send("WHOIS %s %s" % (server, target))
        else:
            self.send("WHOIS %s" % target)

    def whowas(self, target, server = None):
        """ seen whois for comments """
        if server:
            self.send("WHOWAS %s %s" % (server, target))
        else:
            self.send("WHOWAS %s" % target)

    def who(self, target):
        self.send("WHO %s" % target)

    def user(self, login, ircname):
        """ perform the user command 
        
            The correct syntax is: USER login myhost ircserver :IRCNAME
            but myhost / ircserver are ignored
        """
        # the 0 can be replaced with an initial usermode
        self.send("USER %s 0 * :%s" % (login, ircname))
        
    def away(self, message):
        if message:
            self.send("AWAY :%s" % message)
        else:
            self.send("AWAY")

    def raw(self, command):
        self.send(command)

class ctcp:
    """
        Implementation of the Client to Client protocol on top of IRC
    """

    def __init__(self, strict=0):
        self.strict = strict

    ## irc_PRIVMSG and irc_NOTICE are not invoked!!!
    def irc_PRIVMSG(self, command, prefix, args):
        msg = args[-1]
        target = args[0]
        sender = prefix

        if is_ctcp(msg):
            self.handle_ctcp(sender, target, msg, type=0)
        else:
            ##
            ## This mean that ctcp messages will be hidden from normal irc
            ## protocol handling
            self.irc.irc_PRIVMSG(command, prefix, args)

    def irc_NOTICE(self, command, prefix, args):
        msg = args[-1]
        target = args[0]
        sender = prefix

        if is_ctcp(msg):
            self.handle_ctcp(sender, target, msg, type=1)
        else:
            ##
            ## This mean that ctcp messages will be hidden from normal irc
            ## protocol handling
            self.irc.irc_NOTICE(command, prefix, args)

    def handle_ctcp(self, sender, target, msg, type=0, dcc=0):
        """
            Handle CTCP, either PRIVMSG or NOTICE (reply)
        """
        cmd, rest = "", ""
        print "CTCP", sender, target, msg, type
        ##
        ## Stip leading and (optionally) trailing ^A
        if msg[-1] == '\x01' and len(msg) > 1:
            msg = msg[1:-1]
        else:
            msg = msg[1:]
        if ' ' in msg:
            cmd, rest = split(msg, " ", 1)
        else:
            cmd = msg
        cmd = upper(cmd)
            
        method = None
        if type == 1: # reply
            method = getattr(self, "ctcp_reply_%s" % cmd, None)
        else:
            method = getattr(self, "ctcp_%s" % cmd, None)
        if method is not None:
            method(cmd, sender, target, rest)
        else:
            if type == 1:
                self.ctcp_reply_unknown(cmd, sender, target, rest)
            else:
                self.ctcp_unknown(cmd, sender, target, rest)

    ##
    ## Routines for sending ctcp messages

    def ctcp(self, target, type, msg):
        self.irc.privmsg(target, "\x01%s %s\x01" % (type, msg))

    def ctcpreply(self, target, type, msg):
        self.irc.notice(target, "\x01%s %s\x01" % (type, msg))

    def action(self, target, msg):
        self.ctcp(target, "ACTION", msg)

    ##
    ## kludgy static methods
    class is_ctcp_class:
        def __call__(self, string, strict=0):
            """ return true if the string is a ctcp encoded message """
            if strict:
                return len(string) > 2 and string[0] == string[-1] == '\x01'
            return len(string) > 1 and string[0] == '\x01'
    is_ctcp = is_ctcp_class()

def nickparse(nick):
    """ strip @ and + from a nickname. Assume a nick is never empty """
    if nick[0] in ('@','+'):
        return nick[1:], nick[0]
    return nick, None

def isserver(prefix):
    return find(prefix, '!') == -1 and find(prefix, '.') != -1

def ischannel(string):
    ##
    ## strictly: shoud not contain ' :,\x07
    return string[0] in '#&+!'

import model # XXX 

def mode2char(mode):
    """ 
        Convert a mode to a character representing the mode. Actually, 
        this somewhat determines the 'view', which should not be done here. 
        Use constants?  i.e. channelView.MODE_OP etc
    """
    if mode & model.user.MODE_OP:
        return '@'
    if mode & model.user.MODE_VOICE:
        return '+'
    return ' '

def getnick(name):
    idx = find(name, "!")
    if idx > -1:
        return name[:idx]
    return name

def getuserhost(name):
    idx = find(name, "!")
    if idx > -1:
        return name[idx+1:]
    return name
