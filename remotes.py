from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from random import random
import requests
import sys

def enum(**enums):
    return type('Enum', (), enums)

Status = enum(
    Ok = 0,
    Rejected = 1,
    TimedOut = 2,
)

def get_remote_class_list():
    remote_subclass_list = Remote.__subclasses__()

    remote_class_list = []

    for remote_subclass in remote_subclass_list:
        if hasattr(remote_subclass, 'name'):
            remote_class_list.append(remote_subclass)

    return remote_class_list

def get_remote_class_from_string(class_string):
    return getattr(sys.modules[__name__], class_string)

class Remote(QObject):
    last_status = Status.Ok

    def __init__(self, modeldb):
        super().__init__()

        self.modeldb = modeldb

    def connect(self, parent):
        return self.setStatus(Status.Rejected)

    def disconnect(self, parent):
        pass

    def submit_racer_update(self):
        return self.setStatus(Status.Rejected)

    def setStatus(self, status):
        if status != self.last_status:
            self.last_status = status
            self.last_status_changed.emit(self.last_status)

        return status

    last_status_changed = pyqtSignal(int)

class SimulatedRemote(Remote):
    name = 'Simulated Remote'
    failure_rate = 0.9
    interval_ms = 1000 # 1 second

    USERNAME = 'username'

    def connect(self, parent):
        dialog = QDialog(parent=parent)
        dialog.setWindowModality(Qt.ApplicationModal)

        username_lineedit = QLineEdit()
        username = self.modeldb.race_table_model.getRaceProperty(self.USERNAME)
        if username:
            username_lineedit.setText(username)

        password_lineedit = QLineEdit()
        password_lineedit.setEchoMode(QLineEdit.Password)

        form_widget = QWidget()
        form_widget.setLayout(QFormLayout())
        form_widget.layout().addRow('Username', username_lineedit)
        form_widget.layout().addRow('Password', password_lineedit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel);
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        dialog.setLayout(QVBoxLayout())
        dialog.layout().addWidget(form_widget)
        dialog.layout().addWidget(button_box)

        if username:
            password_lineedit.setFocus()
        else:
            username_lineedit.setFocus()

        if dialog.exec() == QDialog.Rejected:
            return self.setStatus(Status.Rejected)

        username = username_lineedit.text()
        password = password_lineedit.text()

        if username != 'simulated' or password != 'remote':
            self.modeldb.race_table_model.deleteRaceProperty(self.USERNAME)

            QMessageBox.warning(parent, 'Error', 'Username or password is incorrect.')
            return self.setStatus(Status.Rejected)

        self.modeldb.race_table_model.setRaceProperty(self.USERNAME, username)

        # Start our update timer.
        self.remote_timer = QTimer(self)
        self.remote_timer.timeout.connect(self.remoteUpdate)
        self.remote_timer.start(self.interval_ms)

        QMessageBox.information(parent, 'Setup Complete', 'Simulated Remote set up successfully.')
        return self.setStatus(Status.Ok)

    def disconnect(self, parent):
        self.modeldb.race_table_model.deleteRaceProperty(self.USERNAME)

        # Stop update timer.
        self.remote_timer.stop()
        self.remote_timer = None

        QMessageBox.information(parent, 'Disconnected', 'Simulated Remote disconnected successfully.')

    # Expects a list of dictionaries each with "bib", "start", and "finish" keys.
    def submit_racer_update(self, update_list):
        if random() > self.failure_rate:
            self.submit_success(update_list)
            return self.setStatus(Status.Ok)
        else:
            self.submit_failure(update_list)
            return self.setStatus(Status.TimedOut)

    def submit_success(self, update_list):
        print('Submit SUCCESS:')
        for update in update_list:
            print('    bib = %s, start = %s, finish = %s' %
                  (update['bib'], update['start'], update['finish']))

    def submit_failure(self, update_list):
        print('Submit FAILURE:')
        for update in update_list:
            print('    bib = %s, start = %s, finish = %s' %
                  (update['bib'], update['start'], update['finish']))

    # Iterate through all racers and push local updates to remote.
    def remoteUpdate(self):
        racer_table_model = self.modeldb.racer_table_model
        submit_list = []

        # First, gather the list of updates and try pushing to remote.
        for row in range(racer_table_model.rowCount()):
            record = racer_table_model.record(row)

            bib = record.value(racer_table_model.BIB)
            start = record.value(racer_table_model.START)
            finish = record.value(racer_table_model.FINISH)
            status = record.value(racer_table_model.STATUS)

            if start and finish and (status != 'remote'):
                racer_update = {'bib': bib,
                                'start': start,
                                'finish': finish,
                                'row': row}

                submit_list.append(racer_update)

        # Only if remote push succeeds, we mark the status as "remote".
        if not submit_list or self.submit_racer_update(submit_list) != Status.Ok:
            return

        for racer_update in submit_list:
            index = racer_table_model.index(racer_update['row'], racer_table_model.fieldIndex(racer_table_model.STATUS))
            racer_table_model.setData(index, 'remote')
            racer_table_model.dataChanged.emit(index, index)

class OnTheDayRemote(Remote):
    name = 'OnTheDay.net Remote'
