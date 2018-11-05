"""Preferences Qt Classes

This module implements a QDialog that can be used to set application preferences.
"""

from PyQt5.QtWidgets import QDialog

class PreferencesWindow(QDialog):
    """This dialog allows the user to set application preferences."""

    def __init__(self, modeldb, parent=None):
        """Initialize the PreferencesWindow instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.setWindowTitle('Preferences')
