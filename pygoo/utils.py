#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PyGoo - An Object-Graph mapper
# Copyright (c) 2010 Nicolas Wack <wackou@gmail.com>
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

from pygoo.abstractnode import AbstractNode
from pygoo import ontology
import collections


# Nice & clean enum implementation by Gabriel Genellina, MIT licensed
# as found at http://code.activestate.com/recipes/577024-yet-another-enum-for-python/
def enum(typename, field_names):
    """Create a new enumeration type"""

    if isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    d = dict((reversed(nv) for nv in enumerate(field_names)), __slots__ = ())
    return type(typename, (object,), d)()


def to_utf8(obj):
    """Converts all unicode strings in the given object to utf-8 strings."""
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    elif isinstance(obj, list):
        return [ to_utf8(elem) for elem in obj ]
    elif isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[to_utf8(key)] = to_utf8(value)
        return result
    else:
        return obj

def multi_is_instance(value, cls):
    """Return whether given object is an instance of the given class, of is a
    sequence that contains only objects of the given class."""
    # FIXME: we might be calling this function a little bit too much...
    if isinstance(cls, (list, set)):
        cls = next(iter(cls))
    if isinstance(value, list):
        return all(isinstance(v, cls) for v in value)
    elif isinstance(value, collections.Iterator):
        # we can't touch the generator otherwise the values will be lost
        from pygoo.baseobject import BaseObject
        return issubclass(cls, AbstractNode) or issubclass(cls, BaseObject) # FIXME: this behaviour is debatable
    else:
        return isinstance(value, cls)



def is_of(name):
    """Return the "is-of" name for the given property."""
    return 'is%sOf' % (name[0].upper() + name[1:])

def is_literal(value):
    return (type(value) in ontology.validLiteralTypes or
            value is None) # TODO: is None could be checked here for validity in the schema


def check_class(name, value, schema, converters=None):
    """This function checks whether value can be converted to a valid type
    according to the schema, optionally using some converter function.

    Return the converted value if an adequate converter could be found, or
    the original value otherwise"""

    if converters:
        conv = converters.get(name)
        if conv is not None:
            value = conv(value)


    if name not in schema or multi_is_instance(value, schema[name]):
        return value


    # try to autoconvert a string to int or float
    if isinstance(value, basestring) and schema[name] in [ int, float ]:
        try:
            return schema[name](value)
        except ValueError:
            pass


    raise TypeError("The '%s' attribute is of type '%s' but you tried to assign it a '%s'"
                    % (name, schema[name], type(value)))


def reverse_name(cls, name):
    cname = cls.reverse_lookup.get(name)
    if cname is None:
        # TODO: asserts this never happens if ontology has no contradiction
        return is_of(name)
    elif isinstance(cname, (list, set)):
        return next(iter(cname))
    else:
        return cname


def reverse_lookup(d, cls):
    """Returns a list of tuples used mostly for node creation.
    They are triples of (name, literal value or node generator, reverseName).
    This also checks for type validity and converts the values if they have type converters.
    string -> unicode, string -> int  and  string -> float  are done automatically."""
    return [ (name,
              check_class(name, value, cls.schema, cls.converters),
              reverse_name(cls, name))
             for name, value in d.items() ]
