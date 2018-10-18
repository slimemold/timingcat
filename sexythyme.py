#!/usr/bin/env python3

from datetime import datetime
import os
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql  import *
from PyQt5.QtWidgets import *

CONST_INPUT_TEXT_POINT_SIZE = 32
CONST_RESULT_TABLE_POINT_SIZE = 20

class RaceInfo(QTableView):
    def __init__(self, db):
        super().__init__()

        self.setupModel(db)

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.horizontalHeader().setVisible(False)
        self.hideColumn(0) # id
        self.hideColumn(2) # data

    def setupModel(self, db):
        self.setModel(QSqlRelationalTableModel(db=db))
        self.model().setTable('Race')
        self.model().select()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.visibleChanged.emit(False)

    # Signals.
    visibleChanged = pyqtSignal(bool)

class FieldProxyModel(QSortFilterProxyModel):
    def columnCount(self, parent):
        return self.sourceModel().columnCount(parent) + 2

class FieldTable(QTableView):
    def __init__(self, db):
        super().__init__()

        self.setupModel(db)

        self.setWindowTitle('Fields')

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder) # field
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(0) # id
        self.hideColumn(2) # data

    def setupModel(self, db):
        model = QSqlRelationalTableModel(db=db)
        model.setTable('Field')
        model.select()

        # Use a proxy model so we can add some interesting columns.
        proxyModel = FieldProxyModel()
        proxyModel.setSourceModel(model)

        self.setModel(proxyModel)

        self.model().setHeaderData(1, Qt.Horizontal, 'Field')
        self.model().setHeaderData(2, Qt.Horizontal, 'Finished')
        self.model().setHeaderData(3, Qt.Horizontal, 'Total')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.visibleChanged.emit(False)

    # Signals.
    visibleChanged = pyqtSignal(bool)

class RacerTable(QTableView):
    def __init__(self, db, field=None):
        super().__init__()

        self.setupModel(db, field)

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder) # bib
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(0) # id
        self.hideColumn(7) # data

    def setupModel(self, db, field):
        self.setModel(QSqlRelationalTableModel(db=db))

        self.field = field
        if self.field:
            self.model().setFilter('name="Alexa Albert"')
            self.setWindowTitle('Racers (%s)' % (field))
        else:
            self.setWindowTitle('Racers')

        self.model().setTable('Racer')
        self.model().select()
        self.model().setRelation(4, QSqlRelation('Field', 'id', 'name'));
        self.model().setHeaderData(1, Qt.Horizontal, 'Bib')
        self.model().setHeaderData(2, Qt.Horizontal, 'Name')
        self.model().setHeaderData(3, Qt.Horizontal, 'Team')
        self.model().setHeaderData(4, Qt.Horizontal, 'Field')
        self.model().setHeaderData(5, Qt.Horizontal, 'Start')
        self.model().setHeaderData(6, Qt.Horizontal, 'Finish')

        if self.field:
            self.hideColumn(4) # field
        else:
            self.showColumn(4)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.visibleChanged.emit(False)

    # Signals.
    visibleChanged = pyqtSignal(bool)

    # Slots.
    def dataChanged(self):
        self.model().select()

class ResultTable(QTableView):
    def __init__(self, db):
        super().__init__()

        self.setupModel(db)

        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False) # Don't allow sorting.
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder) # finish
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(0) # id
        self.hideColumn(3) # data

        font = self.font()
        font.setPointSize(CONST_RESULT_TABLE_POINT_SIZE)
        self.setFont(font)

    def setupModel(self, db):
        self.setModel(QSqlRelationalTableModel(db=db))
        self.model().setTable('Result')
        self.model().setHeaderData(1, Qt.Horizontal, 'Bib')
        self.model().setHeaderData(2, Qt.Horizontal, 'Finish')
        self.model().select()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            print(event.key())
        else:
            super().keyPressEvent(event)

class MainWidget(QWidget):
    def __init__(self, db):
        super().__init__()

        # Top-level layout. Top to bottom.
        self.setLayout(QVBoxLayout())

        # Button row for race info, field, racer list.
        self.button_row = QWidget()
        self.button_row.setLayout(QHBoxLayout())

        # Race Info, Fields, Racers
        self.button_row.race_button = QPushButton('Race Info')
        self.button_row.race_button.setCheckable(True)
        self.button_row.field_button = QPushButton('Fields')
        self.button_row.field_button.setCheckable(True)
        self.button_row.racer_button = QPushButton('Racers')
        self.button_row.racer_button.setCheckable(True)

        # Add to button row.
        self.button_row.layout().addWidget(self.button_row.race_button)
        self.button_row.layout().addWidget(self.button_row.field_button)
        self.button_row.layout().addWidget(self.button_row.racer_button)

        # Result table.
        self.result_table = ResultTable(db)

        # Result line edit.
        self.result_input = QLineEdit()
        self.result_input.setClearButtonEnabled(True)
        font = self.result_input.font()
        font.setPointSize(CONST_INPUT_TEXT_POINT_SIZE)
        self.result_input.setFont(font)

        # Commit All button.
        self.commit_all_button = QPushButton('Commit Selected')

        # Add to top-level layout.
        self.layout().addWidget(self.button_row)
        self.layout().addWidget(self.result_table)
        self.layout().addWidget(self.result_input)
        self.layout().addWidget(self.commit_all_button)

        # Floating windows. Keep then hidden initially.
        self.race_info = RaceInfo(db)
        self.field_table = FieldTable(db)
        self.racer_table = RacerTable(db)

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

    def setupModel(self, db):
        self.centralWidget().setEnabled(True)

        # Connect signals/slots.
        self.field_table.model().dataChanged.connect(
            self.racer_table.dataChanged)

class SexyThymeMainWindow(QMainWindow):
    APPLICATION_NAME = 'SexyThyme'

    def __init__(self):
        super().__init__()

        self.setWindowTitle(self.APPLICATION_NAME)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setCentralWidget(QWidget())

        self.setupMenuBar()

    def setupMenuBar(self):
        self.menuBar().setNativeMenuBar(False)
        fileMenu = self.menuBar().addMenu('&File');
        fileMenu.addAction('New...', self.newFile, QKeySequence.New)
        fileMenu.addAction('Open...', self.openFile, QKeySequence.Open)
        fileMenu.addSeparator()
        fileMenu.addAction('Import Bikereg csv', self.importBikeregFile)
        fileMenu.addSeparator()
        fileMenu.addAction('Quit', self.close, QKeySequence.Quit)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if (not isinstance(self.centralWidget(), MainWidget) or
            (self.centralWidget().result_table.model().rowCount() == 0)):
            event.accept()
            return

        msg_box = QMessageBox()
        msg_box.setWindowTitle(self.APPLICATION_NAME)
        msg_box.setText('You have uncommitted results.')
        msg_box.setInformativeText('Do you really want to quit?')
        msg_box.setStandardButtons(QMessageBox.Ok |
                                   QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Cancel)
        msg_box.setIcon(QMessageBox.Information)

        if msg_box.exec() == QMessageBox.Ok:
            event.accept()
        else:
            event.ignore()

    def newFile(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('rce')
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setLabelText(QFileDialog.Accept, 'New')
        dialog.setNameFilter('Race file (*.rce)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return

        db = self.newDatabase(dialog.selectedFiles()[0])
        self.setCentralWidget(MainWidget(db))

    def openFile(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Race file (*.rce)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return

        db = self.openDatabase(dialog.selectedFiles()[0])
        self.setCentralWidget(MainWidget(db))

    def importBikeregFile(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Bikereg file (*.csv)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return

        filename = dialog.selectedFiles()[0]
        print('Import bikereg csv file ' + filename)

    def newDatabase(self, filename):
        # Delete the file, if it exists.
        if os.path.exists(filename):
            os.remove(filename)

        db = QSqlDatabase.addDatabase('QSQLITE')
        if not db.isValid():
            raise Exception('Invalid database')

        db.setDatabaseName(filename)

        if not db.open():
            raise Exception(db.lastError().text())

        # Create tables.
        query = QSqlQuery(db)

        if not query.exec(
            'PRAGMA foreign_keys = ON;'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'CREATE TABLE Race' +
            '(id INTEGER PRIMARY KEY,' +
             'name VARCHAR,' +
             'data TEXT);'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'CREATE TABLE Field' +
            '(id INTEGER PRIMARY KEY,' +
             'name VARCHAR UNIQUE,' +
             'data TEXT);'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'CREATE TABLE Racer' +
            '(id INTEGER PRIMARY KEY,' +
             'bib INTEGER UNIQUE,' +
             'name VARCHAR,' +
             'team VARCHAR,' +
             'field_id INTEGER,' +
             'start TEXT,' +
             'finish TEXT,' +
             'data TEXT,' +
             'FOREIGN KEY(field_id) REFERENCES Field(id));'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'INSERT INTO Race VALUES(0, "(race name here)", "{}");'):
            raise Exception(query.lastError().text())

        return db
 
    def openDatabase(self, filename):
        db = QSqlDatabase.addDatabase('QSQLITE')
        if not db.isValid():
            raise Exception('Invalid database')

        db.setDatabaseName(filename)

        if not db.open():
            raise Exception(db.lastError().text())

        return db

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = SexyThymeMainWindow()
    main.show()

    sys.exit(app.exec_())
