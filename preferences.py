#!/usr/bin/env python3

"""Preferences Qt Classes

This module implements a QDialog that can be used to set application preferences.
"""

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QCheckBox, QDialog, QGroupBox
from PyQt5.QtWidgets import QVBoxLayout
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

        # Appearance preferences.
        self.digital_clock_checkbox = QCheckBox('LCD clock')

        appearance_groupbox = QGroupBox('Appearance')
        appearance_groupbox.setLayout(QVBoxLayout())
        appearance_groupbox.layout().addWidget(self.digital_clock_checkbox)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(appearance_groupbox)

        self.read_settings()

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Handle hide event."""
        self.write_settings()
        super().hideEvent(event)

    def read_settings(self):
        """Read settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        if settings.contains('pos'):
            self.move(settings.value('pos'))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('pos', self.pos())

        settings.endGroup()
