#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PyGoo - An Object-Graph mapper
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
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

class TestOntology(TestCase):

    def setUp(self):
        print 'SETUP CLEAR ONTOLOGY'
        ontology.clear()

    def atestBasicOntology(self):
        class A(BaseObject):
            schema = { 'title': unicode }
            valid = ['title']
            #unique = ['title']
            unique = valid # use same object on purpose to make sure it still works with aliasing

        class B(A):
            schema = {}
            #valid = [ 'title' ]
            valid = A.valid
            unique = [ 'title' ]

        class C(BaseObject):
            schema = { 'c': int }
            valid = schema.keys()
            unique = valid

        class D(BaseObject):
            schema = {}
            valid = []

        class E:
            schema = { 'e': int }
            unique = [ 'e' ]

        class F(BaseObject):
            schema = { 'friend': BaseObject }
            reverse_lookup = { 'friend': 'friend' }
            valid = schema.keys()

        ontology.print_class(F)

        self.assertEqual(issubclass(A, BaseObject), True)
        self.assertEqual(issubclass(B, A), True)
        self.assertEqual(issubclass(A, A), True)
        self.assertEqual(issubclass(A, B), False)
        self.assertEqual(issubclass(B, BaseObject), True)
        self.assertEqual(issubclass(C, A), False)
        self.assertEqual(B.parent_class().class_name(), 'A')

        #self.assertRaises(TypeError, ontology.register, E) # should inherit from BaseObject
        # should not define the same reverse_lookup name when other class is a superclass (or subclass) of our class
        self.assertRaises(TypeError, ontology.register, F)

        self.assert_(ontology.get_class('A') is A)
        #self.assertRaises(ValueError, ontology.get_class, 'D') # not registered
        self.assert_(ontology.get_class('B').parent_class().parent_class() is BaseObject)

        # test instance creation
        g = MemoryObjectGraph()
        a = g.A(title = u'Scrubs', epnum = 5)

        self.assertEqual(type(a), A)
        self.assertEqual(a.__class__, A)
        self.assertEqual(a.__class__.class_name(), 'A')
        self.assertEqual(a.__class__.__name__, 'A')


    def atestBaseObject(self, GraphClass = MemoryObjectGraph):
        class NiceGuy(BaseObject):
            schema = { 'friend': BaseObject }
            valid = [ 'friend' ]
            reverse_lookup = { 'friend': 'friendOf' }

        # There is a problem when the reverse-lookup has the same name as the property because of the types:
        # NiceGuy.friend = BaseObject, BaseObject.friend = NiceGuy
        #
        # it should also be possible to have A.friend = B and C.friend = B, and not be a problem for B, ie: type(B.friend) in [ A, C ]
        #
        # or we should restrict the ontology only to accept:
        #  - no reverseLookup where key == value
        #  - no 2 classes with the same link types to a third class
        # actually, no reverseLookup where the implicit property could override an already existing one

        g1 = GraphClass()
        g2 = GraphClass()

        n1 = g1.BaseObject(n = 'n1', a = 23)
        n2 = g1.NiceGuy(n = 'n2', friend = n1)
        self.assertEqual(n1.friendOf, n2)

        r2 = g2.add_object(n2)
        r2.n = 'r2'
        self.assertEqual(n1.friendOf, n2)

    def testMediaOntologyRelations(self):
        """Test whether the ONE_TO_ONE and ONE_TO_MANY relations work correctly."""

        ontology.import_ontology('video')
        ontology.print_classes()

        self.assertEqual(ontology.ORDERED_ONE_TO_MANY, Video.schema._relations['files'])
        self.assertEqual(ontology.ORDERED_MANY_TO_ONE, File.schema._relations['video'])

        ontology.import_ontology('media')
        ontology.print_classes()

        # Video relations
        self.assertEqual(ontology.ORDERED_ONE_TO_MANY, Video.schema._relations['files'])
        self.assertEqual(ontology.ORDERED_MANY_TO_ONE, File.schema._relations['video'])
        self.assertEqual(ontology.ONE_TO_ONE, Video.schema._relations['subtitle'])
        self.assertEqual(ontology.ONE_TO_ONE, Subtitle.schema._relations['video'])

        # Movie relations
        self.assertEqual(ontology.ORDERED_ONE_TO_MANY, Movie.schema._relations['files'])
        self.assertEqual(ontology.ORDERED_MANY_TO_ONE, File.schema._relations['video'])
        self.assertEqual(ontology.ONE_TO_ONE, Movie.schema._relations['subtitle'])
        self.assertEqual(ontology.ONE_TO_ONE, Subtitle.schema._relations['video'])
        self.assertEqual(ontology.UNORDERED_ONE_TO_MANY, Movie.schema._relations['comments'])
        self.assertEqual(ontology.UNORDERED_MANY_TO_ONE, Comment.schema._relations['movie'])

        # Episode relations
        self.assertEqual(ontology.ORDERED_ONE_TO_MANY, Episode.schema._relations['files'])
        self.assertEqual(ontology.ORDERED_MANY_TO_ONE, File.schema._relations['video'])
        self.assertEqual(ontology.ONE_TO_ONE, Episode.schema._relations['subtitle'])
        self.assertEqual(ontology.ONE_TO_ONE, Subtitle.schema._relations['video'])
        self.assertEqual(ontology.ORDERED_ONE_TO_MANY, Series.schema._relations['episodes'])
        self.assertEqual(ontology.ORDERED_MANY_TO_ONE, Episode.schema._relations['series'])

    def registerMediaOntology(self):
        # use pygoo.media
        pass

# TODO: more ontology stuff in test_objectnode.py

suite = allTests(TestOntology)

if __name__ == '__main__':
    TextTestRunner(verbosity=2).run(suite)
