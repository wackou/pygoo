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

from pygoo.abstractdirectedgraph import AbstractDirectedGraph, Equal
from pygoo.baseobject import BaseObject, get_node
from pygoo.utils import reverse_lookup
from pygoo import ontology
import types
import logging

log = logging.getLogger(__name__)



def wrap_node(node, node_class = None):
    if node_class is None:
        node_class = BaseObject
    return node_class(basenode = node)

def unwrap_node(node):
    node_class = node.__class__ if isinstance(node, BaseObject) else None
    node = get_node(node)

    return node, node_class



class ObjectGraph(AbstractDirectedGraph):
    """An ObjectGraph is an undirected graph of ObjectNodes.
    An ObjectNode "looks like" an object, with a class type and any number of properties/attributes,
    which can be either literal values or other objects in the graph. These properties are accessed
    using dotted attribute notation.

    The ObjectGraph edges (links) are a bit special in that they are undirected but have a different
    name depending on the direction in which they are followed, e.g.: if you have two nodes, one
    which represent a series, and another one which represent an episode, the link will be named
    "series" when going from the episode to the series, but will be named "episodes" when going from
    the series to the episode.

    When setting a link in the graph, you should define a name for the reverse name of the link, but if
    you don't a default name of "is(%Property)Of" will be given to it.
    For instance, if we have movie.director == personX, we should also have
    personX.isDirectorOf == movie (actually "movie in personX.isDirectorOf").

    The ObjectGraph class provides ways of querying objects in it using type information,
    properties matching filters, or just plain lambda functions that returns whether a node
    is acceptable or not.

    An ObjectGraph can be thought of as a context in which objects live.

    Even though the dotted attribute access makes this less visible, the links between ObjectNodes
    are first-class citizens also, and can themselves have attributes, such as confidence, etc...
    """

    # this should be set to the used ObjectNode class (ie: MemoryObjectNode or Neo4jObjectNode)
    # in the corresponding derived ObjectGraph class
    _object_node_class = type(None)

    def __init__(self, dynamic = False):
        """Creates an ObjectGraph.

        - if dynamic = True, we have static inheritance (valid classes need to be set explicitly)
        - if dynamic = False, we have dynamic type classes (valid classes are automatically updated if the object has the correct properties)
        """
        ontology.register_graph(self)
        self._dynamic = dynamic

    def revalidate_objects(self):
        if not self._dynamic:
            return

        log.info('revalidating objects in graph %s' % self)
        for node in self.nodes():
            node.update_valid_classes()

    def __getattr__(self, name):
        # if attr is not found and starts with an upper case letter, it might be the name
        # of one of the registered classes. In that case, return a function that would instantiate
        # such an object in this graph
        if name[0].isupper() and name in ontology.class_names():
            def inst(basenode = None, **kwargs):
                # if we're copying a node from a different graph, we need to intercept it here to
                # add it correctly with its dependencies instead of creating from scratch
                if basenode is not None and basenode.node.graph() != self:
                    return self.add_object(basenode)

                return ontology.get_class(name)(basenode = basenode, graph = self, **kwargs)

            return inst

        raise AttributeError, name

    def __contains__(self, node):
        """Return whether this graph contains the given node  or object (identity)."""
        return self.contains(get_node(node))


    def add_link(self, node, name, other_node, reverse_name):
        # otherNode should always be a valid instance of a node

        # here we want to check first if we're adding a node that's in the same graph or not
        if node.graph is not other_node.graph:
            raise ValueError('Trying to set attribute "%s" for %s to %s, but they\'re not in the same graph' % (name, node, other_node))

        self.add_directed_edge(node, name, other_node)
        self.add_directed_edge(other_node, reverse_name, node)

    def remove_link(self, node, name, other_node, reverse_name):
        # other_node should always be a valid node
        self.remove_directed_edge(node, name, other_node)
        self.remove_directed_edge(other_node, reverse_name, node)


    def add_node(self, node, recurse = Equal.OnIdentity, excluded_deps = list()):
        return self.add_object(BaseObject(node), recurse, excluded_deps)


    def add_object(self, node, recurse = Equal.OnIdentity, excluded_deps = list()):
        """Add an object and its underlying node and its links recursively into the graph.

        If some dependencies of the node are already in the graph, we should not add
        new instances of them but use the ones already there (ie: merge links).

        This strategy should be configurable, and offer at least the following choices:
          - recurse = OnIdentity   : do not add the dependency only if the exact same node is already there
          - recurse = OnValue      : do not add the dependency only if there is already a node with the exact same properties
          - recurse = OnValidValue : do not add the dependency only if there is already a node with the same valid properties
          - recurse = OnUnique     : do not add the dependency only if there is already a node with the same unique properties
        """
        # FIXME: not necessarily correct, but safer for now to avoid infinite recursion
        #        ie, if we add a node without a class, we won't know its implicit dependencies
        node = node.node.virtual()
        log.debug('Adding to graph: %s - node: %s' % (self, node))
        node, node_class = unwrap_node(node)

        if node_class is None:
            raise TypeError("Can only add BaseObjects to a graph at the moment...")

        # first make sure the node's not already in the graph, using the requested equality comparison
        # TODO: if node is already there, we need to decide what to do with the additional information we have
        #       in the added node dependencies: update missing properties, update all properties (even if already present),
        #       update non-valid properties, ignore new data, etc...
        excluded_properties = node_class.schema._implicit if node_class is not None else []
        log.debug('exclude properties: %s' % excluded_properties)

        gnode = self.find_node(node, recurse, excluded_properties)
        if gnode is not None:
            log.debug('Found already existing node %s' % gnode)
            return wrap_node(gnode, node_class)

        # if node isn't already in graph, we need to make a copy of it that lives in this graph
        log.debug('Creating a new node in this graph')

        # first import any other node this node might depend on
        newprops = []
        for prop, value, reverse_name in reverse_lookup(node, node_class):
            #if (isinstance(value, AbstractNode) or
            #    (isinstance(value, list) and isinstance(value[0], AbstractNode))):
            if isinstance(value, types.GeneratorType):
                # use only the explicit properties here
                if prop not in excluded_properties and value not in excluded_deps:
                    imported_nodes = []
                    for v in value:
                        log.debug('Importing dependency %s: %s' % (prop, v))
                        imported_nodes.append(self.add_object(wrap_node(v, node_class.schema.get(prop)),
                                                              recurse,
                                                              excluded_deps = excluded_deps + [node]).node)
                    newprops.append((prop, imported_nodes, reverse_name))
            else:
                newprops.append((prop, value, reverse_name))

        # actually create the node
        log.debug('Creating node')
        result = self.create_node(newprops, _classes = node._classes)

        return wrap_node(result, node_class)


    def __iadd__(self, node):
        """Should allow node, but also list of nodes, graph, ..."""
        if isinstance(node, list):
            for n in node:
                self.add_object(n)
        else:
            self.add_object(node)

        return self


    ### Search methods

    def find_node(self, node, cmp = Equal.OnIdentity, exclude_properties = list()):
        """Return a node in the graph that is equal to the given one using the
        specified comparison type, or None if not found."""

        if cmp == Equal.OnIdentity:
            if self.contains(node):
                log.debug('%s already in graph %s (id)...' % (node, self))
                return node

        elif cmp == Equal.OnValue:
            for n in self.nodes_from_class(node.virtual_class()):
                if node.same_properties(n, exclude = exclude_properties):
                    log.debug('%s already in graph %s (value)...' % (node, self))
                    return n

        elif cmp == Equal.OnLiterals:
            for n in self.nodes_from_class(node.virtual_class()):
                if node.same_properties(n, n.literal_keys(), exclude = exclude_properties):
                    log.debug('%s already in graph %s (literals)...' % (node, self))
                    return n

        elif cmp == Equal.OnUnique:
            obj = node.virtual()
            props = list(set(obj.unique_properties()) - set(exclude_properties))
            for n in self.nodes_from_class(node.virtual_class()):
                if node.same_properties(n, props, cmp = Equal.OnUnique):
                    log.debug('%s already in graph %s (unique)...' % (n, self))
                    return n

        else:
            raise NotImplementedError


    def find_all(self, node_type = None, valid_node = lambda x: True, **kwargs):
        """This method returns a list of the objects of the given type in this graph for which
        the cond function returns True (or sth that evaluates to True).
        It will also only keep those objects that have properties which match the given keyword
        args dictionary.

        When using both the cond function and the type argument, it is useful to know that the
        type is checked first, so that the cond function can safely assume that only objects of
        the correct type are given to it.

        When using keyword args for filtering, you can chain properties using '_' between them.
        it should be configurable whether property value matching should be case-insensitive or
        use regexps in the case of strings.

        If no match is found, it returns an empty list.

        examples:
          g.find_all(node_type = Movie)
          g.find_all(Episode, lambda x: x.season = 2)
          g.find_all(Movie, lambda m: m.releaseYear > 2000)
          g.find_all(Person, role_movie_title = 'The Dark Knight')
          g.find_all(Character, isCharacterOf_movie_title = 'Fear and loathing.*', regexp = True)
        """
        return list(self._find_all(node_type, valid_node, **kwargs))


    def _find_all(self, node_type = None, valid_node = lambda x: True, **kwargs):
        """Implementation of findAll that returns a generator."""
        if isinstance(node_type, basestring):
            node_type = ontology.get_class(node_type)

        if node_type is None:
            nodes = self.nodes()
        elif issubclass(node_type, BaseObject):
            nodes = self.nodes_from_class(node_type)
        elif isinstance(node_type, tuple):
            nodes = set(set(self.nodes_from_class(cls)) for cls in node_type)
        else:
            raise TypeError('ObjectGraph.find_node: Invalid node type: %s' % node_type)

        for node in nodes:
            # TODO: should this go before or after the properties checking? Which is faster in general?
            try:
                if not valid_node(node):
                    continue
            except Exception, e:
                log.warning('valid_node returned an exception: %s' % e)
                continue

            valid = True
            for prop, value in kwargs.items():
                try:
                    # FIXME: this doesn't work with lists of objects
                    if isinstance(value, BaseObject):
                        value = value.node

                    if node.get_chained_properties(prop.split('_')) != value:
                        valid = False
                        break
                except AttributeError:
                    valid = False
                    break

            if not valid:
                continue

            if node_type is None:
                yield node
            else:
                if isinstance(node_type, tuple):
                    for cls in node_type:
                        if node.isinstance(cls):
                            yield cls(node)
                            break
                    else:
                        raise TypeError('ObjectGraph._find_all: asked for nodes of type %s but found this one: %s' % (node_type, node))
                else:
                    yield node_type(node)


    def find_one(self, node_type = None, valid_node = lambda x: True, **kwargs):
        """Returns a single result. see find_all for description.
        Raises an exception if no result was found."""
        # NB: as _findAll is a generator, this should be fairly optimized
        result = self._find_all(node_type, valid_node, **kwargs)
        try:
            return result.next()
        except StopIteration:
            if isinstance(node_type, BaseObject):
                node_type = node_type.__name__
            raise ValueError('Could not find given %s with props %s' % (node_type if node_type else 'node', kwargs))


    def find_or_create(self, node_type, **kwargs):
        '''This method returns the first object in this graph which has the specified type and
        properties which match the given keyword args dictionary.
        If no match is found, it creates a new object with the keyword args, inserts it in the
        graph, and returns it.

        example: g.findOrCreate(Series, title = 'Arrested Development')'''
        try:
            return self.find_one(node_type, **kwargs)
        except ValueError:
            return node_type(graph = self, **kwargs)

    ## Let's make PyLint happy and let it know that the following methods are still not implemented

    def clear(self):
        """Delete all nodes and links in this graph."""
        raise NotImplementedError

    def create_node(self, props = list(), _classes = set()):
        """Create a node with the given properties and classes."""
        raise NotImplementedError

    def delete_node(self, node):
        """Remove a given node from this graph.

        Strategies for what to do with linked nodes should be configurable, ie:
        remove incoming/outgoing linked nodes as well, only remove link but do
        not touch linked nodes, etc..."""
        raise NotImplementedError

    def nodes(self):
        """Return an iterable on all the nodes in the graph."""
        raise NotImplementedError

    def nodes_from_class(self, cls):
        """Return an iterable on the nodes of a given class."""
        raise NotImplementedError

    def contains(self, node):
        """Return whether this graph contains the given node.

        multiple strategies can be used here for determing object equality, such
        as all properties equal, the primary subset of properties equal, etc...
        (those are defined by the ObjectNode)"""
        raise NotImplementedError
