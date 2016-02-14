import sys
if sys.platform[:4] != 'java':
    import new, copy

# $Id: Extender.py,v 1.4 2001/10/15 08:06:22 ivo Exp $

"""
    This method implements the creation of new instances based on 
    an existing instance and a class. Basically it allows you to
    dynamically make an existing object be a base for a new object

    This module won't work with jython as it lacks the module 'new'
"""

def Extender(clazz, base, name, shallow=0):
    """ 
        extend base with class dynamically. Thanks to radix for 
        this solution 
    """

    # todo: *args / **args to be passed to __init__
    if shallow:
        newbase = base
    else:
        newbase = copy.copy(base)
    newbase.__class__ = new.classobj(name, (newbase.__class__, clazz), {})
    clazz.__init__(newbase)
    return newbase
