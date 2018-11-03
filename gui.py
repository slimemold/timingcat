import csv
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from common import *
from preferences import PreferencesWindow
from racebuilder import Builder
from racemodel import ModelDatabase
from raceview import FieldTableView, RacerTableView, ResultTableView
from remotes import get_remote_class_list, AuthError
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

    def hasModel(self):
        return False

class StartCentralWidget(QLabel, CentralWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setPixmap(QPixmap(os.path.join('resources', 'thyme.jpg')))

class MainCentralWidget(QWidget, CentralWidget):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

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
        self.updateSubmitButton()

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
                                                       self.fieldModelChanged)

        # Signals/slots for result table.
        self.result_table_view.selectionModel().selectionChanged.connect(
                                                  self.resultSelectionChanged)

        # Signals/slots for result input.
        self.result_input.returnPressed.connect(self.newResult)

        # Signals/slots for submit button.
        self.submit_button.clicked.connect(self.result_table_view.handleSubmit)

    def cleanup(self):
        self.builder.hide()
        self.field_table_view.hide()
        self.racer_table_view.hide()

        self.modeldb.cleanup()
        self.modeldb = None

    def hasModel(self):
        return self.modeldb is not None

    def updateSubmitButton(self):
        if self.result_table_view:
            selection_count = len(self.result_table_view.selectionModel().selectedRows())
            total_count = self.result_table_view.model().rowCount()
        else:
            seletion_count = 0
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

    def fieldModelChanged(self, *args):
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

    def resultSelectionChanged(self, selected, deselected):
        self.updateSubmitButton()

    def newResult(self):
        self.modeldb.result_table_model.addResult(
                               self.result_input.text(), QTime.currentTime())
        self.result_table_view.scrollToBottom()
        self.result_input.clear()

class SexyThymeMainWindow(QMainWindow):
    def __init__(self, filename=None, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.setupMenuBar()

        if filename:
            self.switchToMain(filename)
        else:
            self.switchToStart()

    def switchToStart(self):
        # Clean up old central widget, which will clean up the model we gave it.
        if self.centralWidget():
            self.centralWidget().cleanup()

        self.setCentralWidget(StartCentralWidget())

        self.generate_reports_menu_action.setEnabled(False)
        self.connect_remote_menu.setEnabled(False)
        self.disconnect_remote_menu.setEnabled(False)

    def switchToMain(self, filename, new=False):
        # Clean up old central widget, which will clean up the model we gave it.
        if self.centralWidget():
            self.centralWidget().cleanup()

        # Make a new model, and give it to a new central widget.
        model = ModelDatabase(filename, new)
        self.setCentralWidget(MainCentralWidget(model))

        self.generate_reports_menu_action.setEnabled(True)
        self.connect_remote_menu.setEnabled(True)
        self.disconnect_remote_menu.setEnabled(False)

    def setupMenuBar(self):
        # Make a parent-less menubar, so that Qt can use the top-level native
        # one (like on OS-X and Ubuntu Unity) if available.
        menuBar = QMenuBar()
        self.setMenuBar(menuBar)

        # File menu.
        file_menu = self.menuBar().addMenu('&File');
        file_menu.addAction('New...', self.newFile, QKeySequence.New)
        file_menu.addAction('Open...', self.openFile, QKeySequence.Open)
        file_menu.addAction('Close', self.closeFile, QKeySequence.Close)

        file_menu.addSeparator()

        self.generate_reports_menu_action = file_menu.addAction('Generate reports', self.generateReports)

        file_menu.addSeparator()

        file_menu.addAction('Quit', self.close, QKeySequence.Quit)

        # Config menu.
        config_menu = self.menuBar().addMenu('&Config')
        config_menu.addAction('Preferences', self.configPreferences, QKeySequence.Preferences)
        config_menu.addAction('Race Builder', self.configBuilder)
        config_menu.addAction('Import Bikereg csv...', self.importBikeregFile)

        config_menu.addSeparator()

        self.connect_remote_menu = config_menu.addMenu('Connect Remote')
        remote_class_list = get_remote_class_list()
        for remote_class in remote_class_list:
            receiver = lambda remote_class=remote_class: self.connectRemote(remote_class)
            self.connect_remote_menu.addAction(remote_class.name, receiver)

        self.disconnect_remote_menu = config_menu.addAction('Disconnect Remote', self.disconnectRemote)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.shouldClose():
            # Clean up old central widget, which will clean up the model we gave it.
            if self.centralWidget():
                self.centralWidget().cleanup()

            QApplication.quit()
            event.accept()
        else:
            event.ignore()

    def newFile(self):
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
        self.switchToMain(filename, True)
        self.centralWidget().modeldb.addDefaults()

        return filename

    def openFile(self):
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Race file (*.rce)')
        dialog.setOptions(QFileDialog.DontUseNativeDialog)
        dialog.setViewMode(QFileDialog.List)

        if not dialog.exec():
            return None

        filename = dialog.selectedFiles()[0]
        self.switchToMain(filename, False)
        self.centralWidget().modeldb.addDefaults()

        return filename

    def closeFile(self):
        if self.shouldClose():
            self.switchToStart()

    def importFilePrepare(self):
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
        if not self.centralWidget().hasModel():
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
                self.switchToMain(filename, True)
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
        self.switchToMain(filename, True)

        return import_filename

    def importBikeregFile(self):
        import_filename = self.importFilePrepare()

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

                racer_table_model.addRacer(bib, first_name,last_name, field, category, team, age)

        self.centralWidget().modeldb.addDefaults()

    def generateReports(self):
        dialog = ReportsWindow(self.centralWidget().modeldb, self)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.show()

    def configPreferences(self):
        dialog = PreferencesWindow(self.centralWidget().modeldb, self)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.show()

    def configBuilder(self):
        self.centralWidget().builder.show()

    def connectRemote(self, remote_class):
        try:
            self.remote = remote_class(self.centralWidget().modeldb.race_table_model)
            self.remote.connect(self)
        except AuthError as e:
            QMessageBox.warning(self, 'Error', str(e))

        self.connect_remote_menu.setEnabled(False)
        self.disconnect_remote_menu.setEnabled(True)

    def disconnectRemote(self):
        self.remote.disconnect(self)
        self.remote = None

        self.connect_remote_menu.setEnabled(True)
        self.disconnect_remote_menu.setEnabled(False)

    def shouldClose(self):
        # If there are unsubmitted results, give the user a chance to cancel
        # the quit...not that the user will lose anything, but just as a heads
        # up that there's unfinished business on the part of the user.
        if (self.centralWidget().hasModel() and
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
