#!/usr/bin/env python3

"""Common

This module is a dumping ground for various utilities and constants that can be used throughout
the package.
"""

import os
import platform
import sys

ORGANIZATION_NAME = '5rcc'
ORGANIZATION_DOMAIN = '5rcc.com'
APPLICATION_NAME = 'SexyThyme'
AUTHOR = 'Andrew Chew'
CREDITS = ['Andrew Chew', 'Colleen Chew', 'Richard Brockie']
LICENSE = 'GPLv3'
VERSION = '1.0.0'
MAINTAINER = 'Andrew Chew'
EMAIL = 'andrew@5rcc.com'
STATUS = 'Development'

__author__ = AUTHOR
__copyright__ = '''
    Copyright (C) 2018-2019 Andrew Chew

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
__credits__ = CREDITS
__license__ = LICENSE
__version__ = VERSION
__maintainer__ = MAINTAINER
__email__ = EMAIL
__status__ = STATUS

def app_path():
    """Returns the path where this application is.

    This is normally the project directory (the directory where this file is), but when running
    a pyinstaller bundle, the project directory is in some temporary directory.
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the pyInstaller boot loader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS'.
        return sys._MEIPASS #pylint: disable=no-member,protected-access
    else:
        return os.path.dirname(os.path.abspath(__file__))

def pretty_list(lst, op='and'):
    """Takes a list of words and returns a comma-separated conjunction (with oxford comma)."""

    # Filter out any "None"s.
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

def enum(**enums):
    """Simulate an enum."""
    return type('Enum', (), enums)

# Work around pyinstaller's inability to handle keyring's use of the entrypoint module. We have to
# set the keyring backend manually (auto-detect doesn't work).
if getattr(sys, 'frozen', False):
    import keyring #pylint: disable=wrong-import-position

    _system = platform.system() #pylint: disable=invalid-name

    if _system == 'Darwin':
        import keyring.backends.OS_X #pylint: disable=wrong-import-position
        keyring.set_keyring(keyring.backends.OS_X.Keyring())
    elif _system == 'Linux':
        import keyring.backends.SecretService #pylint: disable=wrong-import-position
        keyring.set_keyring(keyring.backends.SecretService.Keyring())
    elif _system == 'Linux':
        import keyring.backends.Windows #pylint: disable=wrong-import-position
        keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())
