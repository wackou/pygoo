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

from __future__ import unicode_literals
from pygoo.abstractnode import AbstractNode
from pygoo.abstractdirectedgraph import Equal
from pygoo.baseobject import BaseObject
from pygoo.utils import is_of, multi_is_instance, is_literal
from pygoo import ontology
import types
import weakref
import collections
import logging

log = logging.getLogger(__name__)



class ObjectNode(AbstractNode):
    """An ObjectNode is a nice and useful mix between an OOP object and a node in a graph.

    An ObjectNode behaves in the following way:
     - it can have any number of named properties, of any type (literal type or another ObjectNode)
         If the property is a literal type, it is stored inside the node
         If the property is another node(s), it means there are directed edges of the same name from this node to the other one(s)
     - it implements dotted attribute access.
     - it keeps a list of valid classes for this node. If a node has a certain class, we can then create a valid instance of
       that class (subclass of BaseObject) with the data from this node. The list of valid classes is actualized each time you
       set a property.

    ObjectNodes should implement different types of equalities:
      - identity: both refs point to the same node in the ObjectGraph
      - all their properties are equal (same type and values)
      - DEPRECATED(*) all their standard properties are equal
      - DEPRECATED(*) only their primary properties are equal

    (*) this should now be done in BaseObject instances instead of directly on the ObjectNode.

    ---------------------------------------------------------------------------------------------------------

    To be precise, ObjectNodes use a type system based on relaxed type classes
    (http://en.wikipedia.org/wiki/Type_classes)
    where there is a standard object hierarchy, but an ObjectNode can be of various distinct
    classes at the same time.

    As this doesn't fit exactly with python's way of doing things, class value should be tested
    using the ObjectNode.isinstance(class) method instead of the usual isinstance(obj, class) function.

    ---------------------------------------------------------------------------------------------------------

    Not yet implemented / TODO:

    Accessing properties should return a "smart" iterator when accessing properties which are instances of
    AbstractNode, which also allows to call dotted attribute access on it, so that this becomes possible:

    for f in Series.episodes.file.filename:
        do_sth()

    where Series.episodes returns multiple results, but Episode.file might also return multiple results.
    File.filename returns a literal property, which means that we can now convert our iterator over BaseObject
    into a list (or single element) of literal
    """

    def __init__(self, graph, props = []):
        super(ObjectNode, self).__init__(graph, props)
        log.debug('ObjectNode.__init__: props = %s' % str(props))

        self.graph = weakref.ref(graph)

        for prop, value, reverse_name in props:
            self.set(prop, value, reverse_name, validate=False)

        self.update_valid_classes()


    def is_valid_instance(self, cls):
        """Returns whether this node can be considered a valid instance of a class given its current properties.

        This method doesn't use the cached value, but does the actual checking of whether there is a match."""
        return self.has_valid_properties(cls, cls.valid)

    def has_valid_properties(self, cls, props):
        for prop in props:
            value = self.get(prop)
            prop_cls = cls.schema[prop]
            if isinstance(prop_cls, (list, set)):
                prop_cls = next(iter(prop_cls))

            if isinstance(value, collections.Iterator):
                value = list(value)
                # TODO: we might need value.isValidInstance in some cases
                if value != [] and not value[0].isinstance(prop_cls):
                    return False
            else:
                # TODO: here we might want to check if value is None and allow it or not
                if type(value) != prop_cls:
                    return False

        return True


    def invalid_properties(self, cls):
        invalid = []
        for prop in cls.valid:
            if prop not in self:
                invalid.append("property '%s' is missing" % prop)
                continue

            # FIXME: link type checking doesn't work
            if isinstance(getattr(self, prop), collections.Iterator):
                continue

            if not multi_is_instance(getattr(self, prop), cls.schema[prop]):
                invalid.append("property '%s' is of type '%s', but should be of type '%s'" %
                               (prop, type(getattr(self, prop)).__name__, cls.schema[prop].__name__))

        return '\n'.join(invalid)


    def update_valid_classes(self):
        """Revalidate all the classes for this node."""
        if self.graph()._dynamic:
            self.clear_classes()
            for cls in ontology._classes.values():
                if self.is_valid_instance(cls):
                    self.add_class(cls)
        else:
            # if we have static inheritance, we don't want to do anything here
            pass

        log.debug('valid classes for %s:\n  %s' % (self.to_string(), [ cls.__name__ for cls in self._classes ]))

    def virtual_class(self):
        """Return the most specialized class that this node is an instance of."""
        cls = BaseObject
        for c in self.classes():
            if issubclass(c, cls):
                cls = c
        return cls

    def virtual(self):
        """Return an instance of the most specialized class that this node is an instance of."""
        return self.virtual_class()(self)

    ### Container methods

    def keys(self):
        for k in self.literal_keys():
            yield k
        for k in self.edge_keys():
            yield k

    def values(self):
        for v in self.literal_values():
            yield v
        for v in self.edge_values():
            yield v

    def items(self):
        for i in self.literal_items():
            yield i
        for i in self.edge_items():
            yield i

    def __contains__(self, name):
        return name in self.keys()

    def __iter__(self):
        for prop in self.keys():
            yield prop

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        # TODO: why do we need this again?
        raise NotImplementedError

    # TODO: implement __len__ for container?


    ### Acessing properties methods

    def __getattr__(self, name):
        try:
            return self.get_literal(name)
        except:
            try:
                return self.outgoing_edge_endpoints(name) # this should be an iterable over the pointed nodes
            except:
                raise AttributeError(name)

    def get(self, name, default=None):
        """Returns the given property or None if not found.
        This can return either a literal value, or an iterator through other nodes if
        the given property actually was a link relation."""
        try:
            return self.__getattr__(name)
        except AttributeError:
            return default

    def follow(self, prop_list):
        """Given a list of successive chained properties, returns an iterator
        to the nodes that could be reached by following those properties.

        e.g.: Movie('2001').follow([ 'director', 'firstName' ]) == ['Stanley']

        In case some property does not exist, it will raise an AttributeError.
        """
        result = self
        for prop in prop_list:
            result = result.get(prop)
            if isinstance(result, collections.Iterator):
                # FIXME: implement me
                pass

        return result

    def get_chained_properties(self, prop_list):
        """Given a list of successive chained properties, returns the final value.
        e.g.: Movie('2001').get_chained_properties([ 'director', 'firstName' ]) == 'Stanley'

        In case some property does not exist, it will raise an AttributeError.
        """
        # FIXME: replace with follow()
        result = self
        for prop in prop_list:
            result = result.get(prop)
            if isinstance(result, collections.Iterator):
                # FIXME: this will fail if it branches before the last property
                #result = toresult(list(result))
                pass

        return result

    ### properties manipulation methods

    def __setattr__(self, name, value):
        if name in [ 'graph' ]:
            object.__setattr__(self, name, value)
        else:
            self.set(name, value)

    def set(self, name, value, reverse_name = None, validate = True):
        """Sets the property name to the given value.

        If value is an ObjectNode, we're actually setting a link between them two, so we use reverseName as the
        name of the link when followed in the other direction.
        If reverseName is not given, a default of 'isNameOf' (using the given name) will be used."""

        if multi_is_instance(value, AbstractNode):
            if reverse_name is None:
                reverse_name = is_of(name)

            self.set_link(name, value, reverse_name)

        elif is_literal(value):
            self.set_literal(name, value)

        else:
            raise TypeError("Trying to set property '%s' of %s to '%s', but it is not of a supported type (literal or object node): %s" % (name, self, value, type(value).__name__))

        # update the cache of valid classes
        if validate:
            self.update_valid_classes()



    def append(self, name, value, reverse_name = None, validate = True):
        if multi_is_instance(value, AbstractNode):
            if reverse_name is None:
                reverse_name = is_of(name)

            self.add_link(name, value, reverse_name)

        else:
            raise TypeError("Trying to append to property '%s' of %s: '%s', but it is not of a supported type (literal or object node): %s" % (name, self, value, type(value).__name__))

        # update the cache of valid classes
        if validate:
            self.update_valid_classes()


    def add_link(self, name, other_node, reverse_name):
        g = self.graph()

        if isinstance(other_node, list) or isinstance(other_node, collections.Iterator):
            for n in other_node:
                g.add_link(self, name, n, reverse_name)
        else:
            g.add_link(self, name, other_node, reverse_name)


    def set_link(self, name, other_node, reverse_name):
        """Can assume that otherNode is always an object node or an iterable over them."""
        # need to check for whether otherNode is an iterable
        #if self._graph != otherNode._graph:
        #    raise ValueError('Both nodes do not live in the same graph, cannot link them together')

        g = self.graph()

        # first remove the old link(s)
        # FIXME: we need to wrap the generator into a list here because it looks like otherwise
        # the removeLink() call messes up with it
        for n in list(self.get(name, [])):
            g.remove_link(self, name, n, reverse_name)

        # then add the new link(s)
        self.add_link(name, other_node, reverse_name)



    def update(self, props):
        """Update this ObjectNode properties with the ones contained in the given dict.
        Should also allow instances of other ObjectNodes."""
        for name, value in props.items():
            self.set(name, value, validate = False)

        self.update_valid_classes()

    def update_new(self, other):
        """Update this ObjectNode properties with the only other ones it doesn't have yet."""
        raise NotImplementedError

    def same_properties(self, other, props = None, exclude = [], cmp = None):
        # NB: sameValidProperties and sameUniqueProperties should be defined in BaseObject
        # TODO: this can surely be optimized
        if props is None:
            props = other.items()
        else:
            props = [ (p, other.get(p)) for p in props ]

        for name, value in props:
            if name in exclude:
                continue
            #print '     prop:', name,
            if isinstance(value, collections.Iterator):
                svalue = list(self.get(name))
                value = list(value)
                #print 'gen; value=', svalue, value

                if cmp == Equal.OnUnique:
                    # FIXME: this is an ugly workaround, but I need to get pygoo back on track
                    #        and this has to work *right now*
                    def same_props_obj(obj1, obj2):
                        props = obj1.unique_properties()
                        return obj1.node.same_properties(obj2.node, props, cmp = Equal.OnUnique)

                    result = (len(svalue) == len(value) and
                              all(same_props_obj(v1.virtual(), v2.virtual()) for v1, v2 in zip(svalue, value)))
                else:
                    # FIXME: v1.virtual() should not be used here...
                    result = (len(svalue) == len(value) and
                              all(v1.virtual() == v2.virtual() for v1, v2 in zip(svalue, value)))

                if result is False:
                    return False
            else:
                #print 'normal; value=', self.get(name), value
                if self.get(name) != value:
                    return False

        return True


    ### String methods

    def __str__(self):
        return self.to_string().encode('utf-8')

    def __unicode__(self):
        return self.to_string()

    def __repr__(self):
        return str(self)


    def to_string(self, cls = None, default = None, recurseLimit = 2, fancyIndent = False):
        # TODO: smarter stringize that guesses the class, should it always be there?
        cls = self.virtual_class()

        if cls is None:
            log.error('FIXME: remove me')
            # most likely called from a node, but anyway we can't infer anything on the links so just display
            # them as anonymous ObjectNodes
            cls = self.__class__
            props = [ (prop, [ cls.__name__ ] * len(tolist(value))) if multi_is_instance(value, ObjectNode) else (prop, unicode(value)) for prop, value in self.items() ]

        else:
            props = []
            for prop, value in self.items():
                # only print explicitly defined properties
                if prop not in cls.schema:
                    continue
                elif isinstance(value, collections.Iterator):
                    if recurseLimit:
                        # TODO: if prop is ONE_TO_ONE, do not do a join
                        props.append((prop, '['+', '.join([v.to_string(cls=cls.schema.get(prop) or default,
                                                                       recurseLimit=recurseLimit-1,
                                                                       fancyIndent=fancyIndent) for v in value ])+']'))
                    else:
                        props.append((prop, '[...]'))
                else:
                    props.append((prop, unicode(value)))

        # could be toJson() instead of simply fancyIndent
        if fancyIndent:
            result = '%s {\n' % cls.__name__
            for k, v in props:
                indented = '\n    '.join(v.split('\n'))
                result += '    %s: %s\n' % (k, indented)
            return result + '}'
        else:
            return '%s(%s)' % (cls.__name__, ', '.join([ '%s=%s' % (k, v) for k, v in props ]))
