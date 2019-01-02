#!/usr/bin/env python3

"""RaceBuilder Qt Classes

This module implements Qt Widgets that have to do with setting up a race, or
adding and configuring components of a race, such as racers and fields.
"""

from PyQt5.QtCore import QDate, QDateTime, QModelIndex, QRegExp, QSettings, QTime, Qt, pyqtSignal
from PyQt5.QtGui import QRegExpValidator, QValidator
from PyQt5.QtWidgets import QComboBox, QDialog, QLabel, QLineEdit, QPlainTextEdit, QPushButton, \
                            QRadioButton, QWidget
from PyQt5.QtWidgets import QDateEdit, QDateTimeEdit, QTimeEdit
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QButtonGroup, QGroupBox, QTabWidget
from PyQt5.QtWidgets import QCompleter, QMessageBox
import common
import defaults
from racemodel import RaceTableModel, InputError

__copyright__ = '''
    Copyright (C) 2018-2019 Andrew Chew

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

class RacerSetup(QWidget):
    """Racer Setup

    This widget allows the user to add racers.
    """

    def __init__(self, modeldb, parent=None):
        """Initialize the RacerSetup instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        racer_table_model = self.modeldb.racer_table_model
        racer_team_column = racer_table_model.team_column

        field_table_model = self.modeldb.field_table_model
        field_name_column = field_table_model.name_column

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

        racer_information_form_widget = QWidget()
        racer_information_form_widget.setLayout(QFormLayout())
        racer_information_form_widget.layout().addRow('First name', self.first_name_lineedit)
        racer_information_form_widget.layout().addRow('Last name', self.last_name_lineedit)
        racer_information_form_widget.layout().addRow('Team', self.team_lineedit)
        racer_information_form_widget.layout().addRow('Category', self.category_lineedit)
        racer_information_form_widget.layout().addRow('Age', self.age_lineedit)
        racer_information_form_widget.layout().addRow('Field', self.field_combobox)
        racer_information_form_widget.layout().addRow('Bib', self.bib_lineedit)

        confirm_button = QPushButton('Add Racer')

        # Top-level widgets.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(racer_information_form_widget)
        self.layout().addWidget(confirm_button)

        # Signals/slots plumbing.
        confirm_button.clicked.connect(self.handle_add_racer)

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
        if not field:
            QMessageBox.warning(self, 'Error', 'Missing field.')
            return
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
        field_name_column = field_table_model.name_column

        # Scope selection (whole race vs a field).
        field_selection_widget = QGroupBox('Set up start times for:')

        scope_button_group = QButtonGroup()
        self.all_fields_radiobutton = QRadioButton('Entire race')
        self.all_fields_radiobutton.setChecked(True)
        scope_button_group.addButton(self.all_fields_radiobutton)
        self.selected_field_radiobutton = QRadioButton('A single field:')
        scope_button_group.addButton(self.selected_field_radiobutton)

        self.selected_field_combobox = QComboBox()
        self.selected_field_combobox.setModel(field_table_model)
        self.selected_field_combobox.setModelColumn(field_name_column)
        self.selected_field_combobox.setEnabled(False)

        field_selection_widget.setLayout(QHBoxLayout())
        field_selection_widget.layout().addWidget(self.all_fields_radiobutton)
        field_selection_widget.layout().addWidget(self.selected_field_radiobutton)
        field_selection_widget.layout().addWidget(self.selected_field_combobox)

        # Start time.
        start_time_widget = QGroupBox('Start time:')

        start_time_button_group = QButtonGroup()
        self.start_time_now_radiobutton = QRadioButton('Now')
        self.start_time_now_radiobutton.setChecked(True)
        start_time_button_group.addButton(self.start_time_now_radiobutton)
        self.start_time_specified_radiobutton = QRadioButton('At:')
        start_time_button_group.addButton(self.start_time_specified_radiobutton)
        self.start_time_datetimeedit = QDateTimeEdit() # Time "now" set in showEvent()
        self.start_time_datetimeedit.setDisplayFormat(defaults.DATETIME_FORMAT)
        self.start_time_datetimeedit.setEnabled(False)

        start_time_widget.setLayout(QHBoxLayout())
        start_time_widget.layout().addWidget(self.start_time_now_radiobutton)
        start_time_widget.layout().addWidget(self.start_time_specified_radiobutton)
        start_time_widget.layout().addWidget(self.start_time_datetimeedit)

        # Start time interval.
        interval_widget = QGroupBox('Interval:')

        interval_button_group = QButtonGroup()
        self.same_start_time_radiobutton = QRadioButton('Same for all')
        self.same_start_time_radiobutton.setChecked(True)
        interval_button_group.addButton(self.same_start_time_radiobutton)
        self.interval_start_time_radiobutton = QRadioButton('Use interval:')
        interval_button_group.addButton(self.interval_start_time_radiobutton)

        self.interval_lineedit = QLineEdit()
        self.interval_lineedit.setText(str(defaults.START_TIME_INTERVAL_SECS))
        self.interval_lineedit.setValidator(QRegExpValidator(QRegExp('[1-9][0-9]*')))
        interval_lineedit_group = QWidget()
        interval_lineedit_group.setLayout(QHBoxLayout())
        interval_lineedit_group.layout().addWidget(self.interval_lineedit)
        interval_lineedit_group.layout().addWidget(QLabel('secs'))
        interval_lineedit_group.setEnabled(False)

        interval_widget.setLayout(QHBoxLayout())
        interval_widget.layout().addWidget(self.same_start_time_radiobutton)
        interval_widget.layout().addWidget(self.interval_start_time_radiobutton)
        interval_widget.layout().addWidget(interval_lineedit_group)

        confirm_button = QPushButton('Assign Start Times')

        # Top-level widgets.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(field_selection_widget)
        self.layout().addWidget(start_time_widget)
        self.layout().addWidget(interval_widget)
        self.layout().addWidget(confirm_button)

        # Signals/slots plumbing.
        confirm_button.clicked.connect(self.handle_assign_start_times)
        self.selected_field_radiobutton.toggled.connect(self.selected_field_combobox.setEnabled)
        self.start_time_specified_radiobutton.toggled.connect(self.start_time_datetimeedit
                                                              .setEnabled)
        self.interval_start_time_radiobutton.toggled.connect(interval_lineedit_group
                                                             .setEnabled)

    def handle_assign_start_times(self):
        """Assign the start times, given the contents of the various input widgets."""
        race_table_model = self.modeldb.race_table_model
        racer_table_model = self.modeldb.racer_table_model

        # Validate inputs.
        if not self.interval_lineedit.text().isdigit:
            raise Exception('Invalid interval')

        field = None
        if self.selected_field_radiobutton.isChecked():
            field = self.selected_field_combobox.currentText()

        reference_datetime = race_table_model.get_reference_clock_datetime()
        if self.start_time_now_radiobutton.isChecked():
            start_time = reference_datetime.msecsTo(QDateTime.currentDateTime())
        else:
            start_time = reference_datetime.msecsTo(self.start_time_datetimeedit.dateTime())

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

        start_datetime = reference_datetime.addMSecs(start_time)
        success_message += ' for %s' % start_datetime.toString(Qt.SystemLocaleLongDate)
        if interval:
            success_message += ' at %s secomd intervals' % interval

        success_message += '.'

        QMessageBox.information(self, 'Success', success_message)

    def showEvent(self, event): #pylint: disable=invalid-name
        """Set up input widgets when this widget is shown.

        Basically, this amounts to populating the start time edit box with the current date and
        time, plus some time ahead, rounded to the nearest 5 minutes.
        """
        self.start_time_datetimeedit.setDate(QDate.currentDate())

        now = QTime.currentTime().addSecs(defaults.START_TIME_FROM_NOW_SECS)
        now.setHMS(now.hour(), now.minute() + 5 - now.minute()%5, 0, 0)
        self.start_time_datetimeedit.setTime(now)

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

        field_information_form_widget = QWidget()
        field_information_form_widget.setLayout(QFormLayout())
        field_information_form_widget.layout().addRow('Name', self.name_lineedit)

        confirm_button = QPushButton('Add Field')

        # Top-level widgets.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(field_information_form_widget)
        self.layout().addWidget(confirm_button)

        # Signals/slots plumbing.
        confirm_button.clicked.connect(self.handle_add_field)

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

        # Cache this. We use it so often.
        self.race_table_model = self.modeldb.race_table_model

        self.name_lineedit = QLineEdit()
        self.date_dateedit = QDateEdit()
        self.date_dateedit.setCalendarPopup(True)
        self.notes_plaintextedit = QPlainTextEdit()
        self.notes_plaintextedit.setPlaceholderText(defaults.RACE_NOTES_PLACEHOLDER_TEXT)
        self.dataChanged(QModelIndex(), QModelIndex(), [Qt.DisplayRole])

        # Top-level widgets.
        self.setLayout(QFormLayout())
        self.layout().addRow('Race Name', self.name_lineedit)
        self.layout().addRow('Race Date', self.date_dateedit)
        self.layout().itemAt(self.layout().rowCount() - 1,
                             QFormLayout.LabelRole).setAlignment(Qt.AlignCenter)
        self.layout().addRow('Notes', self.notes_plaintextedit)

        # Signals/slots plumbing.
        self.race_table_model.dataChanged.connect(self.dataChanged)
        self.name_lineedit.editingFinished.connect(self.name_editing_finished)
        self.date_dateedit.editingFinished.connect(self.date_editing_finished)

    def dataChanged(self, top_left, bottom_right, roles): #pylint: disable=invalid-name
        """Respond to a RaceTableModel data change by updating input widgets with current values."""
        del top_left, bottom_right, roles

        self.name_lineedit.setText(self.race_table_model.get_race_property(RaceTableModel.NAME))
        self.date_dateedit.setDate(self.race_table_model.get_date())

        # The QPlainTextEdit really wants a QPlainTextDocumentLayout as its
        # document layout. If we don't set this up, by default the document
        # has a QAbstractTextDocumentLayout, which seems to work, but makes
        # QPlainTextEdit emit a warning. How a supposed abstract class actually
        # got instantiated is a mystery to me.
        self.notes_plaintextedit.setDocument(self.race_table_model.get_notes())

    def name_editing_finished(self):
        """Commit race name edit to the model."""
        self.race_table_model.set_race_property(RaceTableModel.NAME, self.name_lineedit.text())

    def date_editing_finished(self):
        """Commit race date edit to the model."""
        self.race_table_model.set_date(self.date_dateedit.date())

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Commit the race notes to the model.

        The QPlainTextEdit widget is a pain in the ass.  The only notification
        signal we can get out of it is textChanged, and that gets emitted on
        every single edit, down to the character.  What's worse is, sending the
        change to the model causes the model to emit dataChanged, which causes
        us to update, which results in firing off another textChanged...
        """
        self.race_table_model.set_notes(self.notes_plaintextedit.document())

        super().hideEvent(event)

class TimeSynchronizer(QDialog):
    """Time synchronization widget.

    Make this widget look all big and important, but really, it's just an indirect way of getting
    a reference clock time (the more straightforward way being to just enter one in the text input).

    However, this widget comes in most useful when synchronizing the reference clock with race
    officials. When they press start, we press start/hit enter on this widget. We then use that
    moment in time as our reference clock time.
    """

    TIME_POINT_SIZE = 24
    BUTTON_POINT_SIZE = 54

    def __init__(self, parent=None):
        """Initialize the TimeSynchronizer instance."""
        super().__init__(parent=parent)

        self.instruction_label = QLabel('Adjust desired synchronization time and press '
                                        '"Sync" button to set reference clock time.')
        self.instruction_label.setWordWrap(True)

        self.time_timeedit = QTimeEdit()
        self.time_timeedit.setDisplayFormat(defaults.DATETIME_FORMAT)
        font = self.time_timeedit.font()
        font.setPointSize(self.TIME_POINT_SIZE)
        self.time_timeedit.setFont(font)

        self.sync_button = QPushButton('Sync')
        font = self.sync_button.font()
        font.setPointSize(self.BUTTON_POINT_SIZE)
        self.sync_button.setFont(font)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.instruction_label)
        self.layout().addWidget(self.time_timeedit)
        self.layout().addWidget(self.sync_button)

        self.sync_button.clicked.connect(self.handle_clicked)

    def show(self):
        """Show the TimeSynchronizer.

        Initialize the time to zero.
        """
        self.read_settings()
        self.time_timeedit.setTime(QTime(0, 0))
        super().show()

    def hide(self):
        """Save geometry settings."""
        super().hide()
        self.write_settings()

    def handle_clicked(self):
        """Handler for sync button click."""
        reference_time = self.time_timeedit.time()
        current_time = QTime.currentTime()
        reference_clock_time = current_time.addMSecs(-reference_time.msecsSinceStartOfDay())

        self.clicked.emit(reference_clock_time)

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

    clicked = pyqtSignal(QTime)

class ReferenceClock(QWidget):
    """Race Info Setup

    This widget allows the user to name the race, and jot down various notes about the race.
    """

    REFERENCE_CLOCK_POINT_SIZE = 24

    def __init__(self, modeldb, parent=None):
        """Initialize the ReferenceClock instance."""
        super().__init__(parent=parent)

        self.modeldb = modeldb

        # Cache this. We use it so often.
        self.race_table_model = self.modeldb.race_table_model

        # Time selection/synchronization modal window, shown when synchronize_button is clicked.
        self.time_synchronizer = TimeSynchronizer()
        self.time_synchronizer.setWindowModality(Qt.ApplicationModal)

        # There are some widgets we want to access outside of initialization, so we save them off
        # into "self". However, pylint is getting confused and thinks some of them are possibly
        # never initialized. Therefore, initialize every widget that we want to save to "None" here.
        # (Initialization will take care of giving them proper values after this.)
        self.reference_clock_radiobutton = None
        self.reference_datetime_label = None
        self.datetime_datetimeedit = None

        # Initialize our whole hierarchical mess of widgets.
        self.init_clock_selection_widget()

        # Force update widget contents.
        self.dataChanged(QModelIndex(), QModelIndex(), [Qt.DisplayRole])

        # Signals/slots plumbing.
        self.race_table_model.dataChanged.connect(self.dataChanged)

    def init_clock_selection_widget(self):
        """Initialize the clock selection stuff.

        This method initializes the clock selection radio buttons, and triggers the initialization
        of the reference clock selection stage.

        There are two choices at this level: wall clock and reference clocks.
        """
        # Clock selection (wall clock vs reference clock).
        clock_selection_widget = QGroupBox('Use clock:')

        # Chooser radio buttons and the button group.
        wall_clock_radiobutton = QRadioButton('Wall clock')
        self.reference_clock_radiobutton = QRadioButton('Reference clock')
        clock_source_button_group = QButtonGroup()
        clock_source_button_group.addButton(wall_clock_radiobutton)
        clock_source_button_group.addButton(self.reference_clock_radiobutton)
        clock_selection_widget.setLayout(QHBoxLayout())
        clock_selection_widget.layout().addWidget(wall_clock_radiobutton)
        clock_selection_widget.layout().addWidget(self.reference_clock_radiobutton)

        # The latter choice, that expands to more choices.
        reference_clock_setup_widget = self.init_reference_clock_setup_widget()

        # Top-level widgets.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(clock_selection_widget)
        self.layout().addWidget(reference_clock_setup_widget)

        # Signals/slots plumbing.
        self.reference_clock_radiobutton.toggled.connect(reference_clock_setup_widget.setEnabled)
        self.reference_clock_radiobutton.toggled.connect(self.toggle_reference_clock_setup)

        # Set default state.
        wall_clock_radiobutton.click()
        reference_clock_setup_widget.setEnabled(False)

    def init_reference_clock_setup_widget(self):
        """Initialize the reference clock selection stuff.

        This method initializes the reference clock selection radio buttons, and triggers the
        initialization of the manual reference clock setup stage.

        There are two choices at this level: synchronize and manual setup.
        """
        # Reference clock selection (synchronize vs manual setup).
        reference_clock_selection_widget = QGroupBox('Reference clock setup:')

        # Big text label showing the currently set up reference clock.
        self.reference_datetime_label = QLabel('PLACEHOLDER')
        self.reference_datetime_label.setAlignment(Qt.AlignCenter)
        font = self.reference_datetime_label.font()
        font.setPointSize(self.REFERENCE_CLOCK_POINT_SIZE)
        self.reference_datetime_label.setFont(font)

        # Chooser radio buttons and the button group.
        synchronize_radiobutton = QRadioButton('Synchronize')
        synchronize_radiobutton.setChecked(True)
        synchronize_button = QPushButton('Synchronize')
        manual_setup_radiobutton = QRadioButton('Manual setup')
        reference_clock_setup_button_group = QButtonGroup()
        reference_clock_setup_button_group.addButton(synchronize_radiobutton)
        reference_clock_setup_button_group.addButton(manual_setup_radiobutton)
        reference_clock_selection_row_widget = QWidget()
        reference_clock_selection_row_widget.setLayout(QHBoxLayout())
        reference_clock_selection_row_widget.layout().addWidget(synchronize_radiobutton)
        reference_clock_selection_row_widget.layout().addWidget(synchronize_button)
        reference_clock_selection_row_widget.layout().addWidget(manual_setup_radiobutton)

        reference_clock_selection_widget.setLayout(QVBoxLayout())
        reference_clock_selection_widget.layout().addWidget(self.reference_datetime_label)
        reference_clock_selection_widget.layout().addWidget(reference_clock_selection_row_widget)

        # The latter choice, that expands to more choices.
        reference_clock_manual_setup_widget = self.init_reference_clock_manual_setup_widget()

        # Top-level widgets.
        reference_clock_setup_widget = QWidget()
        reference_clock_setup_widget.setLayout(QVBoxLayout())
        reference_clock_setup_widget.layout().addWidget(reference_clock_selection_widget)
        reference_clock_setup_widget.layout().addWidget(reference_clock_manual_setup_widget)

        # Signals/slots plumbing.
        synchronize_radiobutton.toggled.connect(synchronize_button.setEnabled)
        manual_setup_radiobutton.toggled.connect(reference_clock_manual_setup_widget.setEnabled)
        synchronize_button.clicked.connect(self.time_synchronizer.show)
        self.time_synchronizer.clicked.connect(self.handle_time_synchronizer_done)

        # Set default state.
        synchronize_radiobutton.click()
        reference_clock_manual_setup_widget.setEnabled(False)

        return reference_clock_setup_widget

    def init_reference_clock_manual_setup_widget(self):
        """Initialize the manual reference clock setup stuff.

        This method initializes the manual reference clock setup stuff.
        """
        # Reference clock manual setup widget.
        reference_clock_maual_selection_widget = QGroupBox('Reference clock manual setup:')

        self.datetime_datetimeedit = QDateTimeEdit()
        self.datetime_datetimeedit.setDisplayFormat('yyyy-MM-dd @ h:mm:ss.zzz')
        self.datetime_datetimeedit.setCalendarPopup(True)
        date_today_button = QPushButton('Today')

        date_selection_widget = QWidget()
        date_selection_widget.setLayout(QHBoxLayout())
        date_selection_widget.layout().addWidget(self.datetime_datetimeedit)
        date_selection_widget.layout().addWidget(date_today_button)

        set_reference_clock_button = QPushButton('Set Reference Clock')

        # Top-level widgets.
        reference_clock_maual_selection_widget.setLayout(QVBoxLayout())
        reference_clock_maual_selection_widget.layout().addWidget(date_selection_widget)
        reference_clock_maual_selection_widget.layout().addWidget(set_reference_clock_button)

        # Signals/slots plumbing.
        date_today_button.clicked.connect(
            lambda: self.datetime_datetimeedit.setDateTime(QDateTime(QDate.currentDate())))
        set_reference_clock_button.clicked.connect(self.handle_manual_reference_clock_setup_done)

        return reference_clock_maual_selection_widget

    def dataChanged(self, top_left, bottom_right, roles): #pylint: disable=invalid-name
        """Respond to a RaceTableModel data change by updating input widgets with current values."""
        del top_left, bottom_right, roles

        if self.race_table_model.reference_clock_is_enabled():
            self.reference_clock_radiobutton.click()

        # If there's a reference datetime set up, populate the controls with it.
        if self.race_table_model.reference_clock_has_datetime():
            reference_datetime = self.race_table_model.get_reference_clock_datetime()

            # Make our own combined string, because I haven't found a QDateTime format that I like.
            # Guess I'll keep looking...this looks really hokey.
            datetime_string = reference_datetime.toString(defaults.REFERENCE_CLOCK_DATETIME_FORMAT)

            self.reference_datetime_label.setText(datetime_string)
        else: # Otherwise, just use the race day's date, time zero.
            reference_datetime = QDateTime(QDate.currentDate())

            self.reference_datetime_label.setText('Reference clock not set up')

        self.datetime_datetimeedit.setDateTime(reference_datetime)

    def toggle_reference_clock_setup(self, enable):
        """Toggle reference clock enable/disable.

        Not relevant if there is no reference clock datetime set up.
        """
        if not self.race_table_model.reference_clock_has_datetime():
            return

        old_reference_datetime = self.race_table_model.get_reference_clock_datetime()

        if enable:
            self.race_table_model.enable_reference_clock()
        else:
            self.race_table_model.disable_reference_clock()

        new_reference_datetime = self.race_table_model.get_reference_clock_datetime()
        self.change_reference_datetime(old_reference_datetime, new_reference_datetime)

    def handle_time_synchronizer_done(self, time):
        """Commit the time selection to the model."""
        self.time_synchronizer.hide()

        # When synchronizing, use the current date as the date.
        date = QDate.currentDate()

        old_reference_datetime = self.race_table_model.get_reference_clock_datetime()

        self.race_table_model.set_reference_clock_datetime(QDateTime(date, time))
        self.race_table_model.enable_reference_clock()

        new_reference_datetime = self.race_table_model.get_reference_clock_datetime()
        self.change_reference_datetime(old_reference_datetime, new_reference_datetime)

    def handle_manual_reference_clock_setup_done(self):
        """Commit the reference datetime in the database."""
        old_reference_datetime = self.race_table_model.get_reference_clock_datetime()

        self.race_table_model.set_reference_clock_datetime(self.datetime_datetimeedit.dateTime())
        self.race_table_model.enable_reference_clock()

        new_reference_datetime = self.race_table_model.get_reference_clock_datetime()
        self.change_reference_datetime(old_reference_datetime, new_reference_datetime)

    def change_reference_datetime(self, old_datetime, new_datetime):
        """Applies the new datetime as the reference datetime.

        Note that we also need the old datetime in order to adjust all existing time deltas to
        the new datetime.
        """
        if old_datetime == new_datetime:
            return

        self.race_table_model.change_reference_clock_datetime(old_datetime, new_datetime)

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
        reference_clock = ReferenceClock(self.modeldb)

        self.addTab(racer_setup, 'Racer')
        self.addTab(start_time_setup, 'Start Time')
        self.addTab(field_setup, 'Field')
        self.addTab(race_info, 'Race Info')
        self.addTab(reference_clock, 'Clock')

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
