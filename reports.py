from PyQt5.QtGui import *
from racemodel import *
import re

def time_delta(finish, start):
    if not start:
        return 'DNS'

    if not finish:
        return 'DNF'

    msecs = start.msecsTo(finish)

    hours = msecs // 3600000
    msecs = msecs % 3600000

    minutes = msecs // 60000
    msecs = msecs % 60000

    secs = msecs // 1000
    msecs = msecs % 1000

    if hours > 0:
        return QTime(hours, minutes, secs, msecs).toString('h:mm:ss.zzz')
    else:
        return QTime(hours, minutes, secs, msecs).toString('m:ss.zzz')

def generate_finish_report(modeldb, field_name):
    subfields = modeldb.field_table_model.getSubfields(field_name)

    subfield_list_by_cat = [None]

    if subfields:
        subfield_list_by_cat = []
        subfield_list = re.split('[; ]+', subfields)
        for subfield in subfield_list:
            cat_list = re.split('[, ]+', subfield)
            subfield_list_by_cat.append(cat_list)

    model = QSqlRelationalTableModel(db=modeldb.db)
    model.setTable(RacerTableModel.TABLE)
    model.setRelation(model.fieldIndex(RacerTableModel.FIELD),
        QSqlRelation(FieldTableModel.TABLE,
                     FieldTableModel.ID,
                     FieldTableModel.NAME))
    model.setFilter('%s = "%s"' % (RacerTableModel.FIELD_ALIAS, field_name))
    if not model.select():
        raise DatabaseError(model.lastError().text())

    html = '<h1>%s</h1>' % modeldb.race_table_model.getRaceProperty(RaceTableModel.NAME)
    html += '%s' % modeldb.race_table_model.getRaceProperty(RaceTableModel.DATE)
    html += '<h2>Results: %s</h2>' % field_name

    for cat_list in subfield_list_by_cat:
        if cat_list:
            html += '<div align="center">Cat %s</div>' % ', '.join(cat_list)

        html += '<table>'

        html += '<tr><td>Place</td> <td>#</td> <td>First</td> <td>Last</td> <td>Cat</td> <td>Team</td> <td>Finish</td> <td>Age</td> </tr>'
        place = 1
        for row in range(model.rowCount()):
            category = model.data(model.index(row, model.fieldIndex(RacerTableModel.CATEGORY)))
            if not category or category == '':
                category = '5'

            if category not in cat_list:
                continue

            bib = model.data(model.index(row, model.fieldIndex(RacerTableModel.BIB)))
            first_name = model.data(model.index(row, model.fieldIndex(RacerTableModel.FIRST_NAME)))
            last_name = model.data(model.index(row, model.fieldIndex(RacerTableModel.LAST_NAME)))
            team = model.data(model.index(row, model.fieldIndex(RacerTableModel.TEAM)))
            start = QTime.fromString(model.data(model.index(row, model.fieldIndex(RacerTableModel.START))))
            finish = QTime.fromString(model.data(model.index(row, model.fieldIndex(RacerTableModel.FINISH))))
            delta = time_delta(finish, start)
            age = model.data(model.index(row, model.fieldIndex(RacerTableModel.AGE)))

            html += ('<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> </tr>' %
                     (place, bib, first_name, last_name, category, team, delta, age))

            place += 1

        html += '</table>'

    document = QTextDocument()
    document.setHtml(html)

    return document
