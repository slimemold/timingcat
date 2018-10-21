import os
from PyQt5.QtCore import *
from PyQt5.QtSql  import *
from common import *

class DatabaseError(Exception):
    pass

class InternalModelError(Exception):
    pass

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

    def createTable(self):
        raise NotImplementedError

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

    def addRaceProperty(self, key, value):
        record = self.record()
        record.setValue(self.KEY, key)
        record.setValue(self.VALUE, value)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.race.select():
            raise DatabaseError(self.lastError().text())

    def deleteRaceProperty(self, row):
        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

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

    def addField(self, name):
        record = self.record()
        record.setValue('name', name)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.select():
            raise DatabaseError(self.lastError().text())

    # TODO: Must check to make sure the field is empty before allowing delete.
    def deleteField(self, row):
        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

class RacerTableModel(TableModel):
    TABLE = 'racer'
    ID = 'id'
    BIB = 'bib'
    NAME = 'name'
    TEAM = 'team'
    FIELD = 'field_id'
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
             '"%s" INTEGER, ' % self.FIELD +
             '"%s" TIME NOT NULL, ' % self.START +
             '"%s" TIME NOT NULL, ' % self.FINISH +
             '"%s" TEXT NOT NULL);' % self.STATUS):
            raise DatabaseError(query.lastError().text())

        query.finish()

    def addRacer(self, bib, name, team, field, start, finish, status='local'):
        # See if the field exists in our Field table.  If not, we add a new
        # field.
        field_relation_model = self.relationModel(
                                        self.fieldIndex('field_name_2'))
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
        record.setValue(self.BIB, bib)
        record.setValue(self.NAME, name)
        record.setValue(self.TEAM, team)

        # OMFG I can't believe I have to do this...but Qt is not retranslating
        # this stupid field_name_2 alias back to its original field name,
        # so the database ends up getting the alias instead of the proper
        # one, failing the transaction. This piece of code switches the
        # field back from the field_name_2 alias to the original field_id,
        # so that the ensuing sql query can work.
        sql_field = record.field(self.fieldIndex('field_name_2'))
        sql_field.setName(self.FIELD)
        record.replace(self.fieldIndex('field_name_2'), sql_field)
        record.setValue(self.FIELD, field_id)

        record.setValue(self.START, start)
        record.setValue(self.FINISH, finish)
        record.setValue(self.STATUS, status)

        if not self.insertRecord(-1, record):
            raise DatabaseError(self.lastError().text())
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def deleteRacer(self, row):
        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

    def setRacerFinish(self, bib, finish):
        print('setFinish(%s, %s)' % (bib, finish))

        model = QSqlRelationalTableModel(db=self.modeldb.db)
        model.setTable(self.TABLE)
        model.setFilter('%s = %s' % (self.BIB, bib))
        if not model.select():
            raise DatabaseError(model.lastError().text())

        if model.rowCount() == 0:
            raise UserError('Setting racer finish failed, ' +
                            'bib %s not found' % bib)

        if model.rowCount() > 1:
            raise InternalModelError('Internal error, duplicate bib %s ' % bib +
                                     ' found in racer table')

        model.record(0).setValue(self.BIB, bib)
        model.record(0).setValue(self.FINISH, finish)

        if not model.setRecord(0, model.record(0)):
            raise DatabaseError(self.lastError().text())

        if not self.select():
            raise DatabaseError(self.lastError().text())


        print('found %s rows with bib %s' % (model.rowCount(), bib))


class ResultTableModel(TableModel):
    TABLE = 'result'
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
            '("id" INTEGER NOT NULL PRIMARY KEY, ' +
             '"%s" TEXT NOT NULL, ' % self.SCRATCHPAD +
             '"%s" TIME NOT NULL);' % self.FINISH):
            raise DatabaseError(query.lastError().text())

        query.finish()

    def addResult(self, scratchpad, finish):
        record = self.record()
        record.setValue(self.SCRATCHPAD, scratchpad)
        record.setValue(self.FINISH, finish)

        self.insertRecord(-1, record)
        if not self.select():
            raise DatabaseError(self.lastError().text())

    def deleteResult(self, row):
        if not self.removeRow(row):
            raise DatabaseError(self.lastError().text())

    def commitResult(self, row):
        record = self.record(row)
        bib = record.value(self.SCRATCHPAD)
        finish = record.value(self.FINISH)

        self.modeldb.racer_table_model.setRacerFinish(bib, finish)