from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtWidgets import *
from racemodel import *
import re

class ReportsWindow(QDialog):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.setWindowTitle('Generate Reports')

        # Finish results by field.
        self.field_finish_radiobutton = QRadioButton()
        self.field_combobox = QComboBox()
        self.field_combobox.setModel(self.modeldb.field_table_model)
        self.field_combobox.setModelColumn(self.modeldb.field_table_model.fieldIndex(self.modeldb.field_table_model.NAME))

        field_finish_groupbox = QGroupBox('Finish results by field')
        field_finish_groupbox.setLayout(QHBoxLayout())
        field_finish_groupbox.layout().addWidget(self.field_finish_radiobutton)
        field_finish_groupbox.layout().addWidget(self.field_combobox)

        self.field_finish_radiobutton.setChecked(True)

        generateFinish = QPushButton('Generate Report')

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(field_finish_groupbox)
        self.layout().addWidget(generateFinish)

        generateFinish.clicked.connect(self.generateFinishReport)

    def generateFinishReport(self):
        document = generate_finish_report(self.modeldb, self.field_combobox.currentText())

        printer = QPrinter()

        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() == QDialog.Accepted:
            document.print(printer)

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
    subfields = modeldb.field_table_model.get_subfields(field_name)

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

    html = '<h1>%s</h1>' % modeldb.race_table_model.get_race_property(RaceTableModel.NAME)
    html += '%s' % modeldb.race_table_model.get_race_property(RaceTableModel.DATE)
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

            if cat_list and (category not in cat_list):
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
