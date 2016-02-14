#!/usr/bin/python2.1

import socket, select, fcntl, FCNTL
import md5
from string import *

# twisted stuff
from twisted.protocols import basic
from twisted.internet import tcp

"""

Je bent initieel connected met (precies) 1 NS. Je kan geinvite worden
naar een SB sessie (met N mensen, 1 <= N <= MAX): RNG. Een ring bevat
de SB info, en beantwoord je met een ANS naar de SB

Je kan ook zelf een SB sessie opstarten: XFR. Als reaktie komt een XFR
met connect gegevens. Vervolgens kan je iemand in
deze session inviten via CAL

- is het mogelijk om meerdere SB sessies te hebben met dezelfde user? 
  (denk 't wel - i.e. multi user en private)
  
Een client kan 2 vormen van functionaliteit willen:

- 1-1 sessie openen met gebruiker, waar later andere users bij uitgenodigd
  kunnen worden
- n-n sessie, evt. gejoined, etc.

Laat de keuze over aan client - i.e. client maakt sb sessie aan, invite 
vervolgens users.

"""

##
## The lists
##
## FL = Forward List - The list of users for whom a given user wants to
##      receive state change notifications.
## RL = Reverse List - The list of users who have registered an
##      interest in seeing this user's state change notifications.
## AL = Allow List - The list of users who the user has explicitly
##      allowed to see state change notifications and establish client-to-
##      client sessions via a Switchboard Server.
## BL = Ban List - The list of users who the user has explicitly
##      prevented from seeing state change notifications and establishing
##      client-to-client sessions via a Switchboard Server.

class event:
    """
        The event class implements simple messages that can be send to
        handles by messenger or switchboard_session
    """

    EV_ONLINE = 1
    EV_OFFLINE = 2
    EV_LISTCOMPLETE = 3
    EV_MSG = 4                          ## there's also EV_SB_MSG!
    EV_RING = 5
    ##
    ## switchboard specific messages
    EV_SB_CONNECTED = 128
    EV_SB_DISCONNECTED = 129
    EV_SB_MSG = 130

    def __init__(self, type=-1):
        self.type = type
        self.args = None

class messaging_support:
    """
        This class implements basic messaging/message handling between 
        the client and notification/switchboard servers
    """
    ##
    ## Assumes self.sock. perhaps cleaner to invoke 'abstract' method getsock()?
    def __init__(self):
        self.trid = 0

    def send(self, cmd, args="", crlf=1):
        """ send a command to the server. Automatically insert a new trid,
            and return it """
        id = self.trid
        self.trid = self.trid + 1
        message = "%s %d %s" % (upper(cmd), id, args)
        print "Sending: ", message

        if crlf:
            self.transport.write("%s\r\n" % message)
        else:
            self.transport.write("%s" % (message))
        return id

    ##
    ## Low level MSN commands

    def ans(self, handle, challenge, sessionid):
        # ANS TrID LocalUserHandle AuthResponseInfo SessionID
        return self.send("ANS", "%s %s %s" % (handle, challenge, sessionid))

    def ver(self, protocol=None):
        return self.send("VER", protocol or self.protocol)

    def inf(self):
        return self.send("INF")
        
    def usr(self, SP, args):
        """ SP = security package """
        if SP == None:
            return self.send("USR", args)
        return self.send("USR", "%s %s" % (SP, args))
        
    def syn(self, serial=1):
        """ send a syn with optional serial """
        #
        # Fail if not connected?
        return self.send("SYN", "%s" % serial)

##   NLN - Online
##   FLN - OFFLINE
##   HDN - HIDDEN
##   other States currently supported are:
##   BSY - Busy.
##   IDL - Idle.
##   BRB - Be Right Back.
##   AWY - Away From Computer.
##   PHN - On The Phone.
##   LUN - Out To Lunch.

    def chg(self, status):
        """ change status """
        return self.send("CHG", status)

    def add(self, list, handle, friendly):
        """ add a user to a list """
        # list must be in ('FL', 'RL', 'AL', 'BL')
        return self.send("ADD", "%s %s %s" % (list, handle, friendly))

    def rem(self, list, handle):
        """ remove a user from a list """
        return self.send("REM", "%s %s" % (list, handle))

    def xfr(self, server_type):
        """ request a connection to a server, usually SB """
        return self.send("XFR", server_type)

    def cal(self, handle):
        """ invite someone to the SB - SB only """
        return self.send("CAL", handle)

    def msg(self, delivery, message):
        """ 
            send a message, 'delivery' is ack type,
            U for UNACKNOWLEDGED, A for ACK, N for NACK 
        """
        message = strip(message)
        mime_message = "MIME-Version: 1.0\r\n" + \
                       "Content-Type: text/plain; charset=UTF-8\r\n" + \
                       "X-MMS-IM-Format: FN=MS%20Sans%20Serif; EF=; " + \
                       "CO=0; CS=0; PF=0\r\n\r\n" + message
        self.send("MSG", "%s %d\r\n%s" % \
                  (delivery, len(mime_message),mime_message), crlf=0)

##
## a switchboard can be started or accepted, and can be 1-N
## however, currently the implementation is very 1-1
class switchboard_session(messaging_support, basic.LineReceiver):
    """
        A switchboard session is usually a 1-N chat which can be initiated
        or accepted
    """
    INITIATE = 0
    ACCEPT = 1

    def __init__(self, myhandle):
        messaging_support.__init__(self)

        self.host = None
        self.port = -1
        self.myhandle = myhandle
        self.handle = None
        self.friendly = None
        self.challenge = None
        self.sessionid = None
        self.handler = None
        self.connected = 0
        self.mode = switchboard_session.INITIATE

        ## to store raw received messages
        self.msgbuffer = ""
        self.msglen = -1

    def connectionMade(self):
        if self.mode == switchboard_session.INITIATE:
            self.usr(SP=None, args="%s %s" % (self.myhandle, self.challenge))
        else: # accept
            self.ans(self.myhandle, self.challenge, self.sessionid)
        if self.handler:
            e = event(event.EV_SB_CONNECTED)
            e.args = None
            self.handler(e)
        self.connected = 1

    def sethandler(self, handler):
        self.handler = handler

    def invite(self, handle):
        """ invite 'handle' to this switchboard session """
        self.cal(handle)

    ##
    ## initiate / establish are rather similar
    def initiate(self, host, port):
        self.host = host
        self.port = port
        self.mode = switchboard_session.INITIATE
        self.client = tcp.Client(self.host, self.port, self)

    def establish(self, host, port, handle, friendly, challenge, sessionid):
        self.addr = (host, port)
        self.handle = handle 
        self.friendly = friendly
        self.challenge = challenge
        self.sessionid = sessionid
        self.mode = switchboard_session.ACCEPT

        self.con = tcp.Client(self.addr[0], self.addr[1], self)

    def sendmessage(self, msg):
        """ send a (text)message to the SB """
        self.msg("N", msg)

    def lineReceived(self, line):
        ## we may receive a message that indicates that data follows, starting
        ## with a specific size. This requires some messing with the MSGBuffer..
        dispatchers = { 'ANS':self.handle_ans,
                        'IRO':self.handle_iro,
                        'MSG':self.handle_msg,
                        'BYE':self.handle_bye
                      }
        if strip(line) == "":
            return
        args = split(strip(line))
        if dispatchers.has_key(args[0]):
            dispatchers[args[0]](args)

    def handle_ans(self, args):
        pass

    def handle_iro(self, args):
        pass

    def handle_bye(self, args):
        ## Wrong implementation
        #self.sock.close()
        #self.connected = 0
        if self.handler:
            e = event(event.EV_SB_DISCONNECTED)
            e.args = None
            self.handler(e)

    def handle_msg(self, args):
        ##
        ## VERY similar to messenger.handle_msg

        (cmd, handle, friendly, len) = args
        self.msglen = int(len)
        self.msgbuffer = "" # just to make sure?

        self.setRawMode()
        ##message = self.raw_read(int(len))
        ##print "Message received: ", message
        ##e = event(event.EV_SB_MSG)
        ##e.args = message
        ##if self.handler:
        ##    self.handler(e)

    def rawDataReceived(self, data):
        ##
        ## VERY similar to messenger.handle_msg (except for exact event type)

        print "RAW received: " + data
        self.msgbuffer = self.msgbuffer + data

        if len(self.msgbuffer) >= self.msglen:
            print "Message is complete"
            ##
            ## Message is complete, generate event.
            e = event(event.EV_SB_MSG)
            e.args = self.msgbuffer[:self.msglen]
            if self.handler:
                self.handler(e)
            self.setLineMode(self.msgbuffer[self.msglen:])
            ## clear buffer
            self.msgbuffer = ""
            self.msglen = -1

class messenger(messaging_support, basic.LineReceiver):
    def __init__(self, handle, password, type=0):
        messaging_support.__init__(self)
        self.server="messenger.hotmail.com"
        self.handle = handle
        self.password = password
        self.port=1863
        self.type = type
        self.trid = 0

        self.client = tcp.Client(self.server, self.port, self)
        self.protocol = "MSNP2"
        ##
        ## The contact lists: FL/RL/AL/BL 
        ## for Forward List, Reverse List, Allow List and Block List,
        self.fl = []
        self.rl = []
        self.al = []
        self.bl = []
        ## self.serial?
        self.sessions = []
        self.pending_sessions = {}

        self.handler = None
        
        ## to store raw received messages
        self.msgbuffer = ""
        self.msglen = -1

    def connectionMade(self):
        """
            type 0: DS
                 1: NS
        """
        ## Non-dispatch servers behave weird when INF is requested
        if self.type == 0:
            self.ver()
            self.inf()
        else:
            self.ver()
        self.login()

    def lineReceived(self, line):
        ##
        ## Read individual messages and dispatch them (internally or by
        ## invoking handlers).
        ##
        ## Alternatively, translate message to method and invoke method
        ## (and move this to generic baseclass)
        ##
        ## Do actual connect here?
        dispatchers = { 'XFR':self.handle_xfr,
                        'VER':self.handle_ver,
                        'INF':self.handle_inf,
                        'USR':self.handle_usr,
                        'LST':self.handle_lst,
                        'RNG':self.handle_rng,
                        'NLN':self.handle_nln,
                        'FLN':self.handle_fln,
                        'ILN':self.handle_iln,
                        'MSG':self.handle_msg 
                      }
                        
        print "NS Received: ", line
        if strip(line) == "":
            return
        args = split(strip(line))
        if dispatchers.has_key(args[0]):
            dispatchers[args[0]](args)
        else:
            print "Couldn't handle", args

    def rawDataReceived(self, data):
        """
            Invoked when raw data is available. The messenger switches to
            raw data mode after receiving a MSG message. Once the complete
            message has been received, the messenger switches back to normal
            line mode.
        """

        print "RAW received: " + data
        self.msgbuffer = self.msgbuffer + data

        if len(self.msgbuffer) >= self.msglen:
            print "Message is complete"
            ##
            ## Message is complete, generate event.
            e = event(event.EV_MSG)
            e.args = self.msgbuffer[:self.msglen]
            if self.handler:
                self.handler(e)
            self.setLineMode(self.msgbuffer[self.msglen:])
            ## clear buffer
            self.msgbuffer = ""
            self.msglen = -1

    def sethandler(self, handler):
        self.handler = handler

    def create_sb(self):
        """ create a connection to the switchboard """
        ss = switchboard_session(self.handle)
        trid = self.xfr("SB")
        self.pending_sessions[trid] = ss
        return ss

    def remove_sb(self, sb):
        self.sessions.remove(sb)

    def login(self, handle=None, password=None):
        """ Login to msn """
        if handle:
            self.handle = handle
        if password:
            self.password = password
        ##
        ## the MD5 is actually a INF response, which should be handled and
        ## stored appropriately
        self.usr("MD5", "I %s" % self.handle)
        

    ##
    ## Internal handlers

    def handle_xfr(self, args):
        """ handle an xfr. Can be either NS or SB. Currently only handle NS """
        ##
        ## Determine type of xfr, i.e. to what are we being xfr'd?
        if args[2] == 'NS':
            ##
            ## xfr to notificationserver -- reconnect
            (h,p) = split(args[3], ":")
            (self.server, self.port) = (h, int(p))
            print "Moving to %s:%d" % (self.server, self.port)
            self.type = 1 # now connected to a NS
            self.transport.loseConnection()
            self.client = tcp.Client(self.server, self.port, self)
        elif args[2] == 'SB':
            ##
            ## xfr to switchboard -- create sb session
            (cmd, trid, type, hostip, sp, challenge) = args
            ##
            ## host, port, myhandle, handle, 
            ## friendly, challenge, sessionid):
            (host, port) = (lambda x: (x[0], int(x[1])))(split(hostip, ":"))
            ss = self.pending_sessions[int(trid)] ## must be valid
            ss.challenge = challenge ## UGLY XXX
            ss.initiate(host, port)
            del self.pending_sessions[int(trid)]
            self.sessions.append(ss)

    def handle_usr(self, args):
        """ handle usr, which can be a challenge, a greet, or more... """
        if len(args) == 5 and args[2] != "OK": # ugly, but works for now.
            print "Server gives challenge %s" % (args[4])
            challenge = "%s%s" % (args[4], self.password)
            md5challenge = md5.new()
            md5challenge.update(challenge)
            digest = md5challenge.digest() 

            ## 1.5.2 lacks hexdigest()
            coded_digest = reduce(lambda x, y:"%s%02x" % (x,ord(y)), digest, "")
            self.usr("MD5", "S %s" % coded_digest)
        else:
            print "Login succeeded, I guess"
            self.syn()
            self.chg("NLN") # go online

    def handle_ver(self, args=None):
        pass

    def handle_inf(self, args=None):
        pass

    def handle_lst(self, args):
        """ 
         handle the LST message: LST trid LIST ser# item# total# handle friendly
        """ 
        # FL/RL/AL/BL
        if int(args[5]) > 0: #  and len(args) == 8:
            if args[2] == 'FL':
                self.fl.append((args[6], args[7]))
            elif args[2] == 'RL':
                self.rl.append((args[6], args[7]))
            elif args[2] == 'AL':
                self.al.append((args[6], args[7]))
            elif args[2] == 'BL':
                self.bl.append((args[6], args[7]))
            if args[4] == args[5]:
                e = event(event.EV_LISTCOMPLETE)
                e.args = args[2]
                self.handler(e)

    def handle_rng(self, args): 
        # RNG SessionID SwitchboardServerAddress SP AuthChallengeInfo
        #   CallingUserHandle CallingUserFriendlyName
        (h,p) = split(args[2], ":")
        (host, port) = (h, int(p))
        (sessionid, challenge, handle, friendly) = \
                                      (args[1], args[4], args[5], args[6])
        
        ss = switchboard_session(self.handle)
        ##
        ## Actually, the client may wish to reject...
        ss.establish(host, port, handle, friendly, challenge, sessionid)
        e = event(event.EV_RING)
        e.args = (handle, ss) # add friendly
        self.handler(e)
        self.sessions.append(ss)

    def handle_nln(self, args):
        """ handle online state change """
        e = event(event.EV_ONLINE)
        e.args = (args[1], args[2], args[3])
        self.handler(e)

    def handle_iln(self, args):
        """ handle initial online state notification """
        e = event(event.EV_ONLINE)
        e.args = (args[2], args[3], args[4])
        self.handler(e)

    def handle_fln(self, args):
        """ handle offline state change """
        e = event(event.EV_OFFLINE)
        e.args = args[1]
        self.handler(e)

    def handle_msg(self, args):
        """ handle incoming messages, can be msn noise as well """
        (cmd, handle, friendly, len) = args
        self.msglen = int(len)
        self.msgbuffer = "" # just to make sure?

        self.setRawMode()
        ## message = self.raw_read(int(len))
        ##print "Message received: ", message
        ##e = event(event.EV_MSG)
        ##e.args = message
        ##if self.handler:
        ##    self.handler(e)



##   In the current implementation the Dispatch Server uses the user
##   handle provided in the initial USR command above to assign the user
##   in question to a Notification Server. Alternate implementations
##   might not require referral at this stage.
##
## Does this mean we can basically connect to 'our' server immediately?
