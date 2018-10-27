from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from common import *
import defaults
from racemodel import *

class RacerSetup(QWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        # Racer Information form.
        self.name_lineedit = QLineEdit()
        self.team_lineedit = QLineEdit()
        self.team_lineedit.setCompleter(QCompleter(self.modeldb.racer_table_model))
        self.team_lineedit.completer().setCompletionColumn(self.modeldb.racer_table_model.fieldIndex(RacerTableModel.TEAM))
        self.field_combobox = QComboBox()
        self.field_combobox.setModel(self.modeldb.field_table_model)
        self.field_combobox.setModelColumn(self.modeldb.field_table_model.fieldIndex(FieldTableModel.NAME))
        self.bib_lineedit = QLineEdit()
        self.bib_lineedit.setValidator(QRegExpValidator(QRegExp('[0-9]+')))

        self.racer_information_form_widget = QWidget()
        self.racer_information_form_widget.setLayout(QFormLayout())
        self.racer_information_form_widget.layout().addRow('Name', self.name_lineedit)
        self.racer_information_form_widget.layout().addRow('Team', self.team_lineedit)
        self.racer_information_form_widget.layout().addRow('Field', self.field_combobox)
        self.racer_information_form_widget.layout().addRow('Bib', self.bib_lineedit)

        self.confirm_button = QPushButton('Add Racer')

        # Top-level widgets.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.racer_information_form_widget)
        self.layout().addWidget(self.confirm_button)

        # Signals/slots plumbing.
        self.confirm_button.clicked.connect(self.handleAddRacer)

    def reset(self):
        self.bib_lineedit.setText('')
        self.name_lineedit.setText('')
        self.team_lineedit.setText('')

    def handleAddRacer(self):
        try:
            self.modeldb.racer_table_model.addRacer(self.bib_lineedit.text(),
                                                    self.name_lineedit.text(),
                                                    self.team_lineedit.text(),
                                                    self.field_combobox.currentText())
            self.reset()

        except InputError as e:
            QMessageBox.warning(self, 'Error', str(e))

class StartTimeSetup(QWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        # Scope selection (whole race vs a field).
        self.field_selection_widget = QGroupBox('Set up start times for:')

        self.scope_button_group = QButtonGroup()
        self.all_fields_radiobutton = QRadioButton('Entire race')
        self.all_fields_radiobutton.setChecked(True)
        self.scope_button_group.addButton(self.all_fields_radiobutton)
        self.selected_field_radiobutton = QRadioButton('A single field:')
        self.scope_button_group.addButton(self.selected_field_radiobutton)

        self.selected_field_combobox = QComboBox()
        self.selected_field_combobox.setModel(self.modeldb.field_table_model)
        self.selected_field_combobox.setModelColumn(self.modeldb.field_table_model.fieldIndex(self.modeldb.field_table_model.NAME))
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
        self.confirm_button.clicked.connect(self.handleAssignStartTimes)
        self.selected_field_radiobutton.toggled.connect(self.selected_field_combobox.setEnabled)
        self.start_time_specified_radiobutton.toggled.connect(self.start_time_timeedit.setEnabled)
        self.interval_start_time_radiobutton.toggled.connect(self.interval_lineedit_group.setEnabled)

    def handleAssignStartTimes(self):
        # Validate inputs.
        if not self.interval_lineedit.text().isdigit:
            raise

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
            starts_overwritten = self.modeldb.racer_table_model.assignStartTimes(field, start_time, interval, True)
            if starts_overwritten > 0:
                QMessageBox.question(self, 'Question', 'About to overwrite %s existing start times. Proceed anyway?' % starts_overwritten)
            self.modeldb.racer_table_model.assignStartTimes(field, start_time, interval)
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

    def showEvent(self, event):
        now = QTime.currentTime().addSecs(defaults.START_TIME_FROM_NOW_SECS)
        now.setHMS(now.hour(), now.minute() + 5 - now.minute()%5, 0, 0)
        self.start_time_timeedit.setTime(now)

        super().showEvent(event)

class FieldSetup(QWidget):
    def __init__(self, modeldb, parent=None):
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
        self.confirm_button.clicked.connect(self.handleAddField)

    def reset(self):
        self.name_lineedit.setText('')

    def handleAddField(self):
        try:
            self.modeldb.field_table_model.addField(self.name_lineedit.text())
            self.reset()

        except InputError as e:
            QMessageBox.warning(self, 'Error', str(e))

class RaceInfo(QWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.name_lineedit = QLineEdit()
        self.date_dateedit = QDateEdit()
        self.notes_plaintextedit = QPlainTextEdit()
        self.notes_plaintextedit.setPlaceholderText(defaults.RACE_NOTES_PLACEHOLDER_TEXT)
        self.dataChanged()

        self.date_selection_widget = QWidget()
        self.date_selection_widget.setLayout(QHBoxLayout())
        self.date_selection_widget.layout().addWidget(self.date_dateedit)
        self.date_selection_button = QPushButton('Select date')
        self.date_selection_widget.layout().addWidget(self.date_selection_button)

        # Top-level widgets.
        self.setLayout(QFormLayout())
        self.layout().addRow('Race Name', self.name_lineedit)
        self.layout().addRow('Race Date', self.date_selection_widget)
        self.layout().itemAt(self.layout().rowCount()-1, QFormLayout.LabelRole).setAlignment(Qt.AlignCenter)
        self.layout().addRow('Notes', self.notes_plaintextedit)

        # Signals/slots plumbing.
        self.modeldb.race_table_model.dataChanged.connect(self.dataChanged)
        self.name_lineedit.editingFinished.connect(self.nameEditingFinished)
        self.date_dateedit.editingFinished.connect(self.dateEditingFinished)

    def dataChanged(self, top_left=QModelIndex(), bottom_right=QModelIndex(), rolesi=[]):
        self.name_lineedit.setText(self.modeldb.race_table_model.getRaceProperty(RaceTableModel.NAME))
        self.date_dateedit.setDate(QDate.fromString(self.modeldb.race_table_model.getRaceProperty(RaceTableModel.DATE)))

        # The QPlainTextEdit really wants a QPlainTextDocumentLayout as its
        # document layout. If we don't set this up, by default the document
        # has a QAbstractTextDocumentLayout, which seems to work, but makes
        # QPlainTextEdit emit a warning. How a supposed abstract class actually
        # got instantiated is a mystery to me.
        document = QTextDocument(self.modeldb.race_table_model.getRaceProperty(RaceTableModel.NOTES))
        document.setDocumentLayout(QPlainTextDocumentLayout(document))
        self.notes_plaintextedit.setDocument(document)

    def nameEditingFinished(self):
        self.modeldb.race_table_model.setRaceProperty(RaceTableModel.NAME, self.name_lineedit.text())

    def dateEditingFinished(self):
        self.modeldb.race_table_model.setRaceProperty(RaceTableModel.DATE, self.date_dateedit.text())

    # The QPlainTextEdit widget is a pain in the ass.  The only notification
    # signal we can get out of it is textChanged, and that gets emitted on
    # every single edit, down to the character.  What's worse is, sending the
    # change to the model causes the model to emit dataChanged, which causes
    # us to update, which results in firing off another textChanged...
    def hideEvent(self, event):
        self.modeldb.race_table_model.setRaceProperty(RaceTableModel.NOTES, self.notes_plaintextedit.document().toPlainText())

        super().hideEvent(event)

class Builder(QTabWidget):
    def __init__(self, modeldb, parent=None):
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)

    def showEvent(self, event):
        self.currentWidget().setVisible(True)

        self.visibleChanged.emit(True)

    def hideEvent(self, event):
        self.currentWidget().setVisible(False)

        self.visibleChanged.emit(False)

    # Signals.
    visibleChanged = pyqtSignal(bool)
