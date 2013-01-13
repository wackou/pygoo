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
from pygootest import *

class TestObjectNode(TestCase):

    def setUp(self):
        ontology.clear()

    def testMRO(self):
        class A(object):
            def __init__(self):
                print 'A.__init__()'

            def __contains__(self, obj):
                print 'A.__contains__'

        class B(A):
            def __init__(self):
                super(B, self).__init__()
                print 'B.__init__()'

            #def __contains__(self, obj):
            #    print 'B.__contains__'

        class C(A):
            def __init__(self):
                super(C, self).__init__()
                print 'C.__init__()'

            def __contains__(self, obj):
                print 'C.__contains__'

        class D(B, C):
            def __init__(self):
                super(D, self).__init__()
                print 'D.__init__()'

            #def __contains__(self, obj):
            #    print 'D.__contains__'

        d = D()
        3 in d

    def testAbstractNode(self, GraphClass = MemoryObjectGraph):
        g = GraphClass()

        n = g.create_node()
        n.set_literal('title', 'abc')
        self.assertEqual(n.get_literal('title'), 'abc')
        self.assertEqual(list(n.literal_keys()), [ 'title' ])
        self.assertEqual(list(n.edge_keys()), [])

        n2 = g.create_node()
        n.add_directed_edge('friend', n2)
        n2.add_directed_edge('friend', n)
        self.assertEqual(n.get_literal('title'), 'abc')
        self.assertEqual(list(n.literal_keys()), [ 'title' ])
        self.assertEqual(list(n.edge_keys()), [ 'friend' ])
        self.assertEqual(list(n.outgoing_edge_endpoints('friend')), [ n2 ])
        self.assertEqual(list(n2.outgoing_edge_endpoints('friend')), [ n ])

        n3 = g.create_node()
        n.add_directed_edge('friend', n3)
        n3.add_directed_edge('friend', n)
        self.assertEqual(len(list(n.outgoing_edge_endpoints('friend'))), 2)
        self.assertEqual(len(list(n.outgoing_edge_endpoints())), 2)
        self.assert_(n2 in n.outgoing_edge_endpoints('friend'))
        self.assert_(n3 in n.outgoing_edge_endpoints('friend'))


    def testBasicObjectNode(self, ObjectGraphClass = MemoryObjectGraph):
        g = ObjectGraphClass()

        n = g.create_node()
        n.title = 'abc'
        self.assertEqual(n.get_literal('title'), 'abc')
        self.assertEqual(list(n.literal_keys()), [ 'title' ])
        self.assertEqual(list(n.edge_keys()), [])

        n2 = g.create_node()
        n.friend = n2
        self.assertEqual(n.title, 'abc')
        self.assertEqual(list(n.literal_keys()), [ 'title' ])
        self.assertEqual(list(n.edge_keys()), [ 'friend' ])
        self.assertEqual(list(n.friend), [ n2 ])
        self.assertEqual(list(n2.isFriendOf), [ n ])

        n3 = g.create_node()
        n.friend = [ n2, n3 ]
        self.assert_(n in n2.isFriendOf)
        self.assert_(n in n3.isFriendOf)
        with self.assertRaises(StopIteration):
            next(n3.get('friend'))

        n4 = g.create_node()
        n4.friend = n.friend
        self.assert_(n in n2.isFriendOf)
        self.assert_(n in n3.isFriendOf)
        self.assert_(n4 in n2.isFriendOf)
        self.assert_(n4 in n3.isFriendOf)

        n.friend = []
        self.assert_(n not in n2.isFriendOf)
        self.assert_(n not in n3.isFriendOf)
        self.assert_(n4 in n2.isFriendOf)
        self.assert_(n4 in n3.isFriendOf)




suite = allTests(TestObjectNode)

if __name__ == '__main__':
    TextTestRunner(verbosity=2).run(suite)
