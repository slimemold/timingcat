import os
from PyQt5.QtCore import *
from PyQt5.QtSql  import *

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
            raise Exception('Invalid database')

        self.db.setDatabaseName(filename)

        if not self.db.open():
            raise Exception(self.db.lastError().text())

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

    def createTable():
        raise NotImplemented

class RaceTableModel(TableModel):
    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable(new)

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable('race')
        if not self.select():
            raise Exception(self.lastError().text())

    def createTable(self, new):
        query = QSqlQuery(self.database())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "race" ' +
            '("key" TEXT NOT NULL PRIMARY KEY, ' +
             '"value" TEXT NOT NULL);'):
            raise Exception(query.lastError().text())

        if new:
            if not query.exec(
                'INSERT INTO Race VALUES("Race name", "(race name here)");'):
                raise Exception(query.lastError().text())

        query.finish()

    def addRaceProperty(self, key, value):
        record = self.record()
        record.setValue('key', key)
        record.setValue('value', value)

        if not self.insertRecord(-1, record):
            raise Exception(self.lastError().text())
        if not self.race.select():
            raise Exception(self.lastError().text())

class FieldTableModel(TableModel):
    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable()

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable('field')
        self.setHeaderData(self.fieldIndex('name'), Qt.Horizontal, 'Field')
        if not self.select():
            raise Exception(self.lastError().text())

    def createTable(self):
        query = QSqlQuery(self.database())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "field" ' +
            '("id" INTEGER NOT NULL PRIMARY KEY, ' +
             '"name" TEXT NOT NULL, ' +
             '"data" TEXT NOT NULL);'):
            raise Exception(query.lastError().text())

        query.finish()

    def addField(self, name, data='{}'):
        record = self.record()
        record.setValue('name', name)
        record.setValue('data', data)

        if not self.insertRecord(-1, record):
            raise Exception(self.lastError().text())
        if not self.select():
            raise Exception(self.lastError().text())

class RacerTableModel(TableModel):
    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable()

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable('racer')
        self.setHeaderData(self.fieldIndex('bib'), Qt.Horizontal, 'Bib')
        self.setHeaderData(self.fieldIndex('name'), Qt.Horizontal, 'Name')
        self.setHeaderData(self.fieldIndex('team'), Qt.Horizontal, 'Team')
        self.setHeaderData(self.fieldIndex('field_id'), Qt.Horizontal, 'Field')
        self.setHeaderData(self.fieldIndex('start'), Qt.Horizontal, 'Start')
        self.setHeaderData(self.fieldIndex('finish'), Qt.Horizontal, 'Finish')

        # After this relation is defined, the field name becomes
        # "field_name_2".
        self.setRelation(self.fieldIndex('field_id'),
                         QSqlRelation('field', 'id', 'name'));
        if not self.select():
            raise Exception(self.lastError().text())

    def createTable(self):
        query = QSqlQuery(self.database())

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

        query.finish()

    def addRacer(self, bib, name, team, field, start, finish, data='{}'):
        # See if the field exists in our Field table.  If not, we add a new
        # field.
        field_relation_model = self.relationModel(
                                        self.fieldIndex('field_name_2'))
        field_relation_model.setFilter('name = "%s"' % field)
        if not field_relation_model.select():
            raise Exception(field_relation_model.lastError().text())

        # Yup, not there. Add it, and then select it. Should just be the one
        # after adding.
        if field_relation_model.rowCount() == 0:
            self.modeldb.field_table_model.addField(field)
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

        record = self.record()
        record.setValue('bib', bib)
        record.setValue('name', name)
        record.setValue('team', team)

        # OMFG I can't believe I have to do this...but Qt is not retranslating
        # this stupid field_name_2 alias back to its original field name,
        # so the database ends up getting the alias instead of the proper
        # one, failing the transaction. This piece of code switches the
        # field back from the field_name_2 alias to the original field_id,
        # so that the ensuing sql query can work.
        sql_field = record.field(self.fieldIndex('field_name_2'))
        sql_field.setName('field_id')
        record.replace(self.fieldIndex('field_name_2'), sql_field)
        record.setValue('field_id', field_id)

        record.setValue('start', start)
        record.setValue('finish', finish)
        record.setValue('data', data)

        if not self.insertRecord(-1, record):
            raise Exception(self.lastError().text())
        if not self.submitAll():
            raise Exception(self.lastError().text())
        if not self.select():
            raise Exception(self.lastError().text())

class ResultTableModel(TableModel):
    def __init__(self, modeldb, new):
        super().__init__(modeldb)

        self.createTable()

        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.setTable('result')
        self.setHeaderData(self.fieldIndex('scratchpad'), Qt.Horizontal, 'Bib')
        self.setHeaderData(self.fieldIndex('finish'), Qt.Horizontal, 'Finish')
        if not self.select():
            raise Exception(self.lastError().text())

    def createTable(self):
        query = QSqlQuery(self.database())

        if not query.exec(
            'CREATE TABLE IF NOT EXISTS "result" ' +
            '("id" INTEGER NOT NULL PRIMARY KEY, ' +
             '"scratchpad" TEXT NOT NULL, ' +
             '"finish" TIME NOT NULL, ' +
             '"data" TEXT NOT NULL);'):
            raise Exception(query.lastError().text())

        query.finish()

    def addResult(self, scratchpad, finish, data='{}'):
        record = self.record()
        record.setValue('scratchpad', scratchpad)
        record.setValue('finish', finish)
        record.setValue('data', data)

        self.insertRecord(-1, record)
        if not self.select():
            raise Exception(self.lastError().text())

    def deleteResult(self, row):
        record = self.record()