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

import logging

log = logging.getLogger('pygoo.AbstractNode')



class AbstractNode(object):
    """This class describes a basic node in a directed graph, with the addition
    that it has a special property "classes" which describe which class this node
    can "morph" into. This mechanism could be built as another basic node property,
    but it is not for performance reasons.

    It can also have named directed edges to other nodes, ie: the edges are not
    "anonymous", but are first-class citizens (in future versions, we might even
    want to add other properties to an edge).
    A node can have any number of edges of the same type to other nodes (even
    multiples edges to the same node), but it can't have edges to itself.

    The AbstractNode class is the basic interface one needs to implement for
    providing a backend storage of the data. It is complementary to the
    AbstractDirectedGraph interface.

    You only need to provide the implementation for this interface, and then an
    ObjectNode can be automatically built upon it.

    The methods you need to implement fall into the following categories:
     - add / remove / clear / check / get current valid classes
     - get / set / iterate over literal properties
     - add / remove / iterate over edges

    Note: as ObjectNode reimplements the __setattr__ method, you have to do the same
          in your subclass of AbstractNode to catch the instance attributes you need
          to be able to set. Failure to do this will most certainly result in an
          infinite loop, ie: it looks like everything is stuck very soon, or even a
          stack overflow due to infinite recursion.

    """

    def __init__(self, graph, props = list()):
        log.debug('AbstractNode.__init__: graph = %s' % str(graph))


    def __eq__(self, other):
        """Return whether two nodes are equal.

        This should implement identity of nodes, not properties equality (this should
        be done in the BaseObject instance)."""
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError

    ## Methods needed for storing the nodes ontology (caching)
    ## Note: this could be implemented only using literal values, but it is left
    ##       as part of the API as this is something which is used a lot and
    ##       benefits a lot from being optimized, which can be more easily done
    ##       in the implementation

    def add_class(self, cls):
        """Add the given class to the list of valid classes for this node."""
        raise NotImplementedError

    def remove_class(self, cls):
        """Remove the given class from the list of valid classes for this node."""
        raise NotImplementedError

    def clear_classes(self):
        """Clear the current list of valid classes."""
        raise NotImplementedError

    def classes(self):
        """Return an iterator over the list of classes."""
        raise NotImplementedError

    def isinstance(self, cls):
        """Return whether this node contains the given class in its list of valid classes."""
        raise NotImplementedError


    ### Methods related to getting / setting literal properties

    def get_literal(self, name):
        """Return the literal with the given name.

        :raises AttributeError: If the given name doesn't correspond to a literal property of this node.
        """
        raise NotImplementedError

    def set_literal(self, name, value):
        """Sets the literal to the given value.
        This method can assume that value is always one of the valid literal types."""
        raise NotImplementedError

    def literal_keys(self):
        """Return an iterable over the literal names."""
        raise NotImplementedError

    def literal_values(self):
        """Return an iterable over the literal values."""
        raise NotImplementedError

    def literal_items(self):
        """Return an iterable over the literal items (key, value)."""
        raise NotImplementedError


    ## Methods related to getting / setting edges (edge properties that point
    ## to other nodes)

    def add_directed_edge(self, name, other_node):
        """Add a named edge from this node to the given one.
        TODO: both nodes should live in the same graph, right? otherwise we throw an exception?"""
        raise NotImplementedError

    def remove_directed_edge(self, name, other_node):
        """Remove the given edge between the 2 nodes.
        TODO: should we throw an exception if it doesn't exist or ignore it?"""
        raise NotImplementedError

    def outgoing_edge_endpoints(self, name = None):
        """Return all the nodes which this node points to with the given edge type.
        If name is None, return all outgoing edge points."""
        # Note: it is *imperative* that this function return a generator and not
        #       just any iterable over the values
        raise NotImplementedError

    def edge_keys(self):
        """Return an iterable over the edge names."""
        raise NotImplementedError

    def edge_values(self):
        """Return an iterable over the edge values (ie: the nodes pointed to by this one)."""
        # Note: it is *imperative* that this function return a generator for each
        #       value and not just any iterable over the values
        raise NotImplementedError

    def edge_items(self):
        """Return an iterable over the edge items (name, nodes pointed to)."""
        # Note: it is *imperative* that this function return a generator for each
        #       value and not just any iterable over the values
        raise NotImplementedError


    ### Additional utility methods

    def unlink_all(self):
        """Remove all incoming and outgoing edges from this node."""
        for name, nodes in self.edge_items():
            for n in nodes:
                self.remove_directed_edge(name, n)
                for oname, onodes in n.edge_items():
                    for n2 in onodes:
                        if n2 == self:
                            n.remove_directed_edge(oname, self)
