import os
from PyQt5.QtCore import *
from PyQt5.QtSql  import *
from common import *
import defaults

class DatabaseError(Exception):
    pass

class InternalModelError(Exception):
    pass

class InputError(Exception):
    pass

def _printRecord(record):
    for index in range(record.count()):
        print('%s: %s, generated = %s' % (record.field(index).name(),
                                          record.field(index).value(),
                                          record.isGenerated(index)))

class ModelDatabase(QObject):
    def __init__(self, filename, new=False):
        super().__init__()

        self.filename = filename

        if new:
            # Delete the file, if it exists.
            if os.path.exists(self.filename):
                os.remove(self.filename)

        self.db = QSqlDatabase.addDatabase('QSQLITE', self.filename)

        if not self.db.isValid():
            raise DatabaseError('Invalid database')

        self.db.setDatabaseName(filename)

        if not self.db.open():
            raise DatabaseError(self.db.lastError().text())

        self.race_table_model = RaceTableModel(self, new)
        self.field_table_model = FieldTableModel(self, new)
        self.racer_table_model = RacerTableModel(self, new)
        self.result_table_model = ResultTableModel(self, new)

    def cleanup(self):
        self.db.close()
        QSqlDatabase.removeDatabase(self.filename)

    def addDefaults(self):
        self.race_table_model.addDefaults()
        self.field_table_model.addDefaults()
        self.racer_table_model.addDefaults()
        self.result_table_model.addDefaults()

class TableModel(QSqlRelationalTableModel):
    def __init__(self, modeldb):
        super().__init__(db=modeldb.db)

        self.modeldb = modeldb
        self.column_flags_to_add = {}
        self.column_flags_to_remove = {}

    def createTable(self):
        raise NotImplementedError

    def addDefaults(self):
        pass

    def addColumnFlags(self, column, flags):
        if not column in self.column_flags_to_add.keys():
            self.column_flags_to_add[column] = 0
        self.column_flags_to_add[column] |= int(flags)

    def removeColumnFlags(self, column, flags):
        if not column in self.column_flags_to_remove.keys():
            self.column_flags_to_remove[column] = 0
        self.column_flags_to_remove[column] |= int(flags)

    def flags(self, model_index):
        flags = super().flags(model_index)

        column = model_index.column()

        if not column in self.column_flags_to_add.keys():
            self.column_flags_to_add[column] = 0
        flags |= self.column_flags_to_add[column]

        if not column in self.column_flags_to_remove.keys():
            self.column_flags_to_remove[column] = 0
        flags &= ~self.column_flags_to_remove[model_index.column()]

        return flags

class RaceTableModel(TableModel):
    TABLE = 'race'
    ID = 'id'
    KEY = 'key'
    VALUE = 'value'

    # Race keys
    NAME = 'name'
    DATE = 'date'
    NOTES = 'notes'

    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable(new)

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable(self.TABLE)
        if not self.select():
            raise DatabaseError(self.lastError().text())

        self.removeColumnFlags(0, Qt.ItemIsEditable | Qt.ItemIsSelectable)

    def createTable(self, new):
        query = QSqlQuery(self.database())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "%s" ' % self.TABLE +
            '("%s" INTEGER NOT NULL PRIMARY KEY, ' % self.ID +
             '"%s" TEXT NOT NULL, ' % self.KEY +
             '"%s" TEXT NOT NULL);' % self.VALUE):
            raise DatabaseError(query.lastError().text())

        query.finish()

    def addDefaults(self):
        if not self.getRaceProperty(self.NAME):
            self.addRaceProperty(self.NAME, defaults.RACE_NAME)

        if not self.getRaceProperty(self.DATE):
            self.addRaceProperty(self.DATE, QDateTime.currentDateTime().date().toString())

        if not self.getRaceProperty(self.NOTES):
            self.addRaceProperty(self.NOTES, '')

    def addRaceProperty(self, key, value):
        record = self.record()
        record.setGenerated(self.ID, False)
        record.setValue(self.KEY, key)
        record.setValue(self.VALUE, value)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def deleteRaceProperty(self, key):
        index_list = self.match(self.index(0, self.fieldIndex(self.KEY)),
                                Qt.DisplayRole, key, 1, Qt.MatchExactly)

        if not index_list:
            raise InputError('Failed to find race property with KEY %s' % key)

        index = index_list[0]

        if not self.removeRow(index.row()):
            raise DatabaseError(self.lastError().text())

    def getRaceProperty(self, key):
        index_list = self.match(self.index(0, self.fieldIndex(self.KEY)),
                                Qt.DisplayRole, key, 1, Qt.MatchExactly)

        if not index_list:
            return None

        index = index_list[0]

        return self.data(self.index(index.row(), self.fieldIndex(self.VALUE)))

    def setRaceProperty(self, key, value):
        index_list = self.match(self.index(0, self.fieldIndex(self.KEY)),
                                Qt.DisplayRole, key, 1, Qt.MatchExactly)

        if not index_list:
            raise InputError('Failed to find race property with KEY %s' % key)

        index = index_list[0]
        self.setData(self.index(index.row(), self.fieldIndex(self.VALUE)), value)

class FieldTableModel(TableModel):
    TABLE = 'field'
    ID = 'id'
    NAME = 'name'

    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable(new)

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable(self.TABLE)
        self.setHeaderData(self.fieldIndex(self.NAME), Qt.Horizontal, 'Field')
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def createTable(self, new):
        query = QSqlQuery(self.database())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "%s" ' % self.TABLE +
            '("%s" INTEGER NOT NULL PRIMARY KEY, ' % self.ID +
             '"%s" TEXT UNIQUE NOT NULL);' % self.NAME):
            raise DatabaseError(query.lastError().text())

        query.finish()

    def addDefaults(self):
        if self.rowCount() == 0:
            self.addField(defaults.FIELD_NAME)

    def nameFromId(self, field_id):
        index_list = self.match(self.index(0, self.fieldIndex(self.ID)),
                                Qt.DisplayRole, field_id, 1, Qt.MatchExactly)

        if not index_list:
            return None

        index = index_list[0]

        return self.data(self.index(index.row(), self.fieldIndex(self.NAME)))

    def idFromName(self, name):
        index_list = self.match(self.index(0, self.fieldIndex(self.NAME)),
                                Qt.DisplayRole, name, 1, Qt.MatchExactly)

        if not index_list:
            return None

        index = index_list[0]

        return self.data(self.index(index.row(), self.fieldIndex(self.ID)))

    def addField(self, name):
        if name == '':
            raise InputError('Field name "%s" is invalid' % name)

        record = self.record()
        record.setGenerated(self.ID, False)
        record.setValue(FieldTableModel.NAME, name)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def deleteField(self, name):
        index_list = self.match(self.index(0, self.fieldIndex(self.NAME)),
                                Qt.DisplayRole, name, 1, Qt.MatchExactly)

        if not index_list:
            raise InputError('Failed to find field with NAME %s' % name)

        index = index_list[0]

        if not self.removeRow(index.row()):
            raise DatabaseError(self.lastError().text())

class RacerTableModel(TableModel):
    TABLE = 'racer'
    ID = 'id'
    BIB = 'bib'
    FIRST_NAME = 'first_name'
    LAST_NAME = 'last_name'
    TEAM = 'team'
    FIELD = 'field_id'
    FIELD_ALIAS = 'name'
    START = 'start'
    FINISH = 'finish'
    STATUS = 'status'

    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable()

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable(self.TABLE)
        self.setHeaderData(self.fieldIndex(self.BIB), Qt.Horizontal, 'Bib')
        self.setHeaderData(self.fieldIndex(self.FIRST_NAME), Qt.Horizontal, 'First Name')
        self.setHeaderData(self.fieldIndex(self.LAST_NAME), Qt.Horizontal, 'Last Name')
        self.setHeaderData(self.fieldIndex(self.TEAM), Qt.Horizontal, 'Team')
        self.setHeaderData(self.fieldIndex(self.FIELD), Qt.Horizontal, 'Field')
        self.setHeaderData(self.fieldIndex(self.START), Qt.Horizontal, 'Start')
        self.setHeaderData(self.fieldIndex(self.FINISH), Qt.Horizontal, 'Finish')
        self.setHeaderData(self.fieldIndex(self.STATUS), Qt.Horizontal, 'Status')

        # After this relation is defined, the field name becomes
        # "field_name_2" (FIELD_ALIAS).
        self.setRelation(self.fieldIndex(self.FIELD),
            QSqlRelation(FieldTableModel.TABLE,
                         FieldTableModel.ID,
                         FieldTableModel.NAME))
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def createTable(self):
        query = QSqlQuery(self.database())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "%s" ' % self.TABLE +
            '("%s" INTEGER NOT NULL PRIMARY KEY, ' % self.ID +
             '"%s" INTEGER UNIQUE NOT NULL, ' % self.BIB +
             '"%s" TEXT NOT NULL, ' % self.FIRST_NAME +
             '"%s" TEXT NOT NULL, ' % self.LAST_NAME +
             '"%s" TEXT NOT NULL, ' % self.TEAM +
             '"%s" INTEGER NOT NULL, ' % self.FIELD +
             '"%s" TIME, ' % self.START +
             '"%s" TIME, ' % self.FINISH +
             '"%s" TEXT NOT NULL);' % self.STATUS):
            raise DatabaseError(query.lastError().text())

        query.finish()

    def addRacer(self, bib, first_name, last_name, team, field,
                 start=QTime(), finish=QTime(), status='local'):
        # Do some validation.
        #
        # Don't have to check for None, because that would fail the
        # NOT NULL table constraint.
        #
        # Also, default QTime constructor makes an invalid time that ends up
        # being stored as NULL in the table, which is what we want.
        if not bib.isdigit():
            raise InputError('Racer bib "%s" is invalid' % bib)

        if first_name == '':
            raise InputError('Racer first name "%s" is invalid' % first_name)

        if last_name == '':
            raise InputError('Racer last name "%s" is invalid' % last_name)

        # See if the field exists in our Field table.  If not, we add a new
        # field.
        field_id = self.modeldb.field_table_model.idFromName(field)
        if not field_id:
            self.modeldb.field_table_model.addField(field)
            field_id = self.modeldb.field_table_model.idFromName(field)

        if field_id is None:
            raise InputError('Racer field "%S" is invalid' % field)

        record = self.record()
        record.setGenerated(self.ID, False)
        record.setValue(self.BIB, bib)
        record.setValue(self.FIRST_NAME, first_name)
        record.setValue(self.LAST_NAME, last_name)
        record.setValue(self.TEAM, team)

        # OMFG I can't believe I have to do this...but Qt is not retranslating
        # this stupid field_name_2 alias back to its original field name,
        # so the database ends up getting the alias instead of the proper
        # one, failing the transaction. This piece of code switches the
        # field back from the field_name_2 alias to the original field_id,
        # so that the ensuing sql query can work.
        sql_field = record.field(self.fieldIndex(self.FIELD_ALIAS))
        sql_field.setName(self.FIELD)
        record.replace(self.fieldIndex(self.FIELD_ALIAS), sql_field)
        record.setValue(self.FIELD, field_id)

        record.setValue(self.START, start)
        record.setValue(self.FINISH, finish)
        record.setValue(self.STATUS, status)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def deleteRacer(self, bib):
        index_list = self.match(self.index(0, self.fieldIndex(self.BIB)),
                                Qt.DisplayRole, bib, 1, Qt.MatchExactly)

        if not index_list:
            raise InputError('Failed to find racer with BIB %s' % bib)

        index = index_list[0]

        if not self.removeRow(index.row()):
            raise DatabaseError(self.lastError().text())

    def setRacerStart(self, bib, start):
        index_list = self.match(self.index(0, self.fieldIndex(self.BIB)),
                                Qt.DisplayRole, bib, 1, Qt.MatchExactly)

        if not index_list:
            raise InputError('Failed to find racer with bib %s' % bib)

        index = self.index(index_list[0].row(), self.fieldIndex(self.START))
        self.setData(index, start)
        self.dataChanged.emit(index, index)

    def setRacerFinish(self, bib, finish):
        index_list = self.match(self.index(0, self.fieldIndex(self.BIB)),
                                Qt.DisplayRole, bib, 1, Qt.MatchExactly)

        if not index_list:
            raise InputError('Failed to find racer with bib %s' % bib)

        index = self.index(index_list[0].row(), self.fieldIndex(self.FINISH))
        self.setData(index, finish)
        self.dataChanged.emit(index, index)

    def assignStartTimes(self, field_name, start, interval, dry_run=False):
        if field_name and not self.modeldb.field_table_model.idFromName(field_name):
            raise InputError('Invalid field "%s"' % field_name)

        if not isinstance(start, QTime):
            raise InputError('Invalid start data type "%s"' % type(start))

        if not start.isValid():
            raise InputError('Invalid QTime start')

        racer_table_model = self.modeldb.racer_table_model
        starts_overwritten = 0

        for row in range(racer_table_model.rowCount()):
            if field_name:
                field_index = self.index(row, self.fieldIndex(self.FIELD_ALIAS))
                if not field_name == self.data(field_index):
                    continue

            start_index = self.index(row, self.fieldIndex(self.START))
            if not dry_run:
                self.setData(start_index, start)
            elif self.data(start_index):
                starts_overwritten += 1

            start = start.addSecs(interval)

        if not dry_run:
            self.dataChanged.emit(QModelIndex(), QModelIndex())

        return starts_overwritten

    def racerCount(self):
        return self.rowCount()

    def racerCountTotalInField(self, field_name):
        count = 0

        for row in range(self.rowCount()):
            index = self.index(row, self.fieldIndex(self.FIELD_ALIAS))

            if self.data(index) == field_name:
                count += 1

        return count

    def racerCountFinishedInField(self, field_name):
        count = 0

        for row in range(self.rowCount()):
            field_index = self.index(row, self.fieldIndex(self.FIELD_ALIAS))
            finish_index = self.index(row, self.fieldIndex(self.FINISH))

            if self.data(field_index) == field_name and self.data(finish_index):
                count += 1

        return count

class ResultTableModel(TableModel):
    TABLE = 'result'
    ID = 'id'
    SCRATCHPAD = 'scratchpad'
    FINISH = 'finish'

    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable()

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable(self.TABLE)
        self.setHeaderData(self.fieldIndex(self.SCRATCHPAD),
                           Qt.Horizontal, 'Bib')
        self.setHeaderData(self.fieldIndex(self.FINISH),
                           Qt.Horizontal, 'Finish')
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def createTable(self):
        query = QSqlQuery(self.database())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "%s" ' % self.TABLE +
            '("%s" INTEGER NOT NULL PRIMARY KEY, ' % self.ID +
             '"%s" TEXT NOT NULL, ' % self.SCRATCHPAD +
             '"%s" TIME NOT NULL);' % self.FINISH):
            raise DatabaseError(query.lastError().text())

        query.finish()

    def addResult(self, scratchpad, finish):
        record = self.record()
        record.setGenerated(self.ID, False)
        record.setValue(self.SCRATCHPAD, scratchpad)
        record.setValue(self.FINISH, finish)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def submitResult(self, row):
        record = self.record(row)
        bib = record.value(self.SCRATCHPAD)
        finish = record.value(self.FINISH)

        self.modeldb.racer_table_model.setRacerFinish(bib, finish)
