#!/usr/bin/python

"""
    python 1.5.2 lacks some networking routines. This module implements
    them (as I don't want to drop 1.5.2 compatibility atm)

"""

# $Id: net.py,v 1.2 2001/11/19 00:47:49 ivo Exp $

from string import split
import socket, fcntl, FCNTL

def inet_aton(str):
    """ 
        convert quated dot notation to a int 
    
        python 2.x's inet_aton returns a string containing the network
        representation. This is according to the C inet_aton
    """
    
    n = 0
    quads = split(str, ".")
    if len(quads) != 4:
        raise socket.error, "illegal IP address string passed to inet_aton"
    for i in quads:
        try:
            j = int(i)
            if not(0 <= j <= 255):
                raise socket.error, \
                      "illegal IP address string passed to inet_aton"
        except ValueError:
            raise socket.error, "illegal IP address string passed to inet_aton"
    n = (int(quads[0]) << 24) + (int(quads[1]) << 16) + \
        (int(quads[2]) << 8) + int(quads[3])
    return n

def inet_ntoa(addr):
    """
        Do the reverse of inet_aton, return the quad notation of 'addr'
        which is a long containing the network address
    """
    quad = [0,0,0,0]
    
    for i in (0,1,2,3):
        quad[i] = (addr >> (8*(3-i))) & 0xFF
    return "%u.%u.%u.%u" % tuple(quad)
        
def make_nonblocking(fd):
    fl = fcntl.fcntl(fd, FCNTL.F_GETFL)
    try:
        fcntl.fcntl(fd, FCNTL.F_SETFL, fl | FCNTL.O_NDELAY)
    except AttributeError:
        fcntl.fcntl(fd, FCNTL.F_SETFL, fl | FCNTL.FNDELAY)

if __name__ == '__main__':
    print "Testing inet_aton"
    for i in ('0.0.0.0', '127.0.0.1', '255.255.255.255', '10.0.0.1'):
        print "%s -> %lu" % (i, inet_aton(i))
    print "The following wil fail"

    for i in ('0.0.0.0.0', '127.0.0', '256.255.255.255', 'www.amaze.nl'):
        try:
            print "%s -> %lu" % (i, inet_aton(i))
        except socket.error:
            print "Could not translate %s" % i

    print "Testing inet_ntoa"
    for i in ('0.0.0.0', '127.0.0.1', '255.255.255.255', '10.0.0.1'):
        print "%s -> %s" % (i, inet_ntoa(inet_aton(i)))
