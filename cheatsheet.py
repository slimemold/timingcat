#!/usr/bin/env python3

"""Cheat Sheet

This module implements the cheat sheet widget, which shows help information
such as keyboard shortcuts, etc.
"""

from PyQt5.QtCore import QSettings, Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QLabel, QLayout, QVBoxLayout, QWidget

class CheatSheet(QWidget):
    """Cheat sheet class.

    Just a widget that holds help information.
    """
    def __init__(self, parent=None):
        """Initialize the CheatSheet instance."""
        super().__init__(parent=parent)

        self.setWindowTitle('Help')
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.setLayout(QVBoxLayout())
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

        label = QLabel()
        label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        label.setText(
            'Window Toggling Shortcuts:\n' +
            self.shortcut_help_to_string(QKeySequence.HelpContents, 'Toggle help') +
            self.shortcut_help_to_string('CTRL+R', 'Toggle racer list') +
            self.shortcut_help_to_string('CTRL+F', 'Toggle field list') +
            self.shortcut_help_to_string('CTRL+L', 'Toggle log') +
            '\n' +
            'Results Window Shortcuts:\n' +
            self.shortcut_help_to_string('CTRL+S', 'Submit result(s)') +
            self.shortcut_help_to_string('CTRL+A', 'Select all results') +
            self.shortcut_help_to_string('CTRL+D', 'Deselect all results') +
            '\n' +
            'Miscellaneous:\n' +
            self.shortcut_help_to_string('CTRL+T', 'Toggle reference/wall time shown') +
            self.shortcut_help_to_string('CTRL+B', 'Launch race builder'))

        self.layout().addWidget(label)

        self.read_settings()

    def shortcut_help_to_string(self, shortcut, help_text):
        """Formats a shortcut string and help text."""
        return (QKeySequence.toString(QKeySequence(shortcut), QKeySequence.NativeText) +
                '\t' + help_text + '\n')

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

    # Signals.
    visibleChanged = pyqtSignal(bool)
