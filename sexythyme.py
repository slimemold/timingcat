#!/usr/bin/env python3

import logging
import sys
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtSql import QSqlDatabase, QSqlRelation, QSqlRelationalDelegate, QSqlRelationalTableModel, QSqlTableModel
import PyQt5.QtWidgets as QtWidgets

def open_database(filename):
    database = QSqlDatabase.addDatabase('QSQLITE')
    if not database.isValid():
        raise Exception('Invalid database')

    database.setDatabaseName(filename)

    if not database.open():
        raise Exception(database.lastError().text())

    return database

class FieldTable(QtWidgets.QTableView):
    def __init__(self, db):
        super().__init__()

        self.setWindowTitle('Fields')

        # Set up our model.
        self.setModel(QSqlRelationalTableModel(db=db))
        #self.model().setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model().setTable('Field')
        self.model().select()

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setSortingEnabled(True) # Allow sorting by column
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder) # field
        self.verticalHeader().setVisible(False)
        self.model().setHeaderData(1, Qt.Horizontal, 'Field')
        self.hideColumn(0) # id
        self.hideColumn(2) # data

class RacerTable(QtWidgets.QTableView):
    def __init__(self, db, field=None):
        super().__init__()

        # Set up our model.
        self.setModel(QSqlRelationalTableModel(db=db))
        #self.model().setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.model().field = field
        if self.model().field:
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

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setSortingEnabled(True) # Allow sorting by column
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder) # bib
        self.verticalHeader().setVisible(False)
        self.hideColumn(0) # id
        self.hideColumn(7) # data
        if self.model().field:
            self.hideColumn(4) # field

    def foreignKeyChange(self):
        self.model().select()

class ButtonDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QPushButton()
        return editor

class ResultTable(QtWidgets.QTableView):
    def __init__(self, db):
        super().__init__()

        self.setWindowTitle('Results Scratchpad')

        # Set up our model.
        self.setModel(QSqlRelationalTableModel(db=db))
        self.model().setTable('Result')
        self.model().select()
        self.model().dataChanged.connect(self.dataChanged)

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setSortingEnabled(True) # Allow sorting by column
        self.sortByColumn(2, Qt.SortOrder.AscendingOrder) # finish
        self.verticalHeader().setVisible(False)
        self.model().setHeaderData(1, Qt.Horizontal, 'Bib')
        self.model().setHeaderData(2, Qt.Horizontal, 'Finish')
        self.model().setHeaderData(4, Qt.Horizontal, 'Commit')
        self.hideColumn(0) # id
        self.hideColumn(3) # data

        # Set up our commit buttons.
        self.setItemDelegateForColumn(4, ButtonDelegate(self))

    def dataChanged(self):
        print("dataChanged")
        self.model().select()

class MainWidget(QtWidgets.QWidget):
    def __init__(self, db):
        super().__init__()

        self.setLayout(QtWidgets.QVBoxLayout())
        self.result_table_view = ResultTable(db)
        self.layout().addWidget(self.result_table_view)
        self.result_line_edit = QtWidgets.QLineEdit()
        self.layout().addWidget(self.result_line_edit)

        buttons = QtWidgets.QWidget()
        self.layout().addWidget(buttons)
        buttons.setLayout(QtWidgets.QHBoxLayout())
        buttons.layout().addWidget(QtWidgets.QPushButton("Commit All"))

class SexyThymeMainWindow(QtWidgets.QMainWindow):
    def __init__(self, db):
        super().__init__()

        self.setWindowTitle('SexyThyme')
        self.setCentralWidget(MainWidget(db))
 
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    db = open_database('sbhc2018.rce')

    main = SexyThymeMainWindow(db)
    main.show()

    field_table = FieldTable(db)
    field_table.show()

    racer_table = RacerTable(db)
    racer_table.show()

    # Connect signals/slots.
    field_table.model().dataChanged.connect(racer_table.foreignKeyChange)

    sys.exit(app.exec_())
