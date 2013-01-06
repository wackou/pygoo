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
from pygoo.utils import is_of, reverse_name, reverse_lookup, check_class
from pygoo import ontology
import collections
import logging

log = logging.getLogger(__name__)


def get_node(node):
    if isinstance(node, AbstractNode):
        return node
    elif isinstance(node, BaseObject):
        return node.node
    elif isinstance(node, list) and isinstance(node[0], BaseObject):
        return [ n.node for n in node ]
    else:
        raise TypeError("Given object is not an ObjectNode or BaseObject instance")

def to_nodes(d):
    result = dict(d)
    for k, v in d.items():
        if isinstance(v, BaseObject):
            result[k] = v.node
        elif isinstance(v, list) and (v != [] and isinstance(v[0], BaseObject)):
            result[k] = [ n.node for n in v ]
    return result


# Metaclass to be used for BaseObject so that they are automatically registered in the ontology
class OntologyClass(type):
    def __new__(cls, name, bases, attrs):
        log.debug('Creating ontology class: %s' % name)
        if len(bases) > 1:
            raise TypeError('BaseObject does not allow multiple inheritance for class: %s' % name)
        return type.__new__(cls, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        log.debug('Initializing ontology class: %s' % name)
        super(OntologyClass, cls).__init__(name, bases, attrs)
        ontology.register(cls, attrs)


    def class_variables(cls):
        # need to return a copy here (we're already messing enough with all those mutable objects around...)
        return (ontology.Schema(cls.schema),
                dict(cls.reverse_lookup),
                set(cls.valid),
                set(cls.unique),
                list(cls.display_order),
                dict(cls.converters))

    def set_class_variables(cls, vars):
        cls.schema = ontology.Schema(vars[0])
        cls.reverse_lookup = dict(vars[1])
        cls.valid = set(vars[2])
        cls.unique = set(vars[3])
        cls.display_order = list(vars[4])
        cls.converters = dict(vars[5])


class BaseObject(object):
    """A BaseObject is a statically-typed object which gets its data from an ObjectNode. In that sense, it
    acts like a view of an ObjectNode, and all data assigned to a BaseObject is actually stored in the
    ObjectNode.

    It is possible and inexpensive to create any number of possibly different BaseObject "views" on an
    ObjectNode, which means that you can dynamically interpret an ObjectNode as being an instance of a
    given class (given that it matches the class schema).

    Equality comparison is done by comparing the properties of the nodes, not the identity of the nodes,
    so two BaseObjects wrapping two different nodes in the graph would be equal if their properties are.

    You should derive from this class to define an ontology domain on ObjectGraphs and ObjectNodes.

    You should define the following class variables in derived classes:

    1- 'schema' which is a dict of property names to their respective types
        ex: schema = { 'epNumber': int,
                       'title': unicode
                       }

    2- 'reverse_lookup' which is a dict used to indicate the name to be used for the property name
                        when following a relationship between objects in the other direction.
                        ie: if Episode(...).series == Series('Scrubs'), then we define automatically
                        a way to access the Episode() from the pointed to Series() object.
                        with { 'series': 'episodes' }, we then have:
                        Series('Scrubs').episodes = [ Episode(...), Episode(...) ]
                        reverse_lookup must be defined for each property which is a Node object

    # FIXME: there should be a test for the default value
    3- 'valid' (optional) list of properties a node needs to have to be able to be considered
               as a valid instance of this class
               if valid is either the empty list or unspecified, all instances are considered valid
               by default, this is the same as the keys from the 'schema' dict

    # FIXME: there should be a test for the default value
    4- 'unique' (optional) list of properties that form a primary key
                by default, this is the same as the 'valid' property

    # FIXME: there should be a test for the default value
    5- 'display_order' (optional) order in which the properties should be displayed
                       by default, this will be set to the 'valid' variable

    # FIXME: need to be tested too
    6- 'converters' (optional), which is a dictionary from property name to a pair of functions
                    that are able to serialize/deserialize this property to/from a unicode string.


    Apart from having to define the aforementioned class variables, a BaseObject behaves like a python object,
    so that a subclass of BaseObject can also define its own methods and they can be called normally on instances
    of it.
    As an example, you might want to define:

    class Actor:
        def bestMovies(self):
            maxRating = max(movie.rating for movie in self.roles.movie)
            return [ movie for movie in self.roles.movie if movie.rating == maxRating ]


    Note: at the moment, self.roles.movie wouldn't work, so one would have to do so:
    class Actor:
        def bestMovies(self):
            maxRating = max(role.movie.rating for role in self.roles)
            return [ role.movie for role in self.roles if role.movie.rating == maxRating ]

    Which is slightly less intuitive because it forces us to iterate over the roles instead of over the movies.
    """

    __metaclass__ = OntologyClass

    # TODO: remove those variables which definition should be mandatory
    schema = ontology.Schema({})
    reverse_lookup = {}
    valid = []
    unique = []
    display_order = []
    converters = {}

    # This variable works just like the 'schema' one, except that it only contains properties which have been defined
    # as a result of the reverseLookup names of other classes
    #_implicitSchema = {}

    def __init__(self, basenode = None, graph = None, allow_incomplete = False, **kwargs):
        #log.debug('%s.__init__: basenode = %s, args = %s' % (self.__class__.__name__, basenode, kwargs))
        if graph is None and basenode is None:
            raise ValueError('You need to specify either a graph or a base node when instantiating a %s' % self.__class__.__name__)

        # just to make sure, while developing. This should probably be removed in a stable version
        if (#(graph is not None and not isinstance(graph, ObjectGraph)) or
            (basenode is not None and not (isinstance(basenode, AbstractNode) or
                                           isinstance(basenode, BaseObject)))):
                raise ValueError('Trying to build a BaseObject from a basenode, but you gave a \'%s\': %s' % (type(basenode).__name__, str(basenode)))

        created = False
        if basenode is None:
            # if no basenode is given, we need to create a new node
            self.node = graph.create_node(reverse_lookup(kwargs, self.__class__),
                                          _classes = ontology.parent_classes(self.__class__))
            created = True

        else:
            basenode = get_node(basenode)

            # if basenode is already in this graph, no need to make a copy of it
            # if graph is None, we might just be making a new instance of a node, so it's in the same graph as well
            if graph is None or graph is basenode.graph():
                self.node = basenode
            else:
                if basenode.edge_keys():
                    # we have links, we can't just create the node without adding the dependencies...
                    raise Exception("sorry, can't do that right now...")

                # TODO: we should be able to construct directly from the other node
                self.node = graph.create_node(reverse_lookup(basenode, self.__class__),
                                              _classes = basenode._classes)
                created = True


            # optimization: avoid revalidating the classes all the time when creating a BaseObject from a pre-existing node
            if kwargs:
                self.update(kwargs)

        # if we just created a node and the graph is static, we gave it its valid classes without actually checking...
        # if not a valid instance, remove it from the list of valid classes so that the next check will fail
        if created and not self.node.graph()._dynamic:
            if allow_incomplete and not self.node.has_valid_properties(self.__class__, set(self.__class__.valid).intersection(set(self.node.keys()))):
                # FIXME: change to log.debug
                log.warning('removing1 class %s', self.__class__)
                self.node.remove_class(self.__class__)
            # FIXME: remove the is_valid_check(), no? nodes should always be instantiated
            #        from their class
            if not allow_incomplete and not self.node.is_valid_instance(self.__class__):
                log.warning('removing2 class %s', self.__class__)
                self.node.remove_class(self.__class__)


        # make sure that the new instance we're creating is actually a valid one
        # Note: the following comment shouldn't be necessary if the list of valid classes is always up-to-date
        #if not (self.node.isinstance(self.__class__) or
        #        (self.node._graph._dynamic and self.node.isValidInstance(self.__class__))):
        if not self.node.isinstance(self.__class__):
            # create the error message before we delete the node, as we might remove some information
            # by unlinking other nodes (eg: for an episode node, the delete_node will remove the link
            # to the series if it had one)
            msg = self.node.invalid_properties(self.__class__)

            # if we just created the node and it is invalid, we need to remove it
            if created:
                self.node.graph().delete_node(self.node)

            raise TypeError("Cannot instantiate a valid instance of %s because:\n%s" %
                            (self.__class__.__name__, msg))



    def __contains__(self, prop):
        return prop in self.node

    def get(self, name, default=None):
        try:
            return getattr(self, name)
        except AttributeError:
            return default


    #### a BaseObject has custom attribute access ####

    def __getattr__(self, name):
        result = getattr(self.node, name)

        # if the result is an ObjectNode, wrap it with the class it has been given in the class schema
        # if it was not in the class schema, simply returns an instance of BaseObject
        if isinstance(result, collections.Iterator):
            # FIXME: should rather use ResultClass.make_virtual() or sth similar to
            # promote automatically the node to the class it has instead of getting
            # the class from the schema
            ResultClass = self.__class__.schema.prop_cls(name) or BaseObject
            def result_iterator():
                for node in result:
                    yield ResultClass(basenode=node)

            rel = self.__class__.schema._relations.get(name)
            if rel is not None:
                if (rel == ontology.ONE_TO_ONE or
                    rel == ontology.ORDERED_MANY_TO_ONE or
                    rel == ontology.UNORDERED_MANY_TO_ONE):
                    return next(result_iterator())
                else:
                    return result_iterator()

            return next(result_iterator())

        # FIXME: better test here (although if the graph is consistent (ie: always returns generators) it shouldn't be necessary)
        #elif isinstance(result, list) and isinstance(result[0], AbstractNode):
        #    resultClass = self.__class__.schema.get(name) or BaseObject
        #    return [ resultClass(basenode = node) for node in result ]

        else:
            # FIXME: remove me later
            assert(not isinstance(result, (list, set)))
            return result

    def __setattr__(self, name, value):
        if name == 'node':
            object.__setattr__(self, name, value)
        else:
            self.set(name, value)

    def __delattr__(self, name):
        if name in self.node.literal_keys():
            del self.node._props[name] # FIXME: this is only valid for MemoryObjectNodes (no Neo4jNode)...

        # FIXME: implement me completely (ie: for links too)
        pass



    #### A BaseObject also can work using a container API
    ## NB: the rest of the methods (__iter__, __contains__, ...) are inherited from ObjectNode
    def __getitem__(self, name):
        return self.__getattr__(name)

    def __setitem__(self, name, value):
        return self.__setattr__(name, value)

    def __delitem__(self, name):
        return self.__delattr__(name)


    def _apply_multi(self, func, name, value, validate):
        cls = self.__class__
        if name in cls.schema._implicit:
            raise ValueError("Implicit properties are read-only (%s.%s)" % (cls.__name__, name))

        # if mode == STRICT and name not in cls.schema:
        #     raise ValueError("Unknown property in the class schema: (%s.%s)" % (cls.__name__, name))

        # objects are statically-typed here; graphType == 'STATIC'
        # this also converts value to the correct type if an autoconverter was given in the class definition
        # and replaces BaseObjects with their underlying nodes.
        value = check_class(name, value, cls.schema)

        func(name, value, reverse_name(self.__class__, name), validate)

    def set(self, name, value, validate = True):
        """Sets the given value to the named property."""
        self._apply_multi(self.node.set, name, value, validate)

    def append(self, name, value, validate = True):
        self._apply_multi(self.node.append, name, value, validate)

    def __eq__(self, other):
        # TODO: should allow comparing a BaseObject with an ObjectNode?
        if not isinstance(other, BaseObject):
            return False

        if self.node == other.node:
            return True

        # FIXME: this could lead to cycles or very long chained __eq__ calling on properties
        return list(self.explicit_items()) == list(other.explicit_items())

    def __hash__(self):
        return hash(self.node)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.node.to_string(cls=self.__class__, default=BaseObject).encode('utf-8')

    def __repr__(self):
        return self.__str__()

    def display_string(self):
        return str(self)

    def schema_keys(self):
        return self.__class__.schema.keys()

    def schema_items(self):
        return (x for x in self.items() if x[0] in self.__class__.schema)

    def explicit_schema_keys(self):
        return (x for x in self.schema_keys() if x not in self.__class__.schema._implicit)

    def explicit_schema_items(self):
        return (x for x in self.schema_items() if x[0] not in self.__class__.schema._implicit)

    def explicit_keys(self):
        return (x for x in self.keys() if x not in self.__class__.schema._implicit)

    def explicit_items(self):
        return (x for x in self.items() if x[0] not in self.__class__.schema._implicit)

    @classmethod
    def class_name(cls):
        return cls.__name__

    @classmethod
    def parent_class(cls):
        return cls.__mro__[1]

    def virtual(self):
        """Return an instance of the most specialized class that this node is an instance of."""
        return self.node.virtual()

    def update(self, props):
        props = to_nodes(props)
        for name, value in props.items():
            self.set(name, value, validate = False)
        self.node.update_valid_classes()

    def is_unique(self):
        """Return whether all unique properties (as defined by the class) of the ObjectNode
        are non-null."""
        for prop in self.__class__.unique:
            if prop not in self.node:
                return False
        return True

    def unique_properties(self):
        return self.__class__.unique

    def unique_key(self):
        """Return a tuple containing an unique identifier (inside its class) for this instance.
        If some unique fields are not specified, None will be put instead."""
        return tuple(self.get(k) for k in self.__class__.unique)


    def ordered_properties(self):
        """Returns the list of properties ordered using the defined order in the subclass.

        NB: this should be replaced by using an OrderedDict."""
        result = []
        property_names = list(self.node.keys())

        for p in self.__class__.display_order:
            if p in property_names:
                result.append(p)
                property_names.remove(p)

        return result + property_names
