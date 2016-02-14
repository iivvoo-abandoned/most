from string import split, find

from twisted.internet import tcp
from msn import messenger, switchboard_session

class msnuser:
    def __init__(self, handle, friendly, state='XXX'):
        pass

class client_sessioncallback:
    def connectionMade(self):
        pass

    def connectionFailed(self):
        pass

    def connectionLost(self):
        pass

    def message_received(self, handle, headers, body):
        pass

    def handle_bye(self, handle):
        pass

    def connectionMade(self):
        pass

    def connectionLost(self):
        pass

    def connectionFailed(self):
        pass


class sbsession:
    """
        There are two ways to create a session:

        - request a session through XFR
        - get invited by someone
    """

    CREATED = 0
    INVITED = 1

    def __init__(self, myhandle, host, port, challenge):
        self.myhandle = myhandle
        self.host = host
        self.port = port
        self.challenge = challenge
        self.ses = switchboard_session(myhandle, challenge,
                                       switchboard_session.INITIATE)
        self.ses.sethandler(self)
        self.handler = None
        self.type = sbsession.CREATED

    def sethandler(self, handler):
        self.handler = handler

    def invited(self, handle, friendly, sessionid):
        """ invoked if we get invited """
        self.invited_handle = handle
        self.invited_friendly = friendly
        self.sessionid = sessionid
        self.type = sbsession.INVITED
        self.ses.invited(handle, friendly, sessionid)

    def accept(self): 
        """ 
            accept the session. This means we can actually chose not to
            accept a session created by create_session
        """
        tcp.Client(self.host, self.port, self.ses)

    def sendmessage(self, msg):
        self.ses.sendmessage(msg)

    def invite(self, handle):
        self.ses.invite(handle)

    ## handlers invoked by underlying switchboard_session
    def connectionMade(self): # to be consistend with twisted
        self.handler.connectionMade()

    def message_received(self, handle, message):
        print "MSN session: received message", message
        ## split the message into headers and body
        ##
        ## This may fail with the *other* messages sent by the real msn client
        ## (those without body)
        headers = []
        body = ""
        if find(message, "\r\n\r\n") == -1:
            print "Can't handle message", message
            return

        header, body = split(message, "\r\n\r\n")
        for i in split(header, "\r\n"):
            headers.append(i)
        self.handler.message_received(handle, headers, body)

    def handle_bye(self, handle):
        self.handler.handle_bye(handle)

class client_callback:
    """
        interface for objects that implement the msn client callback
    """

    def handle_invite(self, session):
        """ invoked when we receive an invitation to join a session """
        pass

    def sbcreated(self, session):
        """ 
            invoked when we are ready to connect to a switchboard connection
            created by ourself
        """
        pass

    def handle_onlinechange(self, substate, handle, friendly):
    ## perhaps name statuschange?
        pass

    def handle_online(self, substate, handle, friendly):
        """ handle initial online status """
        pass

    def handle_offline(self, handle):
        """ handle offline change """
        pass

    def list_complete(self, type):
        """ notification that a list has been received completely """
        pass

class client:
    def __init__(self, handle, password, host=None, port=0):
        self.host = host or "messenger.hotmail.com"
        self.port = port or 1863
        self.handle = handle
        self.password = password

        self.msn = messenger(handle, password)
        tcp.Client(self.host, self.port, self.msn)
        
        self.msn.sethandler(self) 
        self.handler = None

    ## methods that can be invoked by the client

    def sethandler(self, handler):
        self.handler = handler

    def create_session(self):
        """ 
            request a connection to a switchboard 
            
            This will eventually result in xfr_sb and therefore
            self.handler.sbcreated being invoked
        """
        ## return the trid as an identifier
        return self.msn.xfr("SB") # XXX use constant

    def accept_session(self, session): # XXX
        """ 
            accept a session which was either created through a ring, 
            or throug create_session 
        
            Remove this method? XXX
        """
        session.accept()
        return session

    def reject_session(self, session):
        pass

    ## messenger events (define separate interface!)
    def xfr_ns(self, host, port):
        """ reconnect to new NS server """
        self.msn.close()
        self.host = host
        self.port = port
        self.msn.setMode(messenger.NS_MODE)
        tcp.Client(host, port, self.msn)

    def xfr_sb(self, trid, host, port, challenge):
        """ received after create_switchboardsession """
        s = sbsession(self.handle, host, port, challenge)
        self.handler.handle_sbcreated(int(trid), s)
        
    def ring(self, host, port, handle, friendly, challenge, sessionid):
        # pass info, give client change to accept/reject
        s = sbsession(self.handle, host, port, challenge)
        s.invited(handle, friendly, sessionid)
        # invoke client handler
        self.handler.handle_invite(s) # session invite?

    def message_received(self, message):
        print "MSN client: received message", message

    def list_complete(self, type):
        print "MSN client: list complete", type
        self.handler.list_complete(type)

    def getlists(self):
        return (self.msn.fl, self.msn.rl, self.msn.al, self.msn.bl)

    def handle_onlinechange(self, substate, handle, friendly):
    ## perhaps name statuschange?
        """ handle change in online status of friend """
        print "MSN client: online change", substate, handle, friendly
        self.handler.handle_onlinechange(substate, handle, friendly)

    def handle_online(self, substate, handle, friendly):
        """ handle initial online status """
        print "MSN client: online", substate, handle, friendly
        self.handler.handle_online(substate, handle, friendly)

    def handle_offline(self, handle):
        """ handle offline change """
        print "MSG client: offline", handle
        self.handler.handle_offline(handle)
