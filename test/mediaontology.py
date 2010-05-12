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

from pygoo import *

class Metadata(BaseObject):
    schema = { 'confidence': float,
               'watched': bool
               }

    valid = []


class Media(BaseObject):
    schema = { 'filename': unicode,
               'sha1': unicode,
               'metadata': Metadata,
               'watched': bool, # TODO: or is the one from Metadata sufficient?

               # used by guessers and solvers
               'matches': Metadata
               }

    valid = [ 'filename' ]
    unique = [ 'filename' ]
    reverse_lookup = { 'metadata': 'files',
                       'matches': 'query' }

    types = { 'video': [ 'avi', 'ogm', 'mkv', 'mpg', 'mpeg' ],
              'subtitle': [ 'sub', 'srt' ]
              }

    def ext(self):
        return self.filename.split('.')[-1]

    def type(self):
        ext = self.ext()
        for name, exts in Media.types.items():
            if ext in exts:
                return name
        return 'unknown type'



class Series(Metadata):

    schema = { 'title': unicode,
               'numberSeasons': int,
               #'episodeList': list
               }

    valid = [ 'title' ]
    unique = [ 'title' ]

    #converters = { 'episodeList': lambda x:x } #parseEpisodeList }


class Episode(Metadata):

    schema = { 'series': Series,
               'season': int,
               'episodeNumber': int,
               'title': unicode
               }

    valid = [ 'series', 'season', 'episodeNumber' ]
    reverse_lookup = { 'series': 'episodes' }
    #order = [ 'series', 'season', 'episodeNumber',  'title' ]

    unique = [ 'series', 'season', 'episodeNumber' ]

    converters = {}


class Movie(Metadata):

    typename = 'Movie'

    schema = { 'title': unicode,
               'year': int,
               # more to come
               }

    valid = [ 'title' ]

    unique = [ 'title', 'year' ]

    order = [ 'title', 'year' ]

    converters = {}


class Subtitle(Metadata):
    """Metadata object used for representing subtitles.

    Note: the language property should be the 2-letter code as defined in:
    http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    """

    typename = 'Subtitle'

    schema = { 'metadata': Metadata,
               'language': unicode }

    valid = [ 'metadata' ]

    reverse_lookup = { 'metadata': 'subtitles' }

    order = [ 'metadata', 'language' ]

    unique = [ 'metadata', 'language' ]

    converters = {}


class Comment(BaseObject):
    schema = { 'metadata': Metadata,
               'author': unicode,
               'text': unicode,
               'date': int
               }

    reverse_lookup = { 'metadata': 'comments' }

    valid = [ 'metadata', 'author', 'date' ]
    unique = [ 'metadata', 'author', 'date' ]



