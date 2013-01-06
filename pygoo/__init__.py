#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PyGoo - An Object-Graph mapper
# Copyright (c) 2010-2013 Nicolas Wack <wackou@gmail.com>
#
# PyGoo is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PyGoo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

__version__ = '0.1-dev'
__all__ = ['MemoryObjectGraph', 'Equal', 'BaseObject']

# Do python3 detection before importing any other module, to be sure that
# it will then always be available
# with code from http://lucumr.pocoo.org/2011/1/22/forwards-compatible-python/
import sys
if sys.version_info[0] >= 3:
    PY3 = True
    unicode_text_type = str
    native_text_type = str
    base_text_type = str
    def u(x):
        return str(x)
    def s(x):
        return x
    class UnicodeMixin(object):
        __str__ = lambda x: x.__unicode__()
    import binascii
    def to_hex(x):
        return binascii.hexlify(x).decode('utf-8')

else:
    PY3 = False
    __all__ = [ str(s) for s in __all__ ] # fix imports for python2
    unicode_text_type = unicode
    native_text_type = str
    base_text_type = basestring
    def u(x):
        if isinstance(x, str):
            return x.decode('utf-8')
        return unicode(x)
    def s(x):
        if isinstance(x, unicode):
            return x.encode('utf-8')
        if isinstance(x, list):
            return [ s(y) for y in x ]
        if isinstance(x, tuple):
            return tuple(s(y) for y in x)
        if isinstance(x, dict):
            return dict((s(key), s(value)) for key, value in x.items())
        return x
    class UnicodeMixin(object):
        __str__ = lambda x: unicode(x).encode('utf-8')
    def to_hex(x):
        return x.encode('hex')

import logging

log = logging.getLogger(__name__)

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# let's be a nicely behaving library
log.addHandler(NullHandler())


from pygoo.memoryobjectgraph import MemoryObjectGraph
from pygoo.objectgraph import Equal
from pygoo.baseobject import BaseObject
