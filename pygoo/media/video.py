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
from pygoo.baseobject import BaseObject
from pygoo.media import File
from guessit.patterns import video_exts
from fnmatch import fnmatch

class Video(BaseObject):
    """Represent a video media entity independent of its physical location."""

    schema = { 'files': [File],
               'watched': bool
               }

    valid = []

    reverse_lookup = { 'files': 'video'
                       }

    @staticmethod
    def isValidVideo(filename):
        return any(fnmatch(filename, '*.' + ext) for ext in video_exts)

    def playUrl(self):
        files = self.get('files')
        # FIXME: move this here in a separate unittest
        assert(type(files) == list)
        # prepare link for playing movie without subtitles
        nfile = 1
        args = {}
        for f in sorted(files, key=lambda f: f.get('filename')):
            args['filename%d' % nfile] = f.filename
            nfile += 1

        if not args:
            raise SmewtException('No files to play!...')

        return SmewtUrl('action', 'play', args)
