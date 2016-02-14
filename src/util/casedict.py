#!/usr/bin/python
""" Implementation of a case insensitive dictionary """

# $Id: casedict.py,v 1.2 2001/09/09 23:10:07 ivo Exp $

from string import lower
from UserDict import UserDict

class casedict(UserDict):
    def __init__(self, **kwargs):
	self._dict = {}
	UserDict.__init__(self, self._dict)
	for i in kwargs.keys():
	    self[i] = kwargs[i]
    def __getitem__(self, key):
        return UserDict.__getitem__(self, lower(key))
    def __setitem__(self, key, value):
        UserDict.__setitem__(self, lower(key), value)
    def has_key(self, key):
        return UserDict.has_key(self, lower(key))
    def get(self, key, default=None):
        return UserDict.get(self, lower(key), default)
    def __delitem__(self, key):
        UserDict.__delitem__(self, lower(key))

if __name__ == '__main__':
    d = casedict(Foo='bar', BlaH=20)
    d['HeLLo'] = 10
    print d
    print d['helLo']
    print d.values()
    del d['FOO']
    print d
