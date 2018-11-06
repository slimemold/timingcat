import csv
import os
from PyQt5.QtCore import QObject, QRegExp, QTime, Qt
from PyQt5.QtGui import QKeySequence, QPixmap, QRegExpValidator
from PyQt5.QtWidgets import QLabel, QLineEdit, QMenuBar, QPushButton, QStatusBar, QWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from common import APPLICATION_NAME, pluralize, pretty_list
from preferences import PreferencesWindow
from racebuilder import Builder
from racemodel import DatabaseError, ModelDatabase, RaceTableModel, RacerTableModel
from raceview import FieldTableView, RacerTableView, ResultTableView
import remotes
from reports import ReportsWindow

INPUT_TEXT_POINT_SIZE = 32

# Widget Instance Hierarchy
#
# SexyThymeMainWindow
#     StartCentralWidget
#     MainCentralWidget
#         button_row
#             builder_button
#             field_button
#             racer_button
#         result_table_view
#         result_input
#         submit_button
#     Builder
#     FieldTableView
#     RacerTableView
#     ResultTableView
#.    Preferences
#.    RemoteConfig

class CentralWidget(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def cleanup(self):
        pass

    def has_model(self):
        return False

class StartCentralWidget(QLabel, CentralWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setPixmap(QPixmap(os.path.join('resources', 'thyme.jpg')))

class MainCentralWidget(QWidget, CentralWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.remote = None

        # Top-level layout. Top to bottom.
        self.setLayout(QVBoxLayout())

        # Button row for race info, field, racer list.
        self.button_row = QWidget()
        self.button_row.setLayout(QHBoxLayout())

        # Race Info, Fields, Racers
        self.button_row.field_button = QPushButton('Fields')
        self.button_row.field_button.setCheckable(True)
        self.button_row.racer_button = QPushButton('Racers')
        self.button_row.racer_button.setCheckable(True)

        # Add to button row.
        self.button_row.layout().addWidget(self.button_row.racer_button)
        self.button_row.layout().addWidget(self.button_row.field_button)

        # Result table.
        self.result_table_view = ResultTableView(self.modeldb)

        # Result line edit.
        self.result_input = QLineEdit()
        font = self.result_input.font()
        font.setPointSize(INPUT_TEXT_POINT_SIZE)
        self.result_input.setFont(font)
        self.result_input.setValidator(QRegExpValidator(QRegExp('[A-Za-z0-9]*')))

        # Submit button.
        self.submit_button = QPushButton()
        self.update_submit_button()

        # Add to top-level layout.
        self.layout().addWidget(self.button_row)
        self.layout().addWidget(self.result_table_view)
        self.layout().addWidget(self.result_input)
        self.layout().addWidget(self.submit_button)

        # Floating windows. Keep then hidden initially.
        self.builder = Builder(self.modeldb)
        self.field_table_view = FieldTableView(self.modeldb)
        self.racer_table_view = RacerTableView(self.modeldb)

        # Signals/slots for button row toggle buttons.
        self.button_row.field_button.toggled.connect(self.field_table_view
                                                         .setVisible)
        self.field_table_view.visibleChanged.connect(self.button_row.field_button
                                                         .setChecked)
        self.button_row.racer_button.toggled.connect(self.racer_table_view
                                                         .setVisible)
        self.racer_table_view.visibleChanged.connect(self.button_row.racer_button
                                                         .setChecked)

        # Signals/slots for field name change notification.
        self.modeldb.field_table_model.dataChanged.connect(
                                                       self.field_model_changed)

        # Signals/slots for result table.
        self.result_table_view.selectionModel().selectionChanged.connect(
                                                  self.result_selection_changed)

        # Signals/slots for result input.
        self.result_input.returnPressed.connect(self.new_result)

        # Signals/slots for submit button.
        self.submit_button.clicked.connect(self.result_table_view.handle_submit)

    def cleanup(self):
        self.builder.hide()
        self.field_table_view.hide()
        self.racer_table_view.hide()

        self.modeldb.cleanup()
        self.modeldb = None

    def has_model(self):
        return self.modeldb is not None

    def update_submit_button(self):
        if self.result_table_view:
            selection_count = len(self.result_table_view.selectionModel().selectedRows())
            total_count = self.result_table_view.model().rowCount()
        else:
            selection_count = 0
            total_count = 0

        if selection_count == 0:
            self.submit_button.setText('Submit')
            self.submit_button.setEnabled(False)
        elif selection_count == 1:
            self.submit_button.setText('Submit')
            self.submit_button.setEnabled(True)
        elif selection_count < total_count:
            self.submit_button.setText('Submit Selected')
            self.submit_button.setEnabled(True)
        else:
            self.submit_button.setText('Submit All')
            self.submit_button.setEnabled(True)

    def field_model_changed(self, *args):
        del args

        # TODO: We only care here if field name changes.

        # When someone changes a field name, we have to update the racer model
        # to get the field name change. In addition, there is a combo box
        # in the racer table view that is a view for a relation model inside
        # the racer model. That combo box needs to update as well, to get the
        # field name change.
        racer_table_model = self.modeldb.racer_table_model
        field_relation_model = racer_table_model.relationModel(
                                   racer_table_model.fieldIndex(RacerTableModel.FIELD_ALIAS))

        if not racer_table_model.select():
            raise DatabaseError(racer_table_model.lastError().text())

        if not field_relation_model.select():
            raise DatabaseError(racer_table_model.lastError().text())

    def result_selection_changed(self, selected, deselected):
        del selected, deselected
        self.update_submit_button()

    def new_result(self):
        self.modeldb.result_table_model.add_result(
                               self.result_input.text(), QTime.currentTime())
        self.result_table_view.scrollToBottom()
        self.result_input.clear()

    def set_remote(self, remote):
        self.remote = remote
        self.racer_table_view.set_remote(remote)

class SexyThymeMainWindow(QMainWindow):
    def __init__(self, filename=None, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.setup_menubar()

        self.remote = None

        if filename:
            self.switch_to_main(filename)
        else:
            self.switch_to_start()

    def switch_to_start(self):
        # Clean up old central widget, which will clean up the model we gave it.
        if self.centralWidget():
            self.centralWidget().cleanup()

        self.setCentralWidget(StartCentralWidget())

        self.generate_reports_menu_action.setEnabled(False)
        self.connect_remote_menu.setEnabled(False)
        self.disconnect_remote_menu.setEnabled(False)

    def switch_to_main(self, filename, new=False):
        # Clean up old central widget, which will clean up the model we gave it.
        if self.centralWidget():
            self.centralWidget().cleanup()

        # Make a new model, and give it to a new central widget.
        model = ModelDatabase(filename, new)
        self.setCentralWidget(MainCentralWidget(model))

        self.generate_reports_menu_action.setEnabled(True)

        remote_class_string = model.race_table_model.get_race_property(RaceTableModel.REMOTE_CLASS)
        if remote_class_string:
            self.connect_remote(remotes.get_remote_class_from_string(remote_class_string))
        else:
            self.set_remote(None)

    def setup_menubar(self):
        # Make a parent-less menubar, so that Qt can use the top-level native
        # one (like on OS-X and Ubuntu Unity) if available.
        menubar = QMenuBar()
        self.setMenuBar(menubar)

        # File menu.
        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction('New...', self.new_file, QKeySequence.New)
        file_menu.addAction('Open...', self.open_file, QKeySequence.Open)
        file_menu.addAction('Close', self.close_file, QKeySequence.Close)

        file_menu.addSeparator()

        self.generate_reports_menu_action = file_menu.addAction('Generate reports',
                                                                self.generate_reports)

        file_menu.addSeparator()

        file_menu.addAction('Quit', self.close, QKeySequence.Quit)

        # Config menu.
        config_menu = self.menuBar().addMenu('&Config')
        config_menu.addAction('Preferences', self.config_preferences, QKeySequence.Preferences)
        config_menu.addAction('Race Builder', self.config_builder)
        config_menu.addAction('Import Bikereg csv...', self.import_bikereg_file)

        config_menu.addSeparator()

        self.connect_remote_menu = config_menu.addMenu('Connect Remote')
        remote_class_list = remotes.get_remote_class_list()
        for remote_class in remote_class_list:
            receiver = lambda remote_class=remote_class: self.connect_remote(remote_class)
            self.connect_remote_menu.addAction(remote_class.name, receiver)

        self.disconnect_remote_menu = config_menu.addAction('Disconnect Remote',
                                                            self.disconnect_remote)

    def keyPressEvent(self, event): #pylint: disable=invalid-name
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event): #pylint: disable=invalid-name
        if self.should_close():
            # Clean up old central widget, which will clean up the model we gave it.
            if self.centralWidget():
                self.centralWidget().cleanup()

            QApplication.quit()
            event.accept()
        else:
            event.ignore()

    def new_file(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('rce')
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setLabelText(QFileDialog.Accept, 'New')
        dialog.setNameFilter('Race file (*.rce)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return None

        filename = dialog.selectedFiles()[0]
        self.switch_to_main(filename, True)
        self.centralWidget().modeldb.add_defaults()

        return filename

    def open_file(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Race file (*.rce)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return None

        filename = dialog.selectedFiles()[0]
        self.switch_to_main(filename, False)
        self.centralWidget().modeldb.add_defaults()

        return filename

    def close_file(self):
        if self.should_close():
            self.switch_to_start()

    def import_file_prepare(self):
        # Pick the import file.
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Bikereg file (*.csv)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return None

        import_filename = dialog.selectedFiles()[0]

        # If we are not yet initialized, pick a new race file.
        if not self.centralWidget().has_model():
            dialog = QFileDialog(self)
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setDefaultSuffix('rce')
            dialog.setFileMode(QFileDialog.AnyFile)
            dialog.setLabelText(QFileDialog.Accept, 'New')
            dialog.setNameFilter('Race file (*.rce)')
            dialog.setOptions(QFileDialog.DontUseNativeDialog)
            dialog.setViewMode(QFileDialog.List)

            if dialog.exec():
                filename = dialog.selectedFiles()[0]
                self.switch_to_main(filename, True)
                return import_filename
            else:
                return None

        # Otherwise, if our current race has stuff in it, confirm to overwrite
        # before clearing it.

        # Get Field and Racer tables so we can whine about how much state
        # we're going to lose if we let the import happen.
        field_table_model = self.centralWidget().modeldb.field_table_model
        racer_table_model = self.centralWidget().modeldb.racer_table_model

        if ((field_table_model.rowCount() != 0) or
            (racer_table_model.rowCount() != 0)):
            msg_box = QMessageBox()
            msg_box.setWindowTitle(APPLICATION_NAME)
            msg_box.setText('Overwriting %s' %
                            pretty_list([pluralize('field', field_table_model.rowCount()),
                                         pluralize('racer', racer_table_model.rowCount())]))
            msg_box.setInformativeText('Do you really want to overwrite ' +
                                       'this data?')
            msg_box.setStandardButtons(QMessageBox.Ok |
                                       QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Cancel)
            msg_box.setIcon(QMessageBox.Information)

            if msg_box.exec() != QMessageBox.Ok:
                return None

        # Reuse old filename.
        filename = self.centralWidget().modeldb.filename
        self.switch_to_main(filename, True)

        return import_filename

    def import_bikereg_file(self):
        import_filename = self.import_file_prepare()

        if not import_filename:
            return

        with open(import_filename) as import_file:
            reader = csv.reader(import_file)

            # Skip the heading row.
            next(reader)

            for row in reader:
                age, bib, field, _, first_name, _, last_name, _, team, category, *_ = row

                # BikeReg lists One-day License holders twice, and the second
                # listing is missing the bib#, and instead has:
                # "License - 1/1/2018 - One-day License" as the field. Skip over
                # these entries.
                if 'One-day License' in field:
                    continue

                racer_table_model = self.centralWidget().modeldb.racer_table_model

                racer_table_model.add_racer(bib, first_name, last_name, field, category, team, age)

        self.centralWidget().modeldb.add_defaults()

    def generate_reports(self):
        dialog = ReportsWindow(self.centralWidget().modeldb, self)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.show()

    def config_preferences(self):
        dialog = PreferencesWindow(self.centralWidget().modeldb, self)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.show()

    def config_builder(self):
        self.centralWidget().builder.show()

    def connect_remote(self, remote_class):
        remote = remote_class(self.centralWidget().modeldb)
        # Allow remote setup if okay or timed out (but not rejected).
        if remote.connect(self) == remotes.Status.Rejected:
            remote = None

        self.set_remote(remote)

    def disconnect_remote(self):
        if self.remote:
            self.remote.disconnect(self)
        self.set_remote(None)

    def set_remote(self, remote):
        race_table_model = self.centralWidget().modeldb.race_table_model

        if remote:
            race_table_model.set_race_property(RaceTableModel.REMOTE_CLASS, type(remote).__name__)
            self.connect_remote_menu.setEnabled(False)
            self.disconnect_remote_menu.setEnabled(True)
            self.setStatusBar(QStatusBar())
            remote.last_status_changed.connect(self.remote_status_changed)
            self.remote_status_changed(remote.last_status)
        else:
            race_table_model.delete_race_property(RaceTableModel.REMOTE_CLASS)
            self.connect_remote_menu.setEnabled(True)
            self.disconnect_remote_menu.setEnabled(False)
            if self.remote:
                self.remote.last_status_changed.disconnect(self.remote_status_changed)
            self.setStatusBar(None)

        self.remote = remote
        self.centralWidget().set_remote(remote)

    def remote_status_changed(self, status):
        if status == remotes.Status.Ok:
            self.statusBar().showMessage('Remote: Ok')
        elif status == remotes.Status.TimedOut:
            self.statusBar().showMessage('Remote: Timed Out')
        elif status == remotes.Status.Rejected:
            self.statusBar().showMessage('Remote: Rejected')
        else:
            self.statusBar().showMessage('Remote: Unknown State')

    def should_close(self):
        # If there are unsubmitted results, give the user a chance to cancel
        # the quit...not that the user will lose anything, but just as a heads
        # up that there's unfinished business on the part of the user.
        if (self.centralWidget().has_model() and
            (self.centralWidget().result_table_view.model().rowCount() != 0)):
            msg_box = QMessageBox()
            msg_box.setWindowTitle(APPLICATION_NAME)
            msg_box.setText('You have unsubmitted results.')
            msg_box.setInformativeText('Do you really want to quit?')
            msg_box.setStandardButtons(QMessageBox.Ok |
                                       QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Cancel)
            msg_box.setIcon(QMessageBox.Information)

            return msg_box.exec() == QMessageBox.Ok

        return True
