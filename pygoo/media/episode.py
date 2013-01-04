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
from pygoo.media import Video, Series

class Episode(Video):

    schema = { 'series': Series,
               'season': int,
               'episodeNumber': int,
               'title': unicode
               }

    reverse_lookup = { 'series': ['episodes'] }

    valid = ['series', 'season', 'episodeNumber']

    def display_string(self):
        return 'episode %dx%02d of %s' % (self.season, self.episodeNumber,
                                          self.series.display_string())
