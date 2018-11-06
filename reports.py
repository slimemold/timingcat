"""Reports Qt Classes

This module contains the dialog that can be used to generate race reports.
"""

import re
from PyQt5.QtCore import QTime
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtSql import QSqlRelation, QSqlRelationalTableModel
from PyQt5.QtWidgets import QComboBox, QDialog, QGroupBox, QPushButton, QRadioButton
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from common import VERSION
from racemodel import DatabaseError, RaceTableModel, FieldTableModel, RacerTableModel

__author__ = 'Andrew Chew'
__copyright__ = '''
    Copyright (C) 2018 Andrew Chew

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
__credits__ = ['Andrew Chew', 'Colleen Chew']
__license__ = 'GPLv3'
__version__ = VERSION
__maintainer__ = 'Andrew Chew'
__email__ = 'andrew@5rcc.com'
__status__ = 'Development'

class ReportsWindow(QDialog):
    """This dialog allows the user to generate finish reports."""

    def __init__(self, modeldb, parent=None):
        """Initialize the ReportsWindow instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        field_table_model = self.modeldb.field_table_model
        field_name_column = field_table_model.fieldIndex(self.modeldb.field_table_model.NAME)

        self.setWindowTitle('Generate Reports')

        # Finish results by field.
        self.field_finish_radiobutton = QRadioButton()
        self.field_combobox = QComboBox()
        self.field_combobox.setModel(field_table_model)
        self.field_combobox.setModelColumn(field_name_column)

        field_finish_groupbox = QGroupBox('Finish results by field')
        field_finish_groupbox.setLayout(QHBoxLayout())
        field_finish_groupbox.layout().addWidget(self.field_finish_radiobutton)
        field_finish_groupbox.layout().addWidget(self.field_combobox)

        self.field_finish_radiobutton.setChecked(True)

        generate_finish_button = QPushButton('Generate Report')

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(field_finish_groupbox)
        self.layout().addWidget(generate_finish_button)

        generate_finish_button.clicked.connect(self.generate_finish_report)

    def generate_finish_report(self):
        """Generate finish report, using the information from the dialog's input widgets."""
        document = generate_finish_report(self.modeldb, self.field_combobox.currentText())

        printer = QPrinter()

        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() == QDialog.Accepted:
            document.print(printer)

def time_delta(finish, start):
    """Return a string representing the time difference between the start and the finish."""
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
        time = QTime(hours, minutes, secs, msecs).toString('h:mm:ss.zzz')
    else:
        time = QTime(hours, minutes, secs, msecs).toString('m:ss.zzz')

    return time

def generate_finish_report(modeldb, field_name):
    """ Generate finish report for a particular field."""
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
        # Make sure cat_list is indeed a list.
        if not cat_list:
            cat_list = []

        if cat_list:
            html += '<div align="center">Cat %s</div>' % ', '.join(cat_list)

        html += '<table>'

        html += ('<tr><td>Place</td> <td>#</td> <td>First</td> <td>Last</td> <td>Cat</td> ' +
                 '<td>Team</td> <td>Finish</td> <td>Age</td> </tr>')
        place = 1
        for row in range(model.rowCount()):
            category = model.data(model.index(row, model.fieldIndex(RacerTableModel.CATEGORY)))
            if not category or category == '':
                category = '5'

            if cat_list and (category not in cat_list):
                continue

            racer_bib_column = model.fieldIndex(RacerTableModel.BIB)
            racer_first_name_column = model.fieldIndex(RacerTableModel.FIRST_NAME)
            racer_last_name_column = model.fieldIndex(RacerTableModel.LAST_NAME)
            racer_team_column = model.fieldIndex(RacerTableModel.TEAM)
            racer_start_column = model.fieldIndex(RacerTableModel.START)
            racer_finish_column = model.fieldIndex(RacerTableModel.FINISH)

            bib = model.data(model.index(row, racer_bib_column))
            first_name = model.data(model.index(row, racer_first_name_column))
            last_name = model.data(model.index(row, racer_last_name_column))
            team = model.data(model.index(row, racer_team_column))
            start = QTime.fromString(model.data(model.index(row, racer_start_column)))
            finish = QTime.fromString(model.data(model.index(row, racer_finish_column)))
            delta = time_delta(finish, start)
            age = model.data(model.index(row, model.fieldIndex(RacerTableModel.AGE)))

            html += ('<tr><td>%s</td> ' % place +
                     '<td>%s</td> ' % bib +
                     '<td>%s</td> ' % first_name +
                     '<td>%s</td> ' % last_name +
                     '<td>%s</td> ' % category +
                     '<td>%s</td> ' % team +
                     '<td>%s</td> ' % delta +
                     '<td>%s</td> ' % age +
                     '</tr>')

            place += 1

        html += '</table>'

    document = QTextDocument()
    document.setHtml(html)

    return document
