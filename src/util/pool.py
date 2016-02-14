# $Id: pool.py,v 1.2 2001/07/23 00:03:56 ivo Exp $

"""
   Implement a (dynamically growing) pool of objects

   It allows passing 
"""

class pool:
    def __init__(self, factory, size=0):
        """ todo: **args that need to be passed to factory 
	
	    size = 0 => unlimited
	"""
        self.factory = factory
	self.size = size
	self.pool = []
	self.free = []

    def get(self):
        if len(self.free) == 0:
	    item = self.factory()
	    self.pool.append(item)
	    return item
	return self.free.pop()

    def release(self, item):
        self.pool.remove(item)
	self.free.append(item)

    def add(self, item):
        """ explicitly add an item to the (free)pool """
	self.free.append(item)

    def remove(self, item):
        """ explicitly delete an item from the (free) pool """
	self.free.remove(item)

    
