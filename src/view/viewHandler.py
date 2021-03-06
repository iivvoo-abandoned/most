"""
    Dispatch view events
"""

# $Id: viewHandler.py,v 1.9 2002/02/24 23:08:24 ivo Exp $

from string import *
import re
from net import * # irc protocol parsing

class viewHandler:
    def __init__(self):
        self.cmdmap = {
	"raw":		self.view_raw,
	"quote":	self.view_raw,
	"msg":		self.view_msg,
	"notice":	self.view_notice,
        "join": 	self.view_join,
        "leave": 	self.view_leave,
        "nick": 	self.view_nick,
        "whois": 	self.view_whois,
        "whowas": 	self.view_whowas,
        "who": 		self.view_who,
        "topic": 	self.view_topic,
        "away": 	self.view_away,
        "quit": 	self.view_quit,
        "invite": 	self.view_invite,

	"connect":	self.view_connect,
	"disconnect":	self.view_disconnect,
	"close":	self.view_disconnect,
	"new":	        self.view_new,

	"me":		self.view_action,
        "chat":         self.view_dcc_chat,
	
	"query":	self.view_newquery
        }

    def not_implemented(self, source, text): pass

    view_raw = view_msgnotice = view_join = view_leave = \
    view_kick = view_who = view_away = view_quit = view_notice  = \
    view_invite = view_new = view_connect = view_disconnect = view_action = \
    view_dcc_chat = not_implemented
    
    
    
    def handle_input(self, source, text):
	event = None
	if strip(text) != "":
	    if text[0] == '/':
                index = find(text, ' ', 1)
                if index == -1:
                    cmd = lower(text[1:])
                    rest = None
                else:
                    cmd = lower(text[1:index])
                    rest = text[index+1:]
                if hasattr(self, "cmd_%s" % cmd):
                    m = getattr(self, "cmd_%s" % cmd)
                    m(source, rest)
                elif self.cmdmap.has_key(cmd):
                    self.cmdmap[cmd](source, rest)
	    else:
                self.view_sendmsg(source, text)

    def cmd_kick(self, source, line):
        channel = source
        nicks = None
        reason = None

        if not line:
            return # raise ...

        line = lstrip(line)
        if ' ' in line:
            arg, rest = split(line, ' ', 1)
            if ischannel(arg):
                channel = arg
                line = rest
                if ' ' in line:
                    arg, rest = split(line, ' ', 1)
                    nick = arg
                    reason = line
                elif line == '':
                    pass # no nick specified
                else:
                    nick = line
            else:
                nick = arg
                reason = rest
        else:
            nick = line

        ##
        ## when done
        self.view_kick(nick, channel, reason)

    def cmd_connect(self, source, line):
        """ 
            connect to a new server

            syntax: /connect servername [portnumber]
        """

        host = None
        port = 6667
        
        args = filter(None, split(line, " "))
        if len(args) == 0:
            pass # no servername
        host = args[0]
        
        if len(args) == 2:
            try:
                port = int(args[1])
            except ValueError:
                pass # invalid portnumber
        self.view_connect(host, port)        

    def cmd_mode(self, source, line):
        """
            mode [target] modechange [params]

            Target can be a channel or a nick

            mode #Koffie +b-l *!*@*
            mode vladdrac +i
            mode +i (target=source, i.e. vladdrac or #foo)
            mode +o vladdrac (target=source)

            modere = r"([!#&]?\w+)?\s+[+-]\w+([+-]\w+)\s+((\w+)\s+)*(\w+)?\s*$"
        """

        target = None
        change = ""
        rest = []
        
        args = re.split("\s+", line)

        if len(args) == 0:
            pass # no args
        if args[0][0] in ('+', '-'):  # no target
            change = args[0]
            rest = args[1:]
        else:
            if len(args) < 2:
                pass # modechange missing
            target = args[0]
            change = args[1]
            rest = args[2:]

        if target == None:
            if source == None:
                pass # no target
            else:
                target = source
        self.view_mode(target, change, rest)

    def cmd_dcc(self, source, rest):
        self.dcc_handle_input(source, rest)

    ##
    ## Generic UI events
    def view_winclose(self, source, target):
        pass

    def view_startdcc(self, name):
        print "FOEI"
    ##
    ## irc specific events
    def view_newquery(self, source, nick):
        pass

    def view_whois(self, source, nick):
        pass

    def view_whowas(self, source, nick):
        pass

    # add source for consistency?

    def view_nick(self, source, nick):
        pass

    def view_kick(self, source, nick):
        pass

    def view_topic(self, source, topic):
        pass

    def view_sendmsg(self, source, msg):
        pass

    def view_msg(self, source, msg):
        pass
