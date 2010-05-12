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

from pygoo.memoryobjectgraph import MemoryObjectGraph
from pygoo.neo4jobjectnode import Neo4jObjectNode
import neo4j
import neo
import logging

log = logging.getLogger('pygoo.Neo4jObjectGraph')

class AllNodes(neo4j.Traversal):
    types = [
        neo4j.Incoming._ingraph,
        ]
    order = neo4j.DEPTH_FIRST
    stop = neo4j.STOP_AT_END_OF_GRAPH
    returnable = neo4j.RETURN_ALL_BUT_START_NODE

def all_nodes():
    # FIXME: ATM returns neo nodes, not expected Neo4jObjectNodes
    return AllNodes(neo.graph.reference_node)

class Neo4jObjectGraph(MemoryObjectGraph):
    """A Neo4jObjectGraph is an ObjectGraph where all data is persistent on disk.
    All attribute modifications are immediately synchronized on the data store.

    A Neo4jObjectGraph uses PersistentObjectNodes."""
    _object_node_class = Neo4jObjectNode

    def __init__(self, dbpath):
        MemoryObjectGraph.__init__(self)
        neo.open(dbpath)

    def close():
        neo.close()

    def clear(self):
        """Delete all objects in this graph."""
        MemoryObjectGraph.clear(self)

        neo.delete_all_data()

    def __contains__(self, node):
        """Return whether this graph contains the given node (identity)."""
        # TODO: only works if correctly cached
        return get_node(node) in self._nodes


    def nodes(self):
        for n in all_nodes():
            yield Neo4jObjectNode(neonode = n)


    def remove_directed_edge(self, node, name, other_node):
        MemoryObjectGraph.remove_directed_edge(self, node, name, other_node)

        for r in node._neonode.relationships():
            if r.end == other_node and r.type == name:
                r.delete()
                # return early, which means if we had the same link multiple times,
                # we only remove one of them. This could be used for doing ref-counting if necessary
                return

    def add_directed_edge(self, node, name, other_node):
        MemoryObjectGraph.add_directed_edge(self, node, name, other_node)

        setattr(node._neonode, name, other_node._neonode)
