#!/usr/bin/env python3

"""Common

This module is a dumping ground for various utilities and constants that can be used throughout
the package.
"""

APPLICATION_NAME = 'SexyThyme'
VERSION = '1.0.0'

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

def pretty_list(lst, op='and'):
    """Takes a list of words and returns a comma-separated conjunction (with oxford comma)."""

    # Filter out any None's.
    lst = list(filter(None.__ne__, lst))

    if not lst:
        return ''
    if len(lst) == 1:
        return lst[0]
    if len(lst) == 2:
        return lst[0] + ' ' + op + ' ' + lst[1]

    return ', '.join(lst[0:-1]) + ', ' + op + ' ' + lst[-1]

def pluralize(word, count):
    """Takes a word and a count, and returns a phrase. Ex: 18 racers."""
    if count == 0:
        return None

    if count == 1:
        return '%s %s' % (count, word)

    return '%s %s' % (count, word + 's')
