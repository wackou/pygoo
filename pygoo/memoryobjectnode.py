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
from pygoo.objectnode import ObjectNode
from pygoo.utils import tolist, toresult, is_literal, to_iterator
from pygoo import ontology
import logging

log = logging.getLogger(__name__)

class MemoryObjectNode(ObjectNode):

    def __init__(self, graph, props = list(), _classes = set()):
        # NB: this should go before super().__init__() because we need
        #     self._props and self._classes to exist before we can set
        #     attributes
        self._props = {}
        self._classes = set(_classes)
        super(MemoryObjectNode, self).__init__(graph, props)

        log.debug('MemoryNode.__init__: classes = %s' % list(self._classes))
        graph._nodes.add(self)


    def __eq__(self, other):
        return self is other

    def __hash__(self):
        # TODO: verify me
        return id(self)

    def __setattr__(self, name, value):
        if name in [ '_props', '_classes' ]:
            object.__setattr__(self, name, value)
        else:
            super(MemoryObjectNode, self).__setattr__(name, value)


    ### Ontology methods

    def add_class(self, cls):
        self._classes.add(cls)

    def remove_class(self, cls):
        self._classes.remove(cls)

    def clear_classes(self):
        self._classes = set()

    def classes(self):
        return self._classes

    def isinstance(self, cls):
        return cls in self._classes



    ### Accessing literal properties

    def get_literal(self, name):
        # if name is not a literal, we need to throw an exception
        result = self._props[name]
        if is_literal(result):
            return result
        raise AttributeError

    def set_literal(self, name, value):
        self._props[name] = value

    # FIXME: need to implement del_literal here

    def literal_keys(self):
        return (k for k, v in self._props.items() if is_literal(v))

    def literal_values(self):
        return (v for v in self._props.values() if is_literal(v))

    def literal_items(self):
        return ((k, v) for k, v in self._props.items() if is_literal(v))



    ### Accessing edge properties

    def add_directed_edge(self, name, other_node):
        # otherNode should always be a valid node
        node_list = tolist(self._props.get(name))
        node_list.append(other_node)
        self._props[name] = toresult(node_list)

    def remove_directed_edge(self, name, other_node):
        # other_node should always be a valid node
        node_list = tolist(self._props.get(name))
        node_list.remove(other_node)
        self._props[name] = toresult(node_list)

        # TODO: we should have this, right?
        if self._props[name] is None:
            del self._props[name]


    def outgoing_edge_endpoints(self, name = None):
        if name is None:
            return self._all_outgoing_edge_endpoints()
        else:
            return self._outgoing_edge_endpoints(name)

    def _outgoing_edge_endpoints(self, name):
        # if name is not an edge, we need to throw an exception
        result = self._props[name]
        if not is_literal(result):
            return to_iterator(result)
        raise AttributeError

    def _all_outgoing_edge_endpoints(self):
        for prop, eps in self.edge_items():
            for ep in eps:
                yield ep


    def edge_keys(self):
        return (k for k, v in self._props.items() if not is_literal(v))

    def edge_values(self):
        return (to_iterator(v) for v in self._props.values() if not is_literal(v))

    def edge_items(self):
        return ((k, to_iterator(v)) for k, v in self._props.items() if not is_literal(v))


    # The next methods are overriden for efficiency
    # They should take precedence over their implementation in ObjectNode, as long as the order
    # of inheritance is respected, ie:
    #
    #   class MemoryObjectNode(MemoryNode, ObjectNode): # GOOD
    #   class MemoryObjectNode(ObjectNode, MemoryNode): # BAD

    def keys(self):
        return self._props.keys()

    # FIXME: wrong implementation as the values for edges should be iterators
    #def values(self):
    #    return self._props.values()

    #def items(self):
    #    return self._props.items()

    def update_valid_classes(self):
        if self.graph()._dynamic:
            self._classes = set(cls for cls in ontology._classes.values() if self.is_valid_instance(cls))
        else:
            # no need to do anything
            pass
