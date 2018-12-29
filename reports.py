#!/usr/bin/env python3

"""Reports Qt Classes

This module contains the dialog that can be used to generate race reports.
"""

import re
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QComboBox, QDialog, QGroupBox, QPushButton, QRadioButton
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
import common
from racemodel import msecs_is_valid, msecs_to_string, RaceTableModel, RacerTableModel

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
__author__ = common.AUTHOR
__credits__ = common.CREDITS
__license__ = common.LICENSE
__version__ = common.VERSION
__maintainer__ = common.MAINTAINER
__email__ = common.EMAIL
__status__ = common.STATUS

class ReportsWindow(QDialog):
    """This dialog allows the user to generate finish reports."""

    def __init__(self, modeldb, parent=None):
        """Initialize the ReportsWindow instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        field_table_model = self.modeldb.field_table_model
        field_name_column = field_table_model.name_column

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

        self.read_settings()

    def generate_finish_report(self):
        """Generate finish report, using the information from the dialog's input widgets."""
        document = generate_finish_report(self.modeldb, self.field_combobox.currentText())

        printer = QPrinter()

        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() == QDialog.Accepted:
            document.print(printer)

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Handle hide event."""
        self.write_settings()
        super().hideEvent(event)

    def read_settings(self):
        """Read settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        if settings.contains('pos'):
            self.move(settings.value('pos'))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('pos', self.pos())

        settings.endGroup()

def get_result_row_list(model, cat_list):
    """Get a list of (result, row) tuples, including only cats in cat_list, sorted by result."""
    result_list = []

    for row in range(model.rowCount()):
        category = model.data(model.index(row, model.category_column))
        if not category or category == '':
            category = '5'

        if cat_list and (category not in cat_list):
            continue

        start = model.index(row, model.start_column).data()
        finish = model.index(row, model.finish_column).data()

        if not msecs_is_valid(start):
            result = 'DNS'
        elif not msecs_is_valid(finish):
            result = msecs_to_string(finish)
        else:
            elapsed = finish - start
            result = msecs_to_string(elapsed)

        result_list.append((result, row))

    result_list.sort(key=lambda record: record[0])

    return result_list

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

    model = RacerTableModel(modeldb)
    model.setFilter('%s = "%s"' % (RacerTableModel.FIELD_ALIAS, field_name))
    model.select()

    html = ''
    html += '<style>'
    html += ('h1 {'
             '   font-size: 12pt;'
             '}')
    html += ('h2 {'
             '   font-size: 10pt;'
             '}')
    html += ('h3 {'
             '   font-size: 10pt;'
             '}')
    html += ('table {'
             '   font-size: 10pt;'
             '}')
    html += ('td, th {'
             '   border: 3px solid black;'
             '   padding: 5px;'
             '}')
    html += ('.place, .number, .category, .age, .finish_h {'
             '   text-align: center;'
             '}')
    html += ('.first, .last, .team {'
             '   text-align: left;'
             '}')
    html += ('.finish {'
             '   text-align: right;'
             '}')
    html += '</style>'

    html += '<h1>%s</h1>' % modeldb.race_table_model.get_race_property(RaceTableModel.NAME)
    html += '%s' % modeldb.race_table_model.get_date().toString(Qt.DefaultLocaleLongDate)
    html += '<h2>Results: %s</h2>' % field_name

    for cat_list in subfield_list_by_cat:
        # Make sure cat_list is indeed a list.
        if not cat_list:
            cat_list = []

        if cat_list:
            html += '<div align="center">Cat %s</div>' % ', '.join(cat_list)

        html += '<table>'

        html += ('<tr><th class="place">Place</th> <th class="number">Bib #</th> ' +
                 '<th class="first">First</th> <th class="last">Last</th> ' +
                 '<th class="category">Cat</th> <th class="team">Team</th> ' +
                 '<th class="finish_h">Finish</th> <th class="age">Age</th> </tr>')

        # Build (result, row) list and sort by result.
        result_list = get_result_row_list(model, cat_list)

        position = 1
        for result, row in result_list:
            category = model.data(model.index(row, model.category_column))
            if not category or category == '':
                category = '5'

            if cat_list and (category not in cat_list):
                continue

            bib = model.index(row, model.bib_column).data()
            first_name = model.index(row, model.first_name_column).data()
            last_name = model.index(row, model.last_name_column).data()
            team = model.index(row, model.team_column).data()
            age = model.index(row, model.age_column).data()
            finish = model.index(row, model.finish_column).data()

            if msecs_is_valid(finish):
                place = position
            else:
                place = 'DNP'
                result = '-'

            html += ('<tr><td class="place">%s</td> ' % place +
                     '<td class="number">%s</td> ' % bib +
                     '<td class="first">%s</td> ' % first_name +
                     '<td class="last">%s</td> ' % last_name +
                     '<td class="category">%s</td> ' % category +
                     '<td class="team">%s</td> ' % team +
                     '<td class="finish">%s</td> ' % result +
                     '<td class="age">%s</td> ' % age +
                     '</tr>')

            position += 1

        html += '</table>'

    document = QTextDocument()
    document.setHtml(html)

    return document
