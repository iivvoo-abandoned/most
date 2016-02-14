#!/usr/bin/python
"""
    This module contains various time formatting routines, etc.
    
    Well, at least one.
"""

# $Id: timefmt.py,v 1.1 2001/08/08 12:24:35 ivo Exp $

from string import join

def plural(i):
    if i == 1:
        return ""
    return "s"

def sec_to_str(sec):
    """ convert 4100 into 1 hour, 8 minutes and 20 seconds """
    sec = int(sec)

    if sec == 0:
        return "0 seconds"
    if sec == 1:
        return "1 second"
    res = []

    s = sec % 60
    m = (sec / 60) % 60
    h = (sec / 3600) % 24
    d = (sec / 86400)

    if d > 0:
        res.append("%d day%s" % (d, plural(d)))
    if h > 0:
        res.append("%d hour%s" % (h, plural(h)))
    if m > 0:
        res.append("%d minute%s" % (m, plural(m)))
    if s > 0:
        res.append("%d second%s" % (s, plural(s)))

    result = ""
    if len(res) > 1:
        result = join(res[:-1], " ")
        result = result + " and %s" % res[-1]
    else:
        result = res[-1]
    return result

if __name__ == '__main__':
    test = [ 0, 1, 30, 59, 60, 61, 120, 121, 900, 3599, 3600, 3601, 3661,
             7200, 7201, 12345, 34567 ]

    for i in test:
        print "%d second(s) is %s" % (i, sec_to_str(i))
