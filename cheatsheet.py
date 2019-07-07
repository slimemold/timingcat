#!/usr/bin/env python3

"""Cheat Sheet

This module implements the cheat sheet widget, which shows help information
such as keyboard shortcuts, etc.
"""

import textwrap
from PyQt5.QtCore import QSettings, Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QLabel
import defaults

class CheatSheet(QLabel):
    """Cheat sheet class.

    Just a widget that holds help information.
    """
    def __init__(self, parent=None):
        """Initialize the CheatSheet instance."""
        super().__init__(parent=parent)

        self.setWindowTitle('Help')
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.setText(
            'Window Toggling Shortcuts:\n' +
            QKeySequence.toString(QKeySequence(QKeySequence.HelpContents)) + '\tToggle help\n' +
            QKeySequence.toString(QKeySequence('CTRL+R')) + '\tToggle racer list\n' +
            QKeySequence.toString(QKeySequence('CTRL+F')) + '\tToggle field list\n' +
            QKeySequence.toString(QKeySequence('CTRL+L')) + '\tToggle log\n' +
            '\n' +
            'Results Window Shortcuts:\n' +
            QKeySequence.toString(QKeySequence('CTRL+S')) + '\tSubmit result(s)\n' +
            QKeySequence.toString(QKeySequence('CTRL+A')) + '\tSelect all results\n' +
            QKeySequence.toString(QKeySequence('CTRL+D')) + '\tDeselect all results\n' +
            '\n' +
            'Miscellaneous:\n' +
            QKeySequence.toString(QKeySequence('CTRL+T')) + '\tToggle reference/wall time shown\n' +
            QKeySequence.toString(QKeySequence('CTRL+B')) + '\tLaunch race builder\n')

        self.read_settings()

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Handle hide event."""
        del event
        self.write_settings()
        self.visibleChanged.emit(False)

    def read_settings(self):
        """Read settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        self.resize(settings.value('size', defaults.CHEAT_SHEET_SIZE))

        if settings.contains('pos'):
            self.move(settings.value('pos'))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())

        settings.endGroup()

    # Signals.
    visibleChanged = pyqtSignal(bool)
