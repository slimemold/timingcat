#!/usr/bin/env python3

"""Defaults

This module contains constants for various application defaults. They are provided here as a
central location for tweaking.
"""

from PyQt5.QtCore import QSize
from common import VERSION

__author__ = 'Andrew Chew'
__copyright__ = '''
    Copyright (C) 2018 Andrew Chew

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
__credits__ = ['Andrew Chew', 'Colleen Chew']
__license__ = 'GPLv3'
__version__ = VERSION
__maintainer__ = 'Andrew Chew'
__email__ = 'andrew@5rcc.com'
__status__ = 'Development'

RACE_NAME = '(race name here)'
RACE_NOTES_PLACEHOLDER_TEXT = 'Add notes here...'
FIELD_NAME = 'default'
START_TIME_FROM_NOW_SECS = 300 # 5 minutes
START_TIME_INTERVAL_SECS = 60
DATETIME_FORMAT = 'h:mm:ss.zzz'
FIELD_TABLE_VIEW_SIZE = QSize(520, 600)
RACER_TABLE_VIEW_SIZE = QSize(1000, 800)
RESULT_TABLE_VIEW_SIZE = QSize(280, 400)
ALWAYS_ON_TOP = True
DIGITAL_CLOCK = True
