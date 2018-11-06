#!/usr/bin/env python3

"""Preferences Qt Classes

This module implements a QDialog that can be used to set application preferences.
"""

from PyQt5.QtWidgets import QDialog
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

class PreferencesWindow(QDialog):
    """This dialog allows the user to set application preferences."""

    def __init__(self, modeldb, parent=None):
        """Initialize the PreferencesWindow instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.setWindowTitle('Preferences')
