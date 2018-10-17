#!/usr/bin/env python3

from datetime import datetime
import sys
from PyQt5.QtCore import pyqtSignal, Qt, QTime
import PyQt5.QtSql as QtSql
import PyQt5.QtWidgets as QtWidgets

def open_database(filename):
    database = QtSql.QSqlDatabase.addDatabase('QSQLITE')
    if not database.isValid():
        raise Exception('Invalid database')

    database.setDatabaseName(filename)

    if not database.open():
        raise Exception(database.lastError().text())

    return database

class RaceInfo(QtWidgets.QTableView):
    def __init__(self, db):
        super().__init__()

        self.setupModel()

        # Set up our view.
        self.setItemDelegate(QtSql.QSqlRelationalDelegate())
        self.horizontalHeader().setVisible(False)
        self.hideColumn(0) # id
        self.hideColumn(2) # data


    def setupModel(self):
        self.setModel(QtSql.QSqlRelationalTableModel(db=db))
        self.model().setTable('Race')
        self.model().select()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    # Signals.
    visibleChanged = pyqtSignal(bool)

    # Slots.
    def toggle(self, checked):
        if checked:
            self.show()
            self.view.show()
        else:
            self.hide()

    def closeEvent(self, event):
        self.visibleChanged.emit(False)

class FieldTable(QtWidgets.QTableView):
    def __init__(self, db):
        super().__init__()

        self.setupModel()

        self.setWindowTitle('Fields')

        # Set up our view.
        self.setItemDelegate(QtSql.QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder) # field
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.model().setHeaderData(1, Qt.Horizontal, 'Field')
        self.hideColumn(0) # id
        self.hideColumn(2) # data

    def setupModel(self):
        # Set up our model.
        self.setModel(QtSql.QSqlRelationalTableModel(db=db))
        self.model().setTable('Field')
        self.model().select()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    # Signals.
    visibleChanged = pyqtSignal(bool)

    # Slots.
    def toggle(self, checked):
        if checked:
            self.show()
        else:
            self.hide()

    def closeEvent(self, event):
        self.visibleChanged.emit(False)

class RacerTable(QtWidgets.QTableView):
    def __init__(self, db, field=None):
        super().__init__()

        self.setupModel(field)

        # Set up our view.
        self.setItemDelegate(QtSql.QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder) # bib
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(0) # id
        self.hideColumn(7) # data
        if self.model().field:
            self.hideColumn(4) # field

    def setupModel(self, field):
        # Set up our model.
        self.setModel(QtSql.QSqlRelationalTableModel(db=db))

        self.model().field = field
        if self.model().field:
            self.model().setFilter('name="Alexa Albert"')
            self.setWindowTitle('Racers (%s)' % (field))
        else:
            self.setWindowTitle('Racers')

        self.model().setTable('Racer')
        self.model().select()
        self.model().setRelation(4, QtSql.QSqlRelation('Field', 'id', 'name'));
        self.model().setHeaderData(1, Qt.Horizontal, 'Bib')
        self.model().setHeaderData(2, Qt.Horizontal, 'Name')
        self.model().setHeaderData(3, Qt.Horizontal, 'Team')
        self.model().setHeaderData(4, Qt.Horizontal, 'Field')
        self.model().setHeaderData(5, Qt.Horizontal, 'Start')
        self.model().setHeaderData(6, Qt.Horizontal, 'Finish')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    # Signals.
    visibleChanged = pyqtSignal(bool)

    # Slots.
    def toggle(self, checked):
        if checked:
            self.show()
        else:
            self.hide()

    def closeEvent(self, event):
        self.visibleChanged.emit(False)

    def dataChanged(self):
        self.model().select()

class ButtonDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QPushButton()
        print("Making pushbutton delegate")
        return editor

class ResultTable(QtWidgets.QTableView):
    def __init__(self, db):
        super().__init__()

        self.setupModel()

        self.setItemDelegate(QtSql.QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False) # Don't allow sorting.
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder) # finish
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(0) # id
        self.hideColumn(3) # data

        font = self.font()
        font.setPointSize(20)
        self.setFont(font)

    def setupModel(self):
        # Set up our model.
        self.setModel(QtSql.QSqlRelationalTableModel(db=db))
        self.model().setTable('Result')
        self.model().setHeaderData(1, Qt.Horizontal, 'Bib')
        self.model().setHeaderData(2, Qt.Horizontal, 'Finish')
        self.model().select()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            print(event.key())
        else:
            super().keyPressEvent(event)

class MainWidget(QtWidgets.QWidget):
    def __init__(self, db):
        super().__init__()

        # Top-level layout. Top to bottom.
        self.setLayout(QtWidgets.QVBoxLayout())

        # Button row for race info, field, racer list.
        self.button_row = QtWidgets.QWidget()
        self.button_row.setLayout(QtWidgets.QHBoxLayout())

        # Race Info, Fields, Racers
        self.button_row.race_button = QtWidgets.QPushButton('Race Info')
        self.button_row.race_button.setCheckable(True)
        self.button_row.field_button = QtWidgets.QPushButton('Fields')
        self.button_row.field_button.setCheckable(True)
        self.button_row.racer_button = QtWidgets.QPushButton('Racers')
        self.button_row.racer_button.setCheckable(True)

        # Add to button row.
        self.button_row.layout().addWidget(self.button_row.race_button)
        self.button_row.layout().addWidget(self.button_row.field_button)
        self.button_row.layout().addWidget(self.button_row.racer_button)

        # Result table.
        self.result_table = ResultTable(db)

        # Result line edit.
        self.result_input = QtWidgets.QLineEdit()
        self.result_input.setClearButtonEnabled(True)
        font = self.result_input.font()
        font.setPointSize(32)
        self.result_input.setFont(font)

        # Commit All button.
        self.commit_all_button = QtWidgets.QPushButton('Commit Selected')

        # Add to top-level layout.
        self.layout().addWidget(self.button_row)
        self.layout().addWidget(self.result_table)
        self.layout().addWidget(self.result_input)
        self.layout().addWidget(self.commit_all_button)

        # Floating windows. Keep then hidden initially.
        self.race_info = RaceInfo(db)
        self.field_table = FieldTable(db)
        self.racer_table = RacerTable(db)

        # Connect signals/slots.
        self.field_table.model().dataChanged.connect(
            self.racer_table.dataChanged)

        # Signals/slots for button row toggle buttons.
        self.button_row.race_button.toggled.connect(self.race_info.setVisible)
        self.race_info.visibleChanged.connect(self.button_row.race_button.setChecked)
        self.button_row.field_button.toggled.connect(self.field_table.setVisible)
        self.field_table.visibleChanged.connect(self.button_row.field_button.setChecked)
        self.button_row.racer_button.toggled.connect(self.racer_table.setVisible)
        self.racer_table.visibleChanged.connect(self.button_row.racer_button.setChecked)

        # Signals/slots for result input.
        self.result_input.returnPressed.connect(self.newResult)

    def newResult(self):
        model = self.result_table.model()
        index = self.result_table.model().rowCount()

        record = model.record()
        record.setValue('scratchpad', self.result_input.text())
        record.setValue('finish', QTime.currentTime())
        record.setValue('data', '{}')

        model.insertRecord(index, record)
        model.select()

        self.result_table.scrollToBottom()

        self.result_input.clear()

class SexyThymeMainWindow(QtWidgets.QMainWindow):
    APPLICATION_NAME = 'SexyThyme'

    def __init__(self, db):
        super().__init__()

        self.setWindowTitle(self.APPLICATION_NAME)
        self.setCentralWidget(MainWidget(db))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
 
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle(self.APPLICATION_NAME)
        msg_box.setText('You are about to leave %s.' % self.APPLICATION_NAME)
        msg_box.setInformativeText('Do you really want to quit?')
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok |
                                   QtWidgets.QMessageBox.Cancel)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)

        if msg_box.exec() == QtWidgets.QMessageBox.Ok:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    db = open_database('sbhc2018.rce')

    main = SexyThymeMainWindow(db)
    main.show()

    sys.exit(app.exec_())
