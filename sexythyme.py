#!/usr/bin/env python3

import argparse
import csv
import os
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql  import *
from PyQt5.QtWidgets import *

CONST_APPLICATION_NAME = 'SexyThyme'
CONST_INPUT_TEXT_POINT_SIZE = 32
CONST_RESULT_TABLE_POINT_SIZE = 20

class Model(QObject):
    def __init__(self, filename, new=False):
        super().__init__()

        self.filename = filename

        if new:
            # Delete the file, if it exists.
            if os.path.exists(self.filename):
                os.remove(self.filename)

        self.db = QSqlDatabase.addDatabase('QSQLITE', self.filename)

        if not self.db.isValid():
            raise Exception('Invalid database')

        self.db.setDatabaseName(filename)

        if not self.db.open():
            raise Exception(self.db.lastError().text())

        if new:
            self.createTables()

        self.setupModels()

    def cleanup(self):
        self.db.close()
        QSqlDatabase.removeDatabase(self.filename)

    def createTables(self):
        # Create tables.
        query = QSqlQuery(self.db)

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "race" ' +
            '("key" TEXT NOT NULL PRIMARY KEY, ' +
             '"value" TEXT NOT NULL);'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "field" ' +
            '("id" INTEGER NOT NULL PRIMARY KEY, ' +
             '"name" TEXT NOT NULL, ' +
             '"data" TEXT NOT NULL);'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "racer" ' +
            '("id" INTEGER NOT NULL PRIMARY KEY, ' +
             '"bib" INTEGER UNIQUE NOT NULL, ' +
             '"name" TEXT NOT NULL, ' +
             '"team" TEXT NOT NULL, ' +
             '"field_id" INTEGER, ' +
             '"start" TIME NOT NULL, ' +
             '"finish" TIME NOT NULL, ' +
             '"data" TEXT NOT NULL);'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "result" ' +
            '("id" INTEGER NOT NULL PRIMARY KEY, ' +
             '"scratchpad" TEXT NOT NULL, ' +
             '"finish" TIME NOT NULL, ' +
             '"data" TEXT NOT NULL);'):
            raise Exception(query.lastError().text())

        if not query.exec(
            'INSERT INTO Race VALUES("Race name", "(race name here)");'):
            raise Exception(query.lastError().text())

        query.finish()

    def setupModels(self):
        self.race = QSqlRelationalTableModel(db=self.db)
        self.race.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.race.setTable('race')
        if not self.race.select():
            raise Exception(self.race.lastError().text())

        self.field = QSqlRelationalTableModel(db=self.db)
        self.field.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.field.setTable('field')
        self.field.setHeaderData(self.field.fieldIndex('name'),
                                 Qt.Horizontal, 'Field')
        if not self.field.select():
            raise Exception(self.field.lastError().text())

        self.racer = QSqlRelationalTableModel(db=self.db)
        self.racer.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.racer.setTable('racer')
        self.racer.setHeaderData(self.racer.fieldIndex('bib'),
                                 Qt.Horizontal, 'Bib')
        self.racer.setHeaderData(self.racer.fieldIndex('name'),
                                 Qt.Horizontal, 'Name')
        self.racer.setHeaderData(self.racer.fieldIndex('team'),
                                 Qt.Horizontal, 'Team')
        self.racer.setHeaderData(self.racer.fieldIndex('field_id'),
                                 Qt.Horizontal, 'Field')
        self.racer.setHeaderData(self.racer.fieldIndex('start'),
                                 Qt.Horizontal, 'Start')
        self.racer.setHeaderData(self.racer.fieldIndex('finish'),
                                 Qt.Horizontal, 'Finish')
        # After this relation is defined, the field name becomes
        # "field_name_2".
        self.racer.setRelation(self.racer.fieldIndex('field_id'),
                               QSqlRelation('field', 'id', 'name'));
        if not self.racer.select():
            raise Exception(self.racer.lastError().text())

        self.result = QSqlRelationalTableModel(db=self.db)
        self.result.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.result.setTable('result')
        self.result.setHeaderData(self.result.fieldIndex('scratchpad'),
                                  Qt.Horizontal, 'Bib')
        self.result.setHeaderData(self.result.fieldIndex('finish'),
                                  Qt.Horizontal, 'Finish')
        if not self.result.select():
            raise Exception(self.result.lastError().text())

    def addRaceProperty(self, key, value):
        record = self.race.record()
        record.setValue('key', key)
        record.setValue('value', value)

        if not self.race.insertRecord(-1, record):
            raise Exception(self.race.lastError().text())
        if not self.race.select():
            raise Exception(self.race.lastError().text())

    def addField(self, name, data='{}'):
        record = self.field.record()
        record.setValue('name', name)
        record.setValue('data', data)

        if not self.field.insertRecord(-1, record):
            raise Exception(self.field.lastError().text())
        if not self.field.select():
            raise Exception(self.field.lastError().text())

    def addRacer(self, bib, name, team, field, start, finish, data='{}'):
        # See if the field exists in our Field table.  If not, we add a new
        # field.
        field_relation_model = self.racer.relationModel(
                                        self.racer.fieldIndex('field_name_2'))
        field_relation_model.setFilter('name = "%s"' % field)
        if not field_relation_model.select():
            raise Exception(field_relation_model.lastError().text())

        # Yup, not there. Add it, and then select it. Should just be the one
        # after adding.
        if field_relation_model.rowCount() == 0:
            self.addField(field)
            if not field_relation_model.select():
                raise Exception(field_relation_model.lastError().text())

        # Make sure there's only one, and get its field id.
        if field_relation_model.rowCount() != 1:
            raise Exception('More than one field with the same name found')
        field_id = (field_relation_model.record(0).field(field_relation_model
                                        .fieldIndex('id')).value())

        # Restore the filter. This model is actually owned by the racer model
        # that we got this from via relationModel(), and I guess it uses it
        # to populate the combobox. If we don't do this, the combobox will
        # only show the latest field added, which I guess makes sense.
        field_relation_model.setFilter('')

        record = self.racer.record()
        record.setValue('bib', bib)
        record.setValue('name', name)
        record.setValue('team', team)

        # OMFG I can't believe I have to do this...but Qt is not retranslating
        # this stupid field_name_2 alias back to its original field name,
        # so the database ends up getting the alias instead of the proper
        # one, failing the transaction. This piece of code switches the
        # field back from the field_name_2 alias to the original field_id,
        # so that the ensuing sql query can work.
        sql_field = record.field(self.racer.fieldIndex('field_name_2'))
        sql_field.setName('field_id')
        record.replace(self.racer.fieldIndex('field_name_2'), sql_field)
        record.setValue('field_id', field_id)

        record.setValue('start', start)
        record.setValue('finish', finish)
        record.setValue('data', data)

        if not self.racer.insertRecord(-1, record):
            raise Exception(self.racer.lastError().text())
        if not self.racer.submitAll():
            raise Exception(self.racer.lastError().text())
        if not self.racer.select():
            raise Exception(self.racer.lastError().text())

    def addResult(self, scratchpad, finish, data='{}'):
        record = self.result.record()
        record.setValue('scratchpad', scratchpad)
        record.setValue('finish', finish)
        record.setValue('data', data)

        self.result.insertRecord(-1, record)
        if not self.result.select():
            raise Exception(model.lastError().text())

class RaceInfo(QTableView):
    def __init__(self, race_model, parent=None):
        super().__init__(parent=parent)

        self.setModel(race_model)

        self.setWindowTitle('Race Info')

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
    def __init__(self, field_model, parent=None):
        super().__init__(parent=parent)

        self.setModel(field_model)

        self.setWindowTitle('Fields')

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(self.model().fieldIndex('name'),
                          Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex('id'))
        self.hideColumn(self.model().fieldIndex('data'))

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
    def __init__(self, racer_model, parent=None):
        super().__init__(parent=parent)

        self.setModel(racer_model)

        self.setWindowTitle('Racers')

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(self.model().fieldIndex('bib'),
                          Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex('id'))
        self.hideColumn(self.model().fieldIndex('data'))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.visibleChanged.emit(False)

    # Signals.
    visibleChanged = pyqtSignal(bool)

class ResultTable(QTableView):
    def __init__(self, result_model, parent=None):
        super().__init__(parent=parent)

        self.setModel(result_model)

        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False) # Don't allow sorting.
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(self.model().fieldIndex('id'),
                          Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex('id'))
        self.hideColumn(self.model().fieldIndex('data'))

        font = self.font()
        font.setPointSize(CONST_RESULT_TABLE_POINT_SIZE)
        self.setFont(font)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            print(event.key())
        else:
            super().keyPressEvent(event)

class CentralWidget(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def cleanup(self):
        pass

    def hasModel(self):
        return False

class MainWidget(QWidget, CentralWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent=parent)

        self.model = model

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
        self.result_table = ResultTable(self.model.result)

        # Result line edit.
        self.result_input = QLineEdit()
        self.result_input.setClearButtonEnabled(True)
        font = self.result_input.font()
        font.setPointSize(CONST_INPUT_TEXT_POINT_SIZE)
        self.result_input.setFont(font)

        # Commit button.
        self.commit_button = QPushButton('Commit Selected')

        # Add to top-level layout.
        self.layout().addWidget(self.button_row)
        self.layout().addWidget(self.result_table)
        self.layout().addWidget(self.result_input)
        self.layout().addWidget(self.commit_button)

        # Floating windows. Keep then hidden initially.
        self.race_info = RaceInfo(self.model.race)
        self.field_table = FieldTable(self.model.field)
        self.racer_table = RacerTable(self.model.racer)

        # Signals/slots for button row toggle buttons.
        self.button_row.race_button.toggled.connect(self.race_info
                                                        .setVisible)
        self.race_info.visibleChanged.connect(self.button_row.race_button
                                                  .setChecked)
        self.button_row.field_button.toggled.connect(self.field_table
                                                         .setVisible)
        self.field_table.visibleChanged.connect(self.button_row.field_button
                                                    .setChecked)
        self.button_row.racer_button.toggled.connect(self.racer_table
                                                         .setVisible)
        self.racer_table.visibleChanged.connect(self.button_row.racer_button
                                                    .setChecked)

        # Signals/slots for field name change notification.
        self.model.field.dataChanged.connect(self.fieldModelChanged)

        # Signals/slots for result input.
        self.result_input.returnPressed.connect(self.newResult)

        # Signals/slots for commit button.
        self.commit_button.clicked.connect(self.commitResults)

    def cleanup(self):
        self.model.cleanup()
        self.model = None

    def hasModel(self):
        return self.model is not None

    def fieldModelChanged(self, top_left, bottom_right, roles):
        # When someone changes a field name, we have to update the racer model
        # to get the field name change. In addition, there is a combo box
        # in the racer table view that is a view for a relation model inside
        # the racer model. That combo box needs to update as well, to get the
        # field name change.
        racer_model = self.model.racer
        field_relation_model = racer_model.relationModel(
                                        racer_model.fieldIndex('field_name_2'))

        racer_model.select()
        field_relation_model.select()

    def newResult(self):
        self.model.addResult(self.result_input.text(), QTime.currentTime())
        self.result_table.scrollToBottom()
        self.result_input.clear()

    def commitResults(self):
        print('commitResults')

class DummyWidget(QLabel, CentralWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setPixmap(QPixmap(os.path.join('resources', 'thyme.jpg')))

class SexyThymeMainWindow(QMainWindow):
    def __init__(self, filename=None, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle(CONST_APPLICATION_NAME)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.setupMenuBar()

        if filename:
            self.switchToMain(filename)
        else:
            self.switchToDummy()

    def switchToDummy(self):
        # Clean up old central widget, which will clean up the model we gave it.
        if self.centralWidget():
            self.centralWidget().cleanup()

        self.setCentralWidget(DummyWidget())

    def switchToMain(self, filename, new=False):
        # Clean up old central widget, which will clean up the model we gave it.
        if self.centralWidget():
            self.centralWidget().cleanup()

        # Make a new model, and give it to a new central widget.
        model = Model(filename, new)
        self.setCentralWidget(MainWidget(model))

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
        if (not self.centralWidget().hasModel() or
            (self.centralWidget().result_table.model().rowCount() == 0)):
            event.accept()
            QApplication.quit()
            return

        msg_box = QMessageBox()
        msg_box.setWindowTitle(CONST_APPLICATION_NAME)
        msg_box.setText('You have uncommitted results.')
        msg_box.setInformativeText('Do you really want to quit?')
        msg_box.setStandardButtons(QMessageBox.Ok |
                                   QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Cancel)
        msg_box.setIcon(QMessageBox.Information)

        if msg_box.exec() == QMessageBox.Ok:
            event.accept()
            QApplication.quit()
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
            return None

        filename = dialog.selectedFiles()[0]
        self.switchToMain(filename, True)

        return filename

    def openFile(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Race file (*.rce)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return None

        filename = dialog.selectedFiles()[0]
        self.switchToMain(filename, False)

        return filename

    def importFilePrepare(self):
        # Pick the import file.
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Bikereg file (*.csv)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return None

        import_filename = dialog.selectedFiles()[0]

        # If we are not yet initialized, pick a new race file.
        if not self.centralWidget().hasModel():
            if self.newFile():
                return import_filename
            else:
                return None

        # Otherwise, if our current race has stuff in it, confirm to overwrite
        # before clearing it.

        # Get Field and Racer tables so we can whine about how much state
        # we're going to lose if we let the import happen.
        field_model = self.centralWidget().field_table.model()
        racer_model = self.centralWidget().racer_table.model()

        if (field_model.rowCount() != 0) or (racer_model.rowCount() != 0):
            msg_box = QMessageBox()
            msg_box.setWindowTitle(CONST_APPLICATION_NAME)
            msg_box.setText('There are %s fields and %s racers defined.' %
                            (field_model.rowCount(), racer_model.rowCount()))
            msg_box.setInformativeText('Do you really want to overwrite ' +
                                       'this data?')
            msg_box.setStandardButtons(QMessageBox.Ok |
                                       QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Cancel)
            msg_box.setIcon(QMessageBox.Information)

            if msg_box.exec() != QMessageBox.Ok:
                return None

        # Reuse old filename.
        filename = self.centralWidget().model.filename
        self.switchToMain(filename, True)

        return import_filename

    def importBikeregFile(self):
        import_filename = self.importFilePrepare()

        if not import_filename:
            return

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

                self.centralWidget().model.addRacer(bib, name, team, field,
                                 QTime.currentTime(), QTime.currentTime())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=CONST_APPLICATION_NAME)
    parser.add_argument('racefile', nargs='?', help='Optional racefile to load')
    args = parser.parse_args()

    app = QApplication(sys.argv)

    main = SexyThymeMainWindow(filename=args.racefile)
    main.show()

    sys.exit(app.exec_())
