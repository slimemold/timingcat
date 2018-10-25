import os
from PyQt5.QtCore import *
from PyQt5.QtSql  import *
from common import *

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
        if not self.getRaceProperty('Race name'):
            self.addRaceProperty('Race name', '(race name here)')

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
        index = None
        for row in range(self.rowCount()):
            if self.data(self.index(row, self.fieldIndex(self.KEY))) == key:
                index = self.index(row, self.fieldIndex(self.KEY))
                break

        if not index:
            raise InputError('Failed to find race property with KEY %s' % key)

        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

    def getRaceProperty(self, key):
        index = None
        for row in range(self.rowCount()):
            if self.data(self.index(row, self.fieldIndex(self.KEY))) == key:
                index = self.index(row, self.fieldIndex(self.KEY))
                break

        if not index:
            return None

        return self.data(self.index(row, self.fieldIndex(self.VALUE)))

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
            self.addField('default')

    def nameFromId(self, field_id):
        index = None
        for row in range(self.rowCount()):
            if self.data(self.index(row, self.fieldIndex(self.ID))) == field_id:
                index = self.index(row, self.fieldIndex(self.ID))
                break

        if not index:
            return None

        return self.data(self.index(row, self.fieldIndex(self.NAME)))

    def idFromName(self, field_name):
        index = None
        for row in range(self.rowCount()):
            if self.data(self.index(row, self.fieldIndex(self.NAME))) == field_name:
                index = self.index(row, self.fieldIndex(self.NAME))
                break

        if not index:
            return None

        return self.data(self.index(row, self.fieldIndex(self.ID)))

    def addField(self, name):
        record = self.record()
        record.setGenerated(self.ID, False)
        record.setValue(FieldTableModel.NAME, name)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def deleteField(self, name):
        index = None
        for row in range(self.rowCount()):
            if self.data(self.index(row, self.fieldIndex(self.NAME))) == name:
                index = self.index(row, self.fieldIndex(self.NAME))
                break

        if not index:
            raise InputError('Failed to find field with NAME %s' % name)

        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

class RacerTableModel(TableModel):
    TABLE = 'racer'
    ID = 'id'
    BIB = 'bib'
    NAME = 'name'
    TEAM = 'team'
    FIELD = 'field_id'
    FIELD_ALIAS = 'field_name_2'
    START = 'start'
    FINISH = 'finish'
    STATUS = 'status'

    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable()

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable(self.TABLE)
        self.setHeaderData(self.fieldIndex(self.BIB), Qt.Horizontal, 'Bib')
        self.setHeaderData(self.fieldIndex(self.NAME), Qt.Horizontal, 'Name')
        self.setHeaderData(self.fieldIndex(self.TEAM), Qt.Horizontal, 'Team')
        self.setHeaderData(self.fieldIndex(self.FIELD), Qt.Horizontal, 'Field')
        self.setHeaderData(self.fieldIndex(self.START), Qt.Horizontal, 'Start')
        self.setHeaderData(self.fieldIndex(self.FINISH), Qt.Horizontal, 'Finish')
        self.setHeaderData(self.fieldIndex(self.STATUS), Qt.Horizontal, 'Status')

        # After this relation is defined, the field name becomes
        # "field_name_2".
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
             '"%s" TEXT NOT NULL, ' % self.NAME +
             '"%s" TEXT NOT NULL, ' % self.TEAM +
             '"%s" INTEGER NOT NULL, ' % self.FIELD +
             '"%s" TIME, ' % self.START +
             '"%s" TIME, ' % self.FINISH +
             '"%s" TEXT NOT NULL);' % self.STATUS):
            raise DatabaseError(query.lastError().text())

        query.finish()

    def addRacer(self, bib, name, team, field, start, finish, status='local'):
        # See if the field exists in our Field table.  If not, we add a new
        # field.
        field_id = self.modeldb.field_table_model.idFromName(field)
        if not field_id:
            self.modeldb.field_table_model.addField(field)
            field_id = self.modeldb.field_table_model.idFromName(field)

        record = self.record()
        record.setGenerated(self.ID, False)
        record.setValue(self.BIB, bib)
        record.setValue(self.NAME, name)
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
        index = None
        for row in range(self.rowCount()):
            if self.data(self.index(row, self.fieldIndex(self.BIB))) == bib:
                index = self.index(row, self.fieldIndex(self.BIB))
                break

        if not index:
            raise InputError('Failed to find racer with BIB %s' % bib)

        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

    def setRacerFinish(self, bib, finish):
        index = None
        for row in range(self.rowCount()):
            if self.data(self.index(row, self.fieldIndex(self.BIB))) == int(bib):
                index = self.index(row, self.fieldIndex(self.BIB))
                break

        if not index:
            raise InputError('Failed to find racer with bib %s' % bib)

        self.setData(self.index(row, self.fieldIndex(self.FINISH)), finish)
        self.dataChanged.emit(index, index)

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
