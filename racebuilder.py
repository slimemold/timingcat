from PyQt5.QtWidgets import *
from common import *
from racemodel import *

class RacerSetup(QWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

class FieldSetup(QWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

class RaceInfo(QWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

class Builder(QTabWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.setWindowTitle('Builder')

        racer_setup = RacerSetup(self.modeldb)
        field_setup = FieldSetup(self.modeldb)
        race_info = RaceInfo(self.modeldb)

        self.addTab(racer_setup, 'Racer Setup')
        self.addTab(field_setup, 'Field Setup')
        self.addTab(race_info, 'Race Info')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)

    def hideEvent(self, event):
        self.visibleChanged.emit(False)

    # Signals.
    visibleChanged = pyqtSignal(bool)
