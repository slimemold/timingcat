#!/usr/bin/env python3

"""Common

This module is a dumping ground for various utilities and constants that can be used throughout
the package.
"""

import os
import platform
import sys
from PyQt5.QtCore import QSettings, QStandardPaths
from PyQt5.QtWidgets import QFileDialog

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

GENERAL_QSETTINGS_GROUP = 'General'
QSETTINGS_KEY_DOCUMENTS_FOLDER = 'doc_dir'

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

class FileDialog(QFileDialog):
    """Our QFileDialog subclass.

    This file dialog saves the last directory that's been navigated to.
    """
    def __init__(self, parent=None):
        """Initialize the FileDialog instance."""
        super().__init__(parent=parent)

        self.setOptions(QFileDialog.DontUseNativeDialog)
        self.setViewMode(QFileDialog.List)
        self.setDirectory(self.get_documents_dir())

    def exec(self):
        """Executes the file dialog, and if accepted, saves the directory.

        The next time we make a file dialog, we go to the same directory.
        """
        dialog_code = super().exec()

        # If dialog is "accepted", save directory.
        if dialog_code:
            filename = self.selectedFiles()[0]
            self.set_documents_dir(os.path.dirname(filename))

        return dialog_code

    def get_documents_dir(self, ):
        """Returns the user's documents directory.

        Use the saved setting if it exists. Otherwise, use the system's standard user Documents
        directory.
        """
        standard_documents_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)

        group_name = GENERAL_QSETTINGS_GROUP
        settings = QSettings()
        settings.beginGroup(group_name)

        documents_dir = settings.value(QSETTINGS_KEY_DOCUMENTS_FOLDER, standard_documents_dir)

        settings.endGroup()

        return documents_dir

    def set_documents_dir(self, dir_name):
        """Set the user's documents directory.

        Save the directory in settings. If settings matches default, remove settings.
        """
        standard_documents_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)

        group_name = GENERAL_QSETTINGS_GROUP
        settings = QSettings()
        settings.beginGroup(group_name)

        if dir_name == standard_documents_dir:
            settings.remove(QSETTINGS_KEY_DOCUMENTS_FOLDER)
        else:
            settings.setValue(QSETTINGS_KEY_DOCUMENTS_FOLDER, dir_name)

        settings.endGroup()

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
    elif _system == 'Windows':
        import keyring.backends.Windows #pylint: disable=wrong-import-position
        keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())
