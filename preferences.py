from PyQt5.QtWidgets import *

class PreferencesWindow(QDialog):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.setWindowTitle('Preferences')
