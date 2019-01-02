#!/usr/bin/env python3

"""Preferences Qt Classes

This module implements a QDialog that can be used to set application preferences.
"""

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QCheckBox, QGroupBox, QWidget
from PyQt5.QtWidgets import QVBoxLayout
import common
import defaults

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
__author__ = common.AUTHOR
__credits__ = common.CREDITS
__license__ = common.LICENSE
__version__ = common.VERSION
__maintainer__ = common.MAINTAINER
__email__ = common.EMAIL
__status__ = common.STATUS

class PreferencesWindow(QWidget):
    """This dialog allows the user to set application preferences."""

    # QSettings keys.
    ALWAYS_ON_TOP = 'always_on_top'
    DIGITAL_CLOCK = 'digital_clock'
    WALL_TIMES = 'wall_times'

    def __init__(self, parent=None):
        """Initialize the PreferencesWindow instance."""
        super().__init__(parent=parent)

        self.setWindowTitle('Preferences')

        # Window Appearance and Behavior preferences.
        self.always_on_top_checkbox = QCheckBox('Main Window Always On Top')
        self.always_on_top_checkbox.setTristate(False)
        self.digital_clock_checkbox = QCheckBox('LCD clock')
        self.digital_clock_checkbox.setTristate(False)

        appearance_groupbox = QGroupBox('Window Appearance and Behavior')
        appearance_groupbox.setLayout(QVBoxLayout())
        appearance_groupbox.layout().addWidget(self.always_on_top_checkbox)
        appearance_groupbox.layout().addWidget(self.digital_clock_checkbox)

        # Clock display.
        self.wall_times_checkbox = QCheckBox('Show Wall Times')
        self.wall_times_checkbox.setTristate(False)

        clock_groupbox = QGroupBox('Clock Display')
        clock_groupbox.setLayout(QVBoxLayout())
        clock_groupbox.layout().addWidget(self.wall_times_checkbox)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(appearance_groupbox)
        self.layout().addWidget(clock_groupbox)

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

        self.always_on_top_checkbox.setCheckState(int(settings.value(self.ALWAYS_ON_TOP,
                                                                     defaults.ALWAYS_ON_TOP)))

        self.digital_clock_checkbox.setCheckState(int(settings.value(self.DIGITAL_CLOCK,
                                                                     defaults.DIGITAL_CLOCK)))

        self.wall_times_checkbox.setCheckState(int(settings.value(self.WALL_TIMES,
                                                                  defaults.WALL_TIMES)))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('pos', self.pos())

        settings.setValue(self.ALWAYS_ON_TOP, self.always_on_top_checkbox.checkState())

        settings.setValue(self.DIGITAL_CLOCK, self.digital_clock_checkbox.checkState())

        settings.setValue(self.WALL_TIMES, self.wall_times_checkbox.checkState())

        settings.endGroup()
