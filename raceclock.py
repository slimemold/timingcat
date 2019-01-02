#!/usr/bin/env python3

"""Race Clock Classes

This module implements the digital clock used to display current race time.
Upon instantiation, we also validate that the current system time is in sync
with Internet (cellphone) time.
"""

from PyQt5.QtCore import QDate, QDateTime, QTime, QTimer
from PyQt5.QtWidgets import QFrame, QLCDNumber
import common

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

class DigitalClock(QLCDNumber):
    """Old-fashioned 7-segment display digital clock showing current time."""
    def __init__(self, modeldb, parent=None):
        """Initialize the DigitalClock instance."""
        super().__init__(8, parent=parent)

        self.modeldb = modeldb
        self.preferences = None

        self.setFrameShape(QFrame.NoFrame)
        self.setSegmentStyle(QLCDNumber.Filled)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.update()
        self.timer.start(100)

        self.setMinimumHeight(48)

    def update(self):
        """Update text on the LCD display."""
        race_table_model = self.modeldb.race_table_model

        if self.preferences and self.preferences.wall_times_checkbox.isChecked():
            msecs = race_table_model.get_wall_time_msecs()
        else:
            msecs = race_table_model.get_reference_msecs()
        datetime = QDateTime(QDate(1, 1, 1), QTime(0, 0)).addMSecs(msecs)

        if datetime.time().second() % 2:
            text = datetime.toString('hh:mm ss')
        else:
            text = datetime.toString('hh:mm:ss')

        self.display(text)
