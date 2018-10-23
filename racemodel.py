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

class TableModel(QSqlRelationalTableModel):
    def __init__(self, modeldb):
        super().__init__(db=modeldb.db)

        self.modeldb = modeldb
        self.column_flags_to_add = {}
        self.column_flags_to_remove = {}

    def createTable(self):
        raise NotImplementedError

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

    def recordDict(self, record):
        record_dict = {}

        for index in range(record.count()):
            record_dict[record.field(index).name()] = record.field(index).value()

        return record_dict

class RaceTableModel(TableModel):
    TABLE = 'race'
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
            '("%s" TEXT NOT NULL PRIMARY KEY, ' % self.KEY +
             '"%s" TEXT NOT NULL);' % self.VALUE):
            raise DatabaseError(query.lastError().text())

        if new:
            if not query.exec(
                'INSERT INTO Race VALUES("Race name", "(race name here)");'):
                raise DatabaseError(query.lastError().text())

        query.finish()

    def recordAtRow(self, row):
        return { self.KEY: self.record(row).value(self.KEY),
                 self.VALUE: self.record(row).value(self.VALUE) }

    def addRaceProperty(self, key, value):
        record = self.record()
        record.setValue(self.KEY, key)
        record.setValue(self.VALUE, value)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.race.select():
            raise DatabaseError(self.lastError().text())

        record_dict = self.recordDict(record)

        racePropertyAdded.emit(record_dict)

    def deleteRaceProperty(self, row):
        record_dict = self.recordDict(self.record(row))

        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

        racePropertyDeleted.emit(record_dict)

    racePropertyAdded = pyqtSignal(dict)
    racePropertyDeleted = pyqtSignal(dict)

class FieldTableModel(TableModel):
    TABLE = 'field'
    ID = 'id'
    NAME = 'name'

    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable()

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable(self.TABLE)
        self.setHeaderData(self.fieldIndex(self.NAME), Qt.Horizontal, 'Field')
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def createTable(self):
        query = QSqlQuery(self.database())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "%s" ' % self.TABLE +
            '("%s" INTEGER NOT NULL PRIMARY KEY, ' % self.ID +
             '"%s" TEXT NOT NULL);' % self.NAME):
            raise DatabaseError(query.lastError().text())

        query.finish()

    def recordAtRow(self, row):
        return { self.ID: self.record(row).value(self.ID),
                 self.NAME: self.record(row).value(self.NAME) }

    def nameFromId(self, field_id):
        model = QSqlRelationalTableModel(db=self.modeldb.db)
        model.setTable(self.TABLE)
        model.setFilter('%s = %s' % (self.ID, field_id))
        if not model.select():
            raise DatabaseError(model.lastError().text())

        if model.rowCount() == 0:
            raise InputError('Failed to find field_id %s' % field_id)

        if model.rowCount() > 1:
            raise InternalModelError('Internal error, duplicate id %s ' % field_id +
                                     ' found in field table')

        record = model.record(0)

        return record.value(self.NAME)

    def addField(self, name):
        record = self.record()
        record.setValue('name', name)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.select():
            raise DatabaseError(self.lastError().text())

        record.setValue(self.ID, self.rowCount()-1)
        record_dict = self.recordDict(record)

        self.fieldAdded.emit(record_dict)

    def deleteField(self, row):
        record_dict = self.recordDict(self.record(row))

        field_id = self.record(row).value(self.ID)
        if self.modeldb.racer_table_model.racerCountTotalInField(field_id) > 0:
            raise InputError('Trying to delete non-empty field')

        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

        self.fieldDeleted.emit(record_dict)

    # TODO: Really should just specify finisher column has changed, rather than
    # the entire table model.
    def signalFinishersChanged(self):
        top_left = QModelIndex()
        bottom_right = QModelIndex()
        self.modeldb.field_table_model.dataChanged.emit(top_left, bottom_right)

    fieldAdded = pyqtSignal(dict)
    fieldDeleted = pyqtSignal(dict)

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
                         FieldTableModel.NAME));
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

    def recordAtRow(self, row):
        return { self.BIB: self.record(row).value(self.BIB),
                 self.NAME: self.record(row).value(self.NAME),
                 self.TEAM: self.record(row).value(self.TEAM),
                 self.FIELD: self.record(row).value(self.FIELD),
                 self.START: self.record(row).value(self.START),
                 self.FINISH: self.record(row).value(self.FINISH),
                 self.STATUS: self.record(row).value(self.TEAM) }

    def fieldNameFromId(self, field_id):
        return self.modeldb.field_table_model.nameFromId(field_id)

    def addRacer(self, bib, name, team, field, start, finish, status='local'):
        # See if the field exists in our Field table.  If not, we add a new
        # field.
        field_relation_model = self.relationModel(
                                        self.fieldIndex(self.FIELD_ALIAS))
        field_relation_model.setFilter('%s = "%s"' % (FieldTableModel.NAME, field))
        if not field_relation_model.select():
            raise DatabaseError(field_relation_model.lastError().text())

        # Yup, not there. Add it, and then select it. Should just be the one
        # after adding.
        if field_relation_model.rowCount() == 0:
            self.modeldb.field_table_model.addField(field)
            if not field_relation_model.select():
                raise DatabaseError(field_relation_model.lastError().text())

        # Make sure there's only one, and get its field id.
        if field_relation_model.rowCount() != 1:
            raise InternalModelError('More than one field with the same name found')
        field_id = (field_relation_model.record(0).field(field_relation_model
                                        .fieldIndex(FieldTableModel.ID)).value())

        # Restore the filter. This model is actually owned by the racer model
        # that we got this from via relationModel(), and I guess it uses it
        # to populate the combobox. If we don't do this, the combobox will
        # only show the latest field added, which I guess makes sense.
        field_relation_model.setFilter('')

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

        record.setValue(self.ID, self.rowCount()-1)
        record_dict = self.recordDict(record)

        self.racerAdded.emit(record_dict)

    def deleteRacer(self, row):
        record_dict = self.recordDict(self.record(row))

        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

        self.racerDeleted.emit(record_dict)

    def setRacerFinish(self, bib, finish):
        model = QSqlRelationalTableModel(db=self.modeldb.db)
        model.setEditStrategy(QSqlTableModel.OnFieldChange)
        model.setTable(self.TABLE)
        model.setFilter('%s = %s' % (self.BIB, bib))
        if not model.select():
            raise DatabaseError(model.lastError().text())

        if model.rowCount() == 0:
            raise InputError('Setting racer finish failed, ' +
                             'bib %s not found' % bib)

        if model.rowCount() > 1:
            raise InternalModelError('Internal error, duplicate bib %s ' % bib +
                                     ' found in racer table')

        record = model.record(0)

        record.setValue(self.FINISH, finish)

        record_dict = self.recordDict(record)

        if not model.setRecord(0, record):
            raise DatabaseError(model.lastError().text())

        if not self.select():
            raise DatabaseError(self.lastError().text())

        self.racerFinished.emit(record_dict)

    def racerCount(self):
        return self.rowCount()

    def racerCountTotalInField(self, field_id):
        model = QSqlRelationalTableModel(db=self.modeldb.db)
        model.setTable(self.TABLE)
        model.setFilter('%s = %s' % (self.FIELD, field_id))
        if not model.select():
            raise DatabaseError(model.lastError().text())

        return model.rowCount()

    def racerCountFinishedInField(self, field_id):
        model = QSqlRelationalTableModel(db=self.modeldb.db)
        model.setTable(self.TABLE)
        model.setFilter('%s = %s AND %s IS NOT NULL' % (self.FIELD, field_id,
                                                        self.FINISH))
        if not model.select():
            raise DatabaseError(model.lastError().text())

        return model.rowCount()

    racerAdded = pyqtSignal(dict)
    racerDeleted = pyqtSignal(dict)
    racerFinished = pyqtSignal(dict)

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

    def recordAtRow(self, row):
        return { self.SCRATCHPAD: self.record(row).value(self.SCRATCHPAD),
                 self.FINISH: self.record(row).value(self.FINISH) }

    def addResult(self, scratchpad, finish):
        record = self.record()
        record.setValue(self.SCRATCHPAD, scratchpad)
        record.setValue(self.FINISH, finish)

        self.insertRecord(-1, record)
        if not self.select():
            raise DatabaseError(self.lastError().text())

        record.setValue(self.ID, self.rowCount()-1)
        record_dict = self.recordDict(record)

        self.resultAdded.emit(record_dict)

    def deleteResult(self, row):
        record_dict = self.recordDict(self.record(row))

        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

        self.resultDeleted.emit(record_dict)

    def submitResult(self, row):
        record = self.record(row)
        bib = record.value(self.SCRATCHPAD)
        finish = record.value(self.FINISH)

        self.modeldb.racer_table_model.setRacerFinish(bib, finish)

        record_dict = self.recordDict(self.record(row))

        self.resultSubmitted.emit(record_dict)

    resultAdded = pyqtSignal(dict)
    resultDeleted = pyqtSignal(dict)
    resultSubmitted = pyqtSignal(dict)
