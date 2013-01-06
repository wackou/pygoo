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

class TestAdvancedGraph(TestCase):

    def setUp(self):
        ontology.reload_saved_ontology('media')

    def testOnUniqueComparison(self):
        # mimics a typical import scenario for smewt:
        #  - we first import a few files
        #  - then we reimport them, with the same values.
        #  - graph should be the same, no duplicates
        ontology.import_all_classes()

        # initial import
        tmp1 = MemoryObjectGraph()
        s = tmp1.Series(title='Monk')
        ep = tmp1.Episode(series=s, season=1, episodeNumber=1, title='ep 1x01')
        epfile = tmp1.File(video=ep, filename='ep_1x01.avi')

        sub = tmp1.Subtitle(video=ep, language='en')
        subfile = tmp1.File(subtitle=sub, filename='ep_1x01.en.srt')


        #tmp1.display_graph()

        collection = MemoryObjectGraph()
        epfilec = collection.add_object(ep, recurse=Equal.OnUnique)

        print 'from collec', collection.find_node(epfilec.node, cmp=Equal.OnUnique)
        #epfilec2 = collection.Media(metadata = epfilec.metadata, filename = 'ep_1x01.avi', other = 'different, but same unique values')
        #collection.display_graph()
        #n1 = collection.find_node(epfilec.node, cmp = Equal.OnUnique)
        #n2 = collection.find_node(epfilec2.node, cmp = Equal.OnUnique)
        #n3 = collection.find_node(epfile.node, cmp = Equal.OnUnique)

        #print 'from collec copy', n1
        #print 'from collec copy2', n2
        #print 'from outside', n3

        #self.assertEqual(n1, n2)
        #self.assert_(n3 is not None)

        #collection.display_graph('before')
        collection.add_object(sub, recurse=Equal.OnUnique)

        #collection.display_graph('collec1')

        self.assertEqual(len(collection.find_all(Episode)), 1)
        self.assertEqual(len(collection.find_all(Subtitle)), 1)
        self.assertEqual(len(collection.find_all(File)), 2)

        # second import, same objects
        tmp2 = MemoryObjectGraph()
        s = tmp2.Series(title='Monk')
        ep = tmp2.Episode(series=s, season=1, episodeNumber=1, title='ep 1x01')
        epfile = tmp2.File(video=ep, filename='ep_1x01.avi')

        sub = tmp2.Subtitle(video=ep, language='en')
        subfile = tmp2.File(subtitle=sub, filename='ep_1x01.en.srt')

        #tmp1.display_graph()

        collection.add_object(epfile, recurse=Equal.OnUnique)

        self.assertEqual(len(collection.find_all(Episode)), 1)
        self.assertEqual(len(collection.find_all(Subtitle)), 1)
        self.assertEqual(len(collection.find_all(File)), 2)

        #collection.display_graph('collec 2 + epfile')

        collection.add_object(subfile, recurse=Equal.OnUnique)

        self.assertEqual(len(collection.find_all(Episode)), 1)
        self.assertEqual(len(collection.find_all(Subtitle)), 1)
        self.assertEqual(len(collection.find_all(File)), 2)

        #collection.display_graph('collec 2 + subfile')

        collection.add_object(ep, recurse=Equal.OnUnique)
        #collection.display_graph('collec 2 + ep md')
        self.assertEqual(len(collection.find_all(Episode)), 1)
        self.assertEqual(len(collection.find_all(Subtitle)), 1)
        self.assertEqual(len(collection.find_all(File)), 2)

        collection.add_object(sub, recurse=Equal.OnUnique)
        #collection.display_graph('collec 2 + sub md')
        self.assertEqual(len(collection.find_all(Episode)), 1)
        self.assertEqual(len(collection.find_all(Subtitle)), 1)
        self.assertEqual(len(collection.find_all(File)), 2)


suite = allTests(TestAdvancedGraph)

if __name__ == '__main__':
    TextTestRunner(verbosity=2).run(suite)
