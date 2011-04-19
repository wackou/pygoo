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

from pygoo.objectnode import ObjectNode
from pygoo.abstractdirectedgraph import AbstractDirectedGraph
from pygoo.memoryobjectnode import MemoryObjectNode
from pygoo.objectgraph import ObjectGraph
import logging

log = logging.getLogger('pygoo.MemoryObjectGraph')


class MemoryObjectGraph(ObjectGraph):
    _object_node_class = MemoryObjectNode

    def __init__(self, **kwargs):
        super(MemoryObjectGraph, self).__init__(**kwargs)
        self._nodes = set()

    def clear(self):
        self._nodes.clear()

    def create_node(self, props = [], _classes = set()):
        return self.__class__._object_node_class(self, props, _classes)

    def delete_node(self, node):
        node.unlink_all()
        node.graph = None
        self._nodes.remove(node)

        # FIXME: we need to revalidate the nodes touched by unlink_all()
        #        actually, we need to look whether to unlink or not depending
        #        on the property characteristics (eg: cascade, set null, ...)


    def nodes(self):
        for node in self._nodes:
            yield node

    def nodes_from_class(self, cls):
        return (node for node in self._nodes if node.isinstance(cls))

    def contains(self, node):
        """Return whether this graph contains the given node (identity)."""
        return node in self._nodes

    # __getstate__ and __setstate__ are needed for the cache to be able to work
    def __setstate__(self, state):
        self._nodes = set()
        super(MemoryObjectGraph, self).__setstate__(state)

