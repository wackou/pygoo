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

__all__ = ['File', 'Video', 'Movie', 'Comment', 'Series', 'Episode', 'Subtitle']

"""pygoo.media contains a media ontology covering mostly movies and tv shows/episodes.

Importing it will require you to have a recent version of GuessIt installed.

Note that GuessIt is not a hard dependency on PyGoo proper, it is only needed if you
import directly pygoo.media or any submodule.
"""

from .file import File
from .video import Video

from pygoo import ontology
ontology.print_classes()
ontology.save_current_ontology('video')

from .movie import Movie, Comment
from .series import Series
from .episode import Episode
from .subtitle import Subtitle