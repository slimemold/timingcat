#!/usr/bin/env python3

import csv
import os
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql  import *
from PyQt5.QtWidgets import *

CONST_INPUT_TEXT_POINT_SIZE = 32
CONST_RESULT_TABLE_POINT_SIZE = 20

class Models(QObject):
    def __init__(self, db):
        self.race = QSqlRelationalTableModel(db=db)
        self.race.setTable('Race')
        self.race.select()

        self.field = QSqlRelationalTableModel(db=db)
        self.field.setTable('Field')
        self.field.select()

        self.racer = QSqlRelationalTableModel(db=db)
        self.racer.setTable('Racer')
        self.racer.select()
        self.racer.setRelation(4, QSqlRelation('Field', 'id', 'name'));
        self.racer.setHeaderData(1, Qt.Horizontal, 'Bib')
        self.racer.setHeaderData(2, Qt.Horizontal, 'Name')
        self.racer.setHeaderData(3, Qt.Horizontal, 'Team')
        self.racer.setHeaderData(4, Qt.Horizontal, 'Field')
        self.racer.setHeaderData(5, Qt.Horizontal, 'Start')
        self.racer.setHeaderData(6, Qt.Horizontal, 'Finish')
        self.racer.select()

        self.result = QSqlRelationalTableModel(db=db)
        self.result.setTable('Result')
        self.result.setHeaderData(1, Qt.Horizontal, 'Bib')
        self.result.setHeaderData(2, Qt.Horizontal, 'Finish')
        self.result.select()

class RaceInfo(QTableView):
    def __init__(self, models):
        super().__init__()

        self.setModel(models.race)

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setVisible(False)

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
    def __init__(self, models):
        super().__init__()

        self.setModel(models.field)

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

    def setupProxyModel(self, db):
        # Use a proxy model so we can add some interesting columns.
        proxyModel = FieldProxyModel()
        proxyModel.setSourceModel(self.model())

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
    def __init__(self, models):
        super().__init__()

        self.setModel(models.racer)

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
    def dataChanged(self, topleft, bottomright, role):
        self.model().select()

class ResultTable(QTableView):
    def __init__(self, models):
        super().__init__()

        self.setModel(models.result)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            print(event.key())
        else:
            super().keyPressEvent(event)

class MainWidget(QWidget):
    def __init__(self, db):
        super().__init__()

        self.models = Models(db)

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
        self.result_table = ResultTable(self.models)

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
        self.race_info = RaceInfo(self.models)
        self.field_table = FieldTable(self.models)
        self.racer_table = RacerTable(self.models)

        # Signals/slots for button row toggle buttons.
        self.button_row.race_button.toggled.connect(self.race_info.setVisible)
        self.race_info.visibleChanged.connect(self.button_row.race_button.setChecked)
        self.button_row.field_button.toggled.connect(self.field_table.setVisible)
        self.field_table.visibleChanged.connect(self.button_row.field_button.setChecked)
        self.button_row.racer_button.toggled.connect(self.racer_table.setVisible)
        self.racer_table.visibleChanged.connect(self.button_row.racer_button.setChecked)

        # Signals/slots for result input.
        self.result_input.returnPressed.connect(self.newResult)

        # Signals/slots for field name change notification (need to update
        # racer models.
        self.field_table.model().dataChanged.connect(
            self.racer_table.dataChanged)

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

        self.newDatabase(dialog.selectedFiles()[0])

    def openFile(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Race file (*.rce)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return

        self.openDatabase(dialog.selectedFiles()[0])

    def importFilePrepare(self):
        # Pick the import file.
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Bikereg file (*.csv)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return

        import_filename = dialog.selectedFiles()[0]

        # If we are not yet initialized, pick a new race file.
        if not isinstance(self.centralWidget(), MainWidget):
            self.newFile()
        # Otherwise, if our current race has stuff in it, confirm to overwrite
        # before clearing it.
        else:
            # Get Field and Racer tables.
            field_model = self.centralWidget().field_table.model()
            racer_model = self.centralWidget().racer_table.model()

            if (field_model.rowCount() != 0) or (racer_model.rowCount() != 0):
                msg_box = QMessageBox()
                msg_box.setWindowTitle(self.APPLICATION_NAME)
                msg_box.setText('There are %s fields and %s racers defined.' %
                                (field_model.rowCount(), racer_model.rowCount()))
                msg_box.setInformativeText('Do you really want to overwrite this data?')
                msg_box.setStandardButtons(QMessageBox.Ok |
                                           QMessageBox.Cancel)
                msg_box.setDefaultButton(QMessageBox.Cancel)
                msg_box.setIcon(QMessageBox.Information)

                if msg_box.exec() != QMessageBox.Ok:
                    return

            db_filename = self.db_filename
            self.closeDatabase()
            self.newDatabase(db_filename)

        return import_filename

    def importBikeregFile(self):
        import_filename = self.importFilePrepare()

        with open(import_filename) as import_file:
            reader = csv.reader(import_file)

            # Skip the heading row.
            next(reader)

            for row in reader:
                _, bib, field, _, first_name, _, last_name, _, team, *_ = row
                name = first_name + ' ' + last_name

                # BikeReg lists One-day License holders twice, and the second
                # listing is missing the bib#, and instead has:
                # "License - 1/1/2018 - One-day License" as the field. Skip over
                # these entries.
                if 'One-day License' in field:
                    continue

                print('Importing %s' % name)

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
            '(key TEXT PRIMARY KEY,' +
             'value TEXT);'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'CREATE TABLE Field' +
            '(id INTEGER PRIMARY KEY,' +
             'name TEXT UNIQUE,' +
             'data TEXT);'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'CREATE TABLE Racer' +
            '(id INTEGER PRIMARY KEY,' +
             'bib INTEGER UNIQUE,' +
             'name TEXT,' +
             'team TEXT,' +
             'field_id INTEGER,' +
             'start TEXT,' +
             'finish TEXT,' +
             'data TEXT,' +
             'FOREIGN KEY(field_id) REFERENCES Field(id));'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'INSERT INTO Race VALUES("Race name", "(race name here)");'):
            raise Exception(query.lastError().text())

        self.db = db
        self.db_filename = filename

        self.setCentralWidget(MainWidget(db))
 
    def openDatabase(self, filename):
        db = QSqlDatabase.addDatabase('QSQLITE')
        if not db.isValid():
            raise Exception('Invalid database')

        db.setDatabaseName(filename)

        if not db.open():
            raise Exception(db.lastError().text())

        self.db = db
        self.db_filename = filename

        self.setCentralWidget(MainWidget(db))

    def closeDatabase(self):
        self.setCentralWidget(QWidget())

        self.db.close()
        print(self.db.connectionName())
        QSqlDatabase.removeDatabase(self.db.connectionName())

        self.db = None
        self.db_filename = None

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = SexyThymeMainWindow()
    main.show()

    sys.exit(app.exec_())
