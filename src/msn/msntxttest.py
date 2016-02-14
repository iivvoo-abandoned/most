#!/usr/bin/python

"""
    Text only test code for msn client code
"""

from clientlayer import *

from twisted.internet import main

class sbtestsession(client_sessioncallback):
    def __init__(self, session):
        self.session = session
        self.session.sethandler(self)

    def message_received(self, handle, headers, body):
        print "sb", headers,body
        self.session.sendmessage("Hi %s, you said: %s" % (handle, body))

    def handle_bye(self, handle):
        print "User left: ", handle

    ## network related
    def connectionMade(self):
        print "Connection to switchboard established"

    def connectionLost(self):
        print "Connection to switchboard lost"

    def connectionFailed(self):
        print "Connection to switchboard failed"

class msntxttest(client_callback):
    def __init__(self, handle, passwd):
        self.msn = client(handle, passwd)
        self.msn.sethandler(self)

    def handle_invite(self, session):
        print "received invite from", session.invited_handle
        s = sbtestsession(session)
        self.msn.accept_session(session) # or session.accept() ?

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

    m = msntxttest(handle, password)
    main.run()
