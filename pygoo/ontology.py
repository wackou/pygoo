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

import weakref
import logging
import sys

log = logging.getLogger('pygoo.Ontology')

# use dict here for fast text based access (when instantiating objects through a graph, for instance)
_classes = {}
_graphs = weakref.WeakValueDictionary()

# Note: voluntarily omit to put str as allowed types, unicode is much better
#       and it will save us a *lot* of trouble
# Note: list should only be list of literal values
# TODO: add datetime
validLiteralTypes = [ unicode, int, long, float ] #, list ]





class Schema(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._implicit = set(args[0]._implicit) if args and isinstance(args[0], Schema) else set()

# dict of name to ontologies
# ontologies are (_classes, class variables)
_saved_ontologies = {}

def revalidate_graphs():
    """revalidate all ObjectNodes in all registered Graphs."""
    for g in _graphs.values():
        g.revalidate_objects()

def save_current_ontology(name):
    # we need to make a copy of the elements here, and of the properties explicitly
    # as when we change the ontology, we modify references to always the same class,
    # not a copy of it
    classes = dict(_classes)
    classvars = [ (cls, cls.class_variables()) for cls in _classes.values() ]
    _saved_ontologies[name] = (classes, classvars)

def reload_saved_ontology(name):
    global _classes

    try:
        classes, classvars = _saved_ontologies[name]
    except KeyError:
        raise KeyError("Could not find '%s' ontology" % name)

    _classes = dict(classes)
    for cls, cvars in classvars:
        cls.set_class_variables(cvars)

    revalidate_graphs()

def clear():
    reload_saved_ontology('origin')
    # FIXME: this still leaks memory, as the nodes in a graph have a ref to it
    #_graphs = weakref.WeakValueDictionary()


def subclasses(cls):
    '''Returns the given class and all of its subclasses'''
    return (c for c in _classes.values() if issubclass(c, cls))

def parent_classes(cls):
    '''Returns the given class and all of its parent classes (BaseObject being the topmost class).'''
    return (c for c in _classes.values() if issubclass(cls, c))

def validate_class_definition(cls, attrs):
    BaseObject = _classes['BaseObject']

    valid_types = validLiteralTypes + [ BaseObject ]

    if not issubclass(cls, BaseObject):
        raise TypeError, "'%s' needs to derive from ontology.BaseObject or one of its subclasses" % cls.__name__

    parent = cls.parent_class()

    def check_present(cls, var, ctype, default_value = True):
        if not isinstance(ctype, tuple):
            ctype = (ctype,)

        try:
            value = getattr(cls, var)
        except AttributeError:
            raise TypeError("Your subclass '%s' should define the '%s' class variable as a %s" % (cls.__name__, var, ' or a '.join(c.__name__ for c in ctype)))

        #if not explicitAttribute(cls, var):
        if var not in attrs:
            if default_value:
                # if not explicitly in subclass definition, create a default one
                setattr(cls, var, ctype[0]())
            else:
                raise TypeError("Your subclass '%s' should define explicitly the '%s' class variable as a %s" % (cls.__name__, var, ' or a '.join(c.__name__ for c in ctype)))

        if type(value) not in ctype:
            raise TypeError("Your subclass '%s' defines the '%s' class variable as a '%s', but it should be of type %s" % (cls.__name__, var, type(value).__name__, ' or '.join(c.__name__ for c in ctype)))

        # convert to our preferred type (first of the possible types)
        setattr(cls, var, ctype[0](value))


    def check_schema_subset(cls, var, default_value = True):
        check_present(cls, var, (set, list), default_value)
        for prop in getattr(cls, var):
            if not prop in cls.schema:
                raise TypeError("In '%s': when defining '%s', you used the '%s' variable, which is not defined in the schema" % (cls.__name__, var, prop))

    def check_parent_superset(cls, var):
        if not set(getattr(cls, var)).issuperset(set(getattr(cls.parent_class(), var))):
            raise TypeError("In '%s': the '%s' variable needs to be a superset of its class parent's one" % (cls.__name__, var))


    # validate that the schema is correctly defined
    check_present(cls, 'schema', dict, default_value =  False)

    # inherit schema from parent class
    schema = Schema(parent.schema) # make a copy of parent's schema
    schema.update(cls.schema) # make sure we don't overwrite (or do we want to allow overloading of variables?)
    schema._implicit = set(parent.schema._implicit) # no need to get cls.schema._implicit as well, it's empty
    cls.schema = schema

    # validate attribute types as defined in schema
    for name, ctype in cls.schema.items():
        if not isinstance(name, str) or not any(issubclass(ctype, dtype) for dtype in valid_types):
            raise TypeError("In '%s': the schema should be a dict of 'str' to either one of those accepted types (or a subclass of them): %s'" % (cls.__name__, ', '.join("'%s'" % c.__name__ for c in validTypes)))


    # all the properties defined as subclasses of BaseObject need to have an
    # associated reverseLookup entry
    check_present(cls, 'reverse_lookup', dict)
    orig_reverse_lookup = cls.reverse_lookup if 'reverse_lookup' in attrs else {}

    # inherit reverseLookup from parent
    rlookup = dict(parent.reverse_lookup)
    rlookup.update(cls.reverse_lookup)
    cls.reverse_lookup = rlookup

    # check that we have reverseLookup names for all needed properties
    object_props = [ name for name, ctype in cls.schema.items() if issubclass(ctype, BaseObject) and name not in cls.schema._implicit ]
    reverse_lookup = [ prop for prop in cls.reverse_lookup.keys() if prop not in cls.schema._implicit ]

    diff = set(reverse_lookup).symmetric_difference(set(object_props))
    if diff:
        raise TypeError("In '%s': you should define exactly one reverseLookup name for each property in your schema that is a subclass of BaseObject, different ones: %s" % (cls.__name__, ', '.join("'%s'" % c for c in diff)))

    # directly update the schema for other classes where needed
    # TODO: make sure we don't overwrite anything (should have been done in the validateClassDefinition, right?)
    for prop, rprop in orig_reverse_lookup.items():
        for c in subclasses(cls.schema[prop]):
            c.schema._implicit.add(rprop)
            c.schema[rprop] = cls
            c.reverse_lookup[rprop] = prop


    # check that the other variables are correctly defined
    check_schema_subset(cls, 'valid', default_value = False)
    check_parent_superset(cls, 'valid')

    check_schema_subset(cls, 'unique')
    check_parent_superset(cls, 'unique')

    check_schema_subset(cls, 'order')
    # TODO: validate converters


def print_class(cls):
    print '*'*100
    print 'class: %s' % cls.__name__
    print 'parent: %s' % cls.parent_class().__name__
    print 'schema', cls.schema
    print 'implicit', cls.schema._implicit
    print 'rlookup', cls.reverse_lookup
    print '*'*100


def display_ontology():
    import cPickle as pickle
    import tempfile
    import subprocess

    fid, filename = tempfile.mkstemp(suffix = '.png')

    dg = []
    dg += [ 'digraph G {' ]

    #for _id, n in nodes.items():
    for cname, cls in _classes.items():
        label = '<FONT COLOR="#884444">%s</FONT><BR/>' % cname
        attrs = []
        for name, type in cls.schema.items():
            if name in cls.schema._implicit: continue
            attrs += [ '%s: %s' % (name, type.__name__) ]
        for name in cls.schema._implicit:
            attrs += [ '<FONT COLOR="#666666">%s: %s</FONT>' % (name, cls.schema[name].__name__) ]

        label += '<BR/>'.join(attrs)
        dg += [ 'node_%s [shape=polygon,sides=4,label=<%s>];' % (cname, label) ]

        dg += [ 'node_%s -> node_%s;' % (cname, cls.parent_class().__name__) ]


    dg += [ '}' ]

    subprocess.Popen([ 'dot', '-Tpng', '-o', filename ], stdin = subprocess.PIPE).communicate('\n'.join(dg))

    subprocess.Popen([ 'gwenview', filename ], stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate()

def register(cls, attrs):
    # when registering BaseObject, skip the tests
    if cls.__name__ == 'BaseObject':
        _classes['BaseObject'] = cls
        # save this as a default ontology, it might be useful
        save_current_ontology('origin')
        return

    if cls.__name__ in _classes:
        if cls == _classes[cls.__name__]:
            log.info('Class %s already registered' % cls.__name__)
            return

        log.warning('Found previous definition of class %s. Ignoring new definition...' % cls.__name__)
        return

    validate_class_definition(cls, attrs)

    _classes[cls.__name__] = cls

    revalidate_graphs()

    #displayOntology()


def register_graph(graph):
    _graphs[id(graph)] = graph

def get_class(class_name):
    """Returns the ObjectNode class object given its name."""
    try:
        return _classes[class_name]
    except:
        raise ValueError, 'Class "%s" has not been registered with the OntologyManager' % class_name

def class_names():
    return _classes.keys()

def import_class(cls):
    sys._getframe(1).f_globals[cls] = get_class(cls)

def import_classes(classes):
    """Import the given classes in the caller's global variables namespace."""
    for cls in classes:
        sys._getframe(1).f_globals[cls] = get_class(cls)

def import_all_classes():
    import_classes(class_names())

def import_ontology(name):
    reload_saved_ontology(name)
    import_all_classes()
