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

from __future__ import with_statement
from pygoo.memoryobjectnode import MemoryObjectNode
from pygoo.objectnode import ObjectNode
import neo
import logging

log = logging.getLogger('pygoo.Neo4jObjectNode')


# SYNC can take 2 values:
# - AUTO: automatically synchronize changes with the underlying store as they are modified
# - MANUAL: only flush data to store when the synchronize() method is called
#
# when SYNC == 'AUTO', there is another option to get rid of the calls to the caching MemoryObjectNode (ie: pure database-based)


class Neo4jObjectNode(MemoryObjectNode):
    """This is a proxy class for the neo4j instances.
    It derives from the MemoryObjectNode, which serves as a cache.
    This only loads the nodes needed from the DB when it needs them."""

    def __init__(self, graph, props = [], neonode = None):
        if neonode is not None:
            self._neonode = neonode
            return

        literal = {}
        links = []
        for prop, value, reverse_name in props:
            if isinstance(value, ObjectNode):
                links.append((prop, value, reverse_name))
            else:
                literal[prop] = value

        print 'starting transaction'
        with neo.transaction:
            self._neonode = neo.graph.node(**literal)
            print 'node created'
            self._neonode._ingraph(neo.graph.reference_node) # as a way to get them all
            print 'setting links'
            for link in links:
                self.setLink(*link)
            print 'setting links ok'
        print 'transaction ok'

        #MemoryObjectNode.__init__(self, graph, props)


    def __eq__(self, other):
        return self._neonode == other._neonode

    def __hash__(self):
        # TODO: verify me
        return id(self)

    ### Acessing properties methods


    def __setattr__(self, name, value):
        if name == '_neonode':
            object.__setattr__(self, name, value)
        else:
            MemoryObjectNode.__setattr__(self, name, value)

    def get_link(self, name):
        log.debug('getlink:', name)
        return to_result([ r.end for r in self._neonode.relationships() if r.type == name ])

    def get_literal(self, name):
        log.debug('getliteral:', name)
        result = self._neonode[name]
        if isinstance(result, basestring):
            return result

        return result.value # fix in neo4j.py

    def set_literal(self, name, value):
        MemoryObjectNode.set_literal(self, name, value) # keep in cache
        with neo.transaction:
            self._neonode[name] = value

    #def update(self, props):
