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

# import unittest and everything from pygoo
from unittest import TestCase
from pygoo import *

# import potentially useful modules for the tests (which will import * from this file)
import os

# we don't want to be too verbose in tests
import logging
logging.getLogger('pygoo').setLevel(logging.WARNING)

# before starting any tests, save pygoo's media ontology in case we mess with it and need it again later
from mediaontology import *
ontology.save_current_ontology('media')
