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

from unittest import *
from pygoo import *
from pygoo import ontology
from pygoo.media import *
from pygoo.slogging import setupLogging
import logging
import os

MAIN_LOGGING_LEVEL = logging.INFO

setupLogging()
logging.getLogger().setLevel(MAIN_LOGGING_LEVEL)
logging.getLogger('pygoo.ontology').setLevel(logging.WARNING)
#logging.getLogger('pygoo.objectgraph').setLevel(logging.DEBUG)

# FIXME: remove this after fixing guessit
logging.getLogger('guessit.language').setLevel(logging.WARNING)


def allTests(testClass):
    return TestLoader().loadTestsFromTestCase(testClass)
