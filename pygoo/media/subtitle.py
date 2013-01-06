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
from guessit.patterns import subtitle_exts
from guessit import Language
from pygoo.baseobject import BaseObject
from pygoo.media import Video, File
from os.path import splitext
from fnmatch import fnmatch

def str2lang(s):
    if isinstance(s, basestring):
        return Language(s)
    return s

class Subtitle(BaseObject):
    """Object used for representing subtitles.

    Note: the type guessit.Language is a literal, not an outgoing edge.
    """

    schema = { 'video': Video,
               'language': Language,
               'files': [File]
               }

    reverse_lookup = { 'video': 'subtitle',
                       'files': 'subtitle'
                       }

    valid = [ 'video' ]
    unique = [ 'video', 'language' ]
    converters = { 'language': str2lang }


    @staticmethod
    def isValidSubtitle(filename):
        return any(fnmatch(filename, '*.' + ext) for ext in subtitle_exts)

    def subtitleLink(self):
        flag = utils.smewtMediaUrl('common', 'images', 'flags',
                                   '%s.png' % Language(self.language).alpha2)

        sfiles = []
        for subfile in utils.tolist(self.files):
            subtitleFilename = subfile.filename
            videoFiles = utils.tolist(self.metadata.get('files'))
            # we shouldn't need to check that they start with the same prefix anymore, as
            # the taggers/guessers should have mapped them correctly
            mediaFilename = [ f.filename for f in videoFiles
                              if subtitleFilename.startswith(splitext(f.filename)[0])
                              ]
            mediaFilename = mediaFilename[0] if mediaFilename else ''

            sfiles += [ (mediaFilename, subtitleFilename) ]


        # FIXME: cannot put this import above otherwise we create an infinite
        # import recursion loop...
        from smewt.base.actionfactory import PlayAction

        return utils.SDict({ 'languageImage': flag,
                             'url': PlayAction(sfiles).url()})
