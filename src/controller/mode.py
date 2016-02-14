#!/usr/bin/python

# $Id: mode.py,v 1.3 2002/02/05 17:44:25 ivo Exp $

"""
    Class to parse modes. The class is initialized with a modestring,
    the result methods will provide the parsed plus/min modes and 
    parameters.

    TODO: banlist support?
"""

""" Handle messages like:

	Vlads!^ivo@struis.intranet.amaze.nl MODE #foo +o Test 
	Test MODE Test :-i
        VladDrac!~ivo@10.34.213.210 MODE #foo +bol b*!*@* MostUser 23
	VladDrac!~ivo@10.34.213.210 MODE #foo +t-l

        :struis.intranet.amaze.nl 324 Vads #foo +tnl 12

	x!~y@1.2.3.4 MODE #foo +l 21 
	 Nick: x
         Origin: x!~y@1.2.3.4
         Target: #foo
         Command: MODE
         rest: +l
         rest: 21 
	
	Alternative interface for this class: get params by mode
	or, return plus/minmodes in (mode, param) pairs, i.e.
	+ookl Foo Bar key 12 -> (o, Foo), (o, Bar), (k, key), (l, 12)
"""

from string import *

class mode:
    def __init__(self, mode=None):
	self._plusmodes = ""
	self._minmodes = ""
	self._plusparams = ""
	self._minparams = ""
        self.setmode(mode)

    def setmode(self, mode):
	if type(mode) in (type(()), type([])):
            self.mode = mode
	else:
	    self.mode = split(mode, ' ')
	self.parse()

    def parse(self):
	modechars = self.mode[0]
	modeparams = self.mode[1:]
        plusmodes = ""
	minmodes = ""
	plusparams = []
	minparams = []

	# XXX There's too much duplications here
	#
	# Are plusmodes always defined to come first?
        pcount = 0
	if modechars[0] == '+':
	    min_start = find(modechars, '-')
	    if min_start != -1:
                plusmodes,minmodes = split(modechars[1:], '-')
	    else:
	        plusmodes = modechars[1:]
            for i in plusmodes:
                if i in 'volkbIe':    # modes that require a parameter
		    if len(modeparams) > pcount:
	                plusparams.append(modeparams[pcount])
   	                pcount = pcount + 1
		    else:
		        plusparams.append("") # or None?
                else:
                    plusparams.append("")
	    for i in minmodes:
                if i in 'vobIe':    # modes that require a parameter
	            minparams.append(modeparams[pcount])
	            pcount = pcount + 1
                else:
                    minparams.append("")

	elif modechars[0] == '-':
	    plus_start = find(modechars, '+')
	    if plus_start != -1:
                minmodes,plusmodes = split(modechars[1:], '+')
	    else:
	        minmodes = modechars[1:]
	    for i in minmodes:
                if i in 'vobIe':    # modes that require a parameter
	            minparams.append(modeparams[pcount])
	            pcount = pcount + 1
                else:
                    minparams.append("")
            for i in plusmodes:
                if i in 'volkbIe':    # modes that require a parameter
		    if len(modeparams) > pcount:
	                plusparams.append(modeparams[pcount])
   	                pcount = pcount + 1
		    else:
		        plusparams.append("") # or None?
                else:
                    plusparams.append("")
        self._plusmodes = plusmodes
	self._minmodes = minmodes
	self._plusparams = plusparams
	self._minparams = minparams

    def plusmodes(self):
        return self._plusmodes

    def minmodes(self):
        return self._minmodes

    def plusmode(self, index):
        return self._plusmodes[index]

    def minmode(self, index):
        return self._minmodes[index]

    def plusparams(self):
        return self._plusparams

    def minparams(self):
        return self._minparams

    def plusparam(self, index):
        return self._plusparams[index]

    def minparam(self, index):
        return self._minparams[index]

if __name__ == '__main__':
    # you won't get them as complex as the first on irc.
    tests = [ "+tnokb-lib VladDrac key *!*@* *!*@*.nl",
              "+tnkl",
	      "+-",
	      "+l- 10",
	      "-oo+oo Foo1 Foo2 Foo3 Foo4"]

    for i in tests:
        m = mode(i)
	print "String: %s" % i
        print "Plusmodes: %s" % m.plusmodes()
        print "Minmodes: %s" % m.minmodes()
        print "Plusparams: "
        print m.plusparams()
        print "Minparams:"
        print m.minparams()
