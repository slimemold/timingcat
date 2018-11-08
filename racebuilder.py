#!/usr/bin/env python3

"""RaceBuilder Qt Classes

This module implements Qt Widgets that have to do with setting up a race, or
adding and configuring components of a race, such as racers and fields.
"""

from PyQt5.QtCore import QDate, QModelIndex, QRegExp, QSettings, QTime, Qt
from PyQt5.QtGui import QRegExpValidator, QTextDocument, QValidator
from PyQt5.QtWidgets import QComboBox, QLabel, QLineEdit, QPlainTextEdit, \
                            QPushButton, QRadioButton, QWidget
from PyQt5.QtWidgets import QCalendarWidget, QDateEdit, QTimeEdit
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QButtonGroup, QGroupBox, QTabWidget
from PyQt5.QtWidgets import QCompleter, QMessageBox, QPlainTextDocumentLayout
from common import VERSION
import defaults
from racemodel import RaceTableModel, FieldTableModel, RacerTableModel, InputError

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

class RacerSetup(QWidget):
    """Racer Setup

    This widget allows the user to add racers.
    """

    def __init__(self, modeldb, parent=None):
        """Initialize the RacerSetup instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        racer_table_model = self.modeldb.racer_table_model
        racer_team_column = racer_table_model.fieldIndex(RacerTableModel.TEAM)

        field_table_model = self.modeldb.field_table_model
        field_name_column = field_table_model.fieldIndex(FieldTableModel.NAME)

        # Racer Information form.
        self.first_name_lineedit = QLineEdit()
        self.first_name_lineedit.setValidator(QRegExpValidator(QRegExp('.+')))
        self.last_name_lineedit = QLineEdit()
        self.last_name_lineedit.setValidator(QRegExpValidator(QRegExp('.+')))
        self.team_lineedit = QLineEdit()
        self.team_lineedit.setCompleter(QCompleter(racer_table_model))
        self.team_lineedit.completer().setCompletionColumn(racer_team_column)
        self.category_lineedit = QLineEdit()
        self.age_lineedit = QLineEdit()
        self.age_lineedit.setValidator(QRegExpValidator(QRegExp('[1-9][0-9]*')))
        self.field_combobox = QComboBox()
        self.field_combobox.setModel(field_table_model)
        self.field_combobox.setModelColumn(field_name_column)
        self.bib_lineedit = QLineEdit()
        self.bib_lineedit.setValidator(QRegExpValidator(QRegExp('[1-9][0-9]*')))

        self.racer_information_form_widget = QWidget()
        self.racer_information_form_widget.setLayout(QFormLayout())
        self.racer_information_form_widget.layout().addRow('First name', self.first_name_lineedit)
        self.racer_information_form_widget.layout().addRow('Last name', self.last_name_lineedit)
        self.racer_information_form_widget.layout().addRow('Team', self.team_lineedit)
        self.racer_information_form_widget.layout().addRow('Category', self.category_lineedit)
        self.racer_information_form_widget.layout().addRow('Age', self.age_lineedit)
        self.racer_information_form_widget.layout().addRow('Field', self.field_combobox)
        self.racer_information_form_widget.layout().addRow('Bib', self.bib_lineedit)

        self.confirm_button = QPushButton('Add Racer')

        # Top-level widgets.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.racer_information_form_widget)
        self.layout().addWidget(self.confirm_button)

        # Signals/slots plumbing.
        self.confirm_button.clicked.connect(self.handle_add_racer)

    def reset(self):
        """Clear the input widgets."""
        self.bib_lineedit.setText('')
        self.first_name_lineedit.setText('')
        self.last_name_lineedit.setText('')
        self.age_lineedit.setText('')
        self.team_lineedit.setText('')

    def handle_add_racer(self):
        """Add the racer, given the information contained in the input widgets."""
        racer_table_model = self.modeldb.racer_table_model
        field_table_model = self.modeldb.field_table_model

        # Do some validation.
        first_name_okay = False
        first_name = self.first_name_lineedit.text()
        validator = self.first_name_lineedit.validator()
        state, _, _ = validator.validate(first_name, self.first_name_lineedit.cursorPosition())
        first_name_okay = state == QValidator.Acceptable

        last_name = self.last_name_lineedit.text()
        validator = self.last_name_lineedit.validator()
        state, _, _ = validator.validate(last_name, self.last_name_lineedit.cursorPosition())
        last_name_okay = state == QValidator.Acceptable

        if not first_name_okay and not last_name_okay:
            QMessageBox.warning(self, 'Error',
                                'Invalid first and last name (need at least a first or last name).')
            return

        team = self.team_lineedit.text() # Team can be blank.
        category = self.category_lineedit.text()
        age = self.age_lineedit.text()

        field = self.field_combobox.currentText()
        if not field_table_model.id_from_name(field):
            QMessageBox.warning(self, 'Error', 'Invalid field %s.' % field)
            return

        bib = self.bib_lineedit.text()
        validator = self.bib_lineedit.validator()
        state, _, _ = validator.validate(bib, self.bib_lineedit.cursorPosition())
        if state != QValidator.Acceptable:
            QMessageBox.warning(self, 'Error', 'Invalid bib number "%s".' % bib)
            return

        try:
            racer_table_model.add_racer(bib, first_name, last_name, field, category, team, age)
            self.reset()

        except InputError as e:
            QMessageBox.warning(self, 'Error', str(e))

class StartTimeSetup(QWidget):
    """Start Time Setup

    This widget allows the user to set up start times. Start times can be the same for the entire
    race, or it can be the same for a particular field. Or, the start times can be assigned
    at a set interval.
    """

    def __init__(self, modeldb, parent=None):
        """Initialize the StartTimeSetup instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        field_table_model = self.modeldb.field_table_model
        field_name_column = field_table_model.fieldIndex(self.modeldb.field_table_model.NAME)

        # Scope selection (whole race vs a field).
        self.field_selection_widget = QGroupBox('Set up start times for:')

        self.scope_button_group = QButtonGroup()
        self.all_fields_radiobutton = QRadioButton('Entire race')
        self.all_fields_radiobutton.setChecked(True)
        self.scope_button_group.addButton(self.all_fields_radiobutton)
        self.selected_field_radiobutton = QRadioButton('A single field:')
        self.scope_button_group.addButton(self.selected_field_radiobutton)

        self.selected_field_combobox = QComboBox()
        self.selected_field_combobox.setModel(field_table_model)
        self.selected_field_combobox.setModelColumn(field_name_column)
        self.selected_field_combobox.setEnabled(False)

        self.field_selection_widget.setLayout(QHBoxLayout())
        self.field_selection_widget.layout().addWidget(self.all_fields_radiobutton)
        self.field_selection_widget.layout().addWidget(self.selected_field_radiobutton)
        self.field_selection_widget.layout().addWidget(self.selected_field_combobox)

        # Start time.
        self.start_time_widget = QGroupBox('Start time:')

        self.start_time_button_group = QButtonGroup()
        self.start_time_now_radiobutton = QRadioButton('Now')
        self.start_time_now_radiobutton.setChecked(True)
        self.start_time_button_group.addButton(self.start_time_now_radiobutton)
        self.start_time_specified_radiobutton = QRadioButton('At:')
        self.start_time_button_group.addButton(self.start_time_specified_radiobutton)
        self.start_time_timeedit = QTimeEdit() # Time "now" set in showEvent()
        self.start_time_timeedit.setDisplayFormat(defaults.TIME_FORMAT)
        self.start_time_timeedit.setEnabled(False)

        self.start_time_widget.setLayout(QHBoxLayout())
        self.start_time_widget.layout().addWidget(self.start_time_now_radiobutton)
        self.start_time_widget.layout().addWidget(self.start_time_specified_radiobutton)
        self.start_time_widget.layout().addWidget(self.start_time_timeedit)

        # Start time interval.
        self.interval_widget = QGroupBox('Interval:')

        self.interval_button_group = QButtonGroup()
        self.same_start_time_radiobutton = QRadioButton('Same for all')
        self.same_start_time_radiobutton.setChecked(True)
        self.interval_button_group.addButton(self.same_start_time_radiobutton)
        self.interval_start_time_radiobutton = QRadioButton('Use interval:')
        self.interval_button_group.addButton(self.interval_start_time_radiobutton)

        self.interval_lineedit = QLineEdit()
        self.interval_lineedit.setText(str(defaults.START_TIME_INTERVAL_SECS))
        self.interval_lineedit.setValidator(QRegExpValidator(QRegExp('[1-9][0-9]*')))
        self.interval_lineedit_group = QWidget()
        self.interval_lineedit_group.setLayout(QHBoxLayout())
        self.interval_lineedit_group.layout().addWidget(self.interval_lineedit)
        self.interval_lineedit_group.layout().addWidget(QLabel('secs'))
        self.interval_lineedit_group.setEnabled(False)

        self.interval_widget.setLayout(QHBoxLayout())
        self.interval_widget.layout().addWidget(self.same_start_time_radiobutton)
        self.interval_widget.layout().addWidget(self.interval_start_time_radiobutton)
        self.interval_widget.layout().addWidget(self.interval_lineedit_group)

        self.confirm_button = QPushButton('Assign Start Times')

        # Top-level widgets.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.field_selection_widget)
        self.layout().addWidget(self.start_time_widget)
        self.layout().addWidget(self.interval_widget)
        self.layout().addWidget(self.confirm_button)

        # Signals/slots plumbing.
        self.confirm_button.clicked.connect(self.handle_assign_start_times)
        self.selected_field_radiobutton.toggled.connect(self.selected_field_combobox.setEnabled)
        self.start_time_specified_radiobutton.toggled.connect(self.start_time_timeedit.setEnabled)
        self.interval_start_time_radiobutton.toggled.connect(self.interval_lineedit_group
                                                             .setEnabled)

    def handle_assign_start_times(self):
        """Assign the start times, given the contents of the various input widgets."""
        racer_table_model = self.modeldb.racer_table_model

        # Validate inputs.
        if not self.interval_lineedit.text().isdigit:
            raise Exception('Invalid interval')

        field = None
        if self.selected_field_radiobutton.isChecked():
            field = self.selected_field_combobox.currentText()

        if self.start_time_now_radiobutton.isChecked():
            start_time = QTime.currentTime()
        else:
            start_time = self.start_time_timeedit.time()

        interval = 0
        if self.interval_start_time_radiobutton.isChecked():
            interval = int(self.interval_lineedit.text())

        try:
            # If we're potentially going to be overwriting existing start times,
            # warn before committing.
            starts_overwritten = racer_table_model.assign_start_times(field, start_time, interval,
                                                                      True)
            if starts_overwritten > 0:
                if QMessageBox.question(self, 'Question',
                                        'About to overwrite %s existing ' % starts_overwritten +
                                        'start times. Proceed anyway?') != QMessageBox.Yes:
                    return
            racer_table_model.assign_start_times(field, start_time, interval)
        except InputError as e:
            QMessageBox.warning(self, 'Error', str(e))

        success_message = 'Start times have been assigned'
        if field:
            success_message += ' to field "%s"' % field

        success_message += ' for %s' % start_time.toString(defaults.TIME_FORMAT)
        if interval:
            success_message += ' at %s secomd intervals' % interval

        success_message += '.'

        QMessageBox.information(self, 'Success', success_message)

    def showEvent(self, event): #pylint: disable=invalid-name
        """Set up input widgets when this widget is shown.

        Basically, this amounts to populating the start time edit box with the current time, plus
        some time ahead, rounded to the nearest 5 minutes.
        """
        now = QTime.currentTime().addSecs(defaults.START_TIME_FROM_NOW_SECS)
        now.setHMS(now.hour(), now.minute() + 5 - now.minute()%5, 0, 0)
        self.start_time_timeedit.setTime(now)

        super().showEvent(event)

class FieldSetup(QWidget):
    """Field Setup

    This widget allows the user to add a new field to the race.
    """

    def __init__(self, modeldb, parent=None):
        """Initialize the FieldSetup instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        # Racer Information form.
        self.name_lineedit = QLineEdit()

        self.field_information_form_widget = QWidget()
        self.field_information_form_widget.setLayout(QFormLayout())
        self.field_information_form_widget.layout().addRow('Name', self.name_lineedit)

        self.confirm_button = QPushButton('Add Field')

        # Top-level widgets.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.field_information_form_widget)
        self.layout().addWidget(self.confirm_button)

        # Signals/slots plumbing.
        self.confirm_button.clicked.connect(self.handle_add_field)

    def reset(self):
        """Clear the input widgets."""
        self.name_lineedit.setText('')

    def handle_add_field(self):
        """Add a new field."""
        field_table_model = self.modeldb.field_table_model

        try:
            field_table_model.add_field(self.name_lineedit.text())
            self.reset()

        except InputError as e:
            QMessageBox.warning(self, 'Error', str(e))

class RaceInfo(QWidget):
    """Race Info Setup

    This widget allows the user to name the race, and jot down various notes about the race.
    """

    def __init__(self, modeldb, parent=None):
        """Initialize the RaceInfo instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        race_table_model = self.modeldb.race_table_model

        self.name_lineedit = QLineEdit()
        self.date_dateedit = QDateEdit()
        self.notes_plaintextedit = QPlainTextEdit()
        self.notes_plaintextedit.setPlaceholderText(defaults.RACE_NOTES_PLACEHOLDER_TEXT)
        self.dataChanged(QModelIndex(), QModelIndex(), [])

        self.date_selection_widget = QWidget()
        self.date_selection_widget.setLayout(QHBoxLayout())
        self.date_selection_widget.layout().addWidget(self.date_dateedit)
        self.date_selection_button = QPushButton('Select date')
        self.date_selection_widget.layout().addWidget(self.date_selection_button)

        # Calendar modal window, shown when date_selection_button is clicked.
        self.calendar = QCalendarWidget()
        self.calendar.setWindowModality(Qt.ApplicationModal)

        # Top-level widgets.
        self.setLayout(QFormLayout())
        self.layout().addRow('Race Name', self.name_lineedit)
        self.layout().addRow('Race Date', self.date_selection_widget)
        self.layout().itemAt(self.layout().rowCount() - 1,
                             QFormLayout.LabelRole).setAlignment(Qt.AlignCenter)
        self.layout().addRow('Notes', self.notes_plaintextedit)

        # Signals/slots plumbing.
        race_table_model.dataChanged.connect(self.dataChanged)
        self.name_lineedit.editingFinished.connect(self.name_editing_finished)
        self.date_dateedit.editingFinished.connect(self.date_editing_finished)
        self.date_selection_button.clicked.connect(self.date_selection_start)
        self.calendar.clicked.connect(self.date_selection_finished)

    def dataChanged(self, top_left, bottom_right, roles): #pylint: disable=invalid-name
        """Respond to a RaceTableModel data change by updating input widgets with current values."""
        del top_left, bottom_right, roles

        race_table_model = self.modeldb.race_table_model

        self.name_lineedit.setText(race_table_model.get_race_property(RaceTableModel.NAME))
        date_string = race_table_model.get_race_property(RaceTableModel.DATE)
        self.date_dateedit.setDate(QDate.fromString(date_string))

        # The QPlainTextEdit really wants a QPlainTextDocumentLayout as its
        # document layout. If we don't set this up, by default the document
        # has a QAbstractTextDocumentLayout, which seems to work, but makes
        # QPlainTextEdit emit a warning. How a supposed abstract class actually
        # got instantiated is a mystery to me.
        document = QTextDocument(race_table_model.get_race_property(RaceTableModel.NOTES))
        document.setDocumentLayout(QPlainTextDocumentLayout(document))
        self.notes_plaintextedit.setDocument(document)

    def name_editing_finished(self):
        """Commit race name edit to the model."""
        race_table_model = self.modeldb.race_table_model
        race_table_model.set_race_property(RaceTableModel.NAME, self.name_lineedit.text())

    def date_editing_finished(self):
        """Commit race date edit to the model."""
        race_table_model = self.modeldb.race_table_model
        race_table_model.set_race_property(RaceTableModel.DATE, self.date_dateedit.text())

    def date_selection_start(self):
        """Show the calendar date selection widget."""
        self.calendar.show()

    def date_selection_finished(self, date):
        """Commit the calendar date selection to the model."""
        self.calendar.hide()
        self.date_dateedit.setDate(date)
        self.date_editing_finished()

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Commit the race notes to the model.

        The QPlainTextEdit widget is a pain in the ass.  The only notification
        signal we can get out of it is textChanged, and that gets emitted on
        every single edit, down to the character.  What's worse is, sending the
        change to the model causes the model to emit dataChanged, which causes
        us to update, which results in firing off another textChanged...
        """
        race_table_model = self.modeldb.race_table_model
        race_table_model.set_race_property(RaceTableModel.NOTES,
                                         self.notes_plaintextedit.document().toPlainText())

        super().hideEvent(event)

class Builder(QTabWidget):
    """Top-level Builder widget

    This widget encapsulates all of the subtasks needed to set up a race.
    """

    def __init__(self, modeldb, parent=None):
        """Initialize the Builder instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.setWindowTitle('Builder')

        racer_setup = RacerSetup(self.modeldb)
        start_time_setup = StartTimeSetup(self.modeldb)
        field_setup = FieldSetup(self.modeldb)
        race_info = RaceInfo(self.modeldb)

        self.addTab(racer_setup, 'Racer Setup')
        self.addTab(start_time_setup, 'Start Time Setup')
        self.addTab(field_setup, 'Field Setup')
        self.addTab(race_info, 'Race Info')

        self.read_settings()

    def keyPressEvent(self, event): #pylint: disable=invalid-name
        """Handle key press."""
        if event.key() == Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)

    def showEvent(self, event): #pylint: disable=invalid-name
        """Handle show event."""
        self.currentWidget().setVisible(True)
        super().showEvent(event)

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Handle hide event."""
        self.currentWidget().setVisible(False)
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
