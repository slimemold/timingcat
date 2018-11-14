#!/usr/bin/env python3

"""Remote Classes

This module contains implementations for the optional remotes that can be used. A remote is a
remote service on which we can push results (typically, racer finishes).
"""

from random import random
#import requests
import sys
from PyQt5.QtCore import QObject, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QMessageBox, QWidget
from PyQt5.QtWidgets import QFormLayout, QVBoxLayout
import common
from racemodel import msecs_is_valid

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

def enum(**enums):
    """Simulate an enum."""
    return type('Enum', (), enums)

Status = enum(
    Ok=0,
    Rejected=1,
    TimedOut=2,
)

def get_remote_class_list():
    """Return a list of remote class types.

    A remote class must be a descendant of class "Remote", and have the "name" attribute.
    """
    remote_subclass_list = Remote.__subclasses__()

    remote_class_list = []

    for remote_subclass in remote_subclass_list:
        if hasattr(remote_subclass, 'name'):
            remote_class_list.append(remote_subclass)

    return remote_class_list

def get_remote_class_from_string(class_string):
    """Return the class type corresponding to the class name."""
    return getattr(sys.modules[__name__], class_string)

class Remote(QObject):
    """Parent class of all remotes."""
    last_status = Status.Ok

    def __init__(self, modeldb):
        """Initialize the Remote instance."""
        super().__init__()

        self.modeldb = modeldb

    def connect(self, parent):
        """Connect to the remote. Return status of the connect operation.

        This base class just succeeds this operation.
        """
        del parent
        return self.setStatus(Status.Ok)

    def disconnect(self, parent):
        """Disconnect from the remote."""
        pass

    def submit_racer_update(self, update_list):
        """Submit a list of racer updates. Return status of the submit operation.

        This base class just succeeds this operation.
        """
        del update_list
        return self.setStatus(Status.Ok)

    def set_status(self, status):
        """Set the last_status.

        Emit the last_status_changed signal if the status is different from the last_status.
        """
        if status != self.last_status:
            self.last_status = status
            self.last_status_changed.emit(self.last_status)

        return status

    last_status_changed = pyqtSignal(int)

class SimulatedRemote(Remote):
    """Simulates a remote by implementing submissions to nowhere, with a simulated failure rate."""
    name = 'Simulated Remote'
    failure_rate = 0.9
    interval_ms = 1000 # 1 second

    USERNAME = 'username'

    def __init__(self, modeldb):
        """Initialize the SimulatedRemote instance."""
        super().__init__(modeldb)

        self.remote_timer = None

    def connect(self, parent):
        dialog = QDialog(parent=parent)
        dialog.setWindowModality(Qt.ApplicationModal)

        username_lineedit = QLineEdit()
        username = self.modeldb.race_table_model.get_race_property(self.USERNAME)
        if username:
            username_lineedit.setText(username)

        password_lineedit = QLineEdit()
        password_lineedit.setEchoMode(QLineEdit.Password)

        form_widget = QWidget()
        form_widget.setLayout(QFormLayout())
        form_widget.layout().addRow('Username', username_lineedit)
        form_widget.layout().addRow('Password', password_lineedit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
            return self.set_status(Status.Rejected)

        username = username_lineedit.text()
        password = password_lineedit.text()

        if username != 'simulated' or password != 'remote':
            self.modeldb.race_table_model.delete_race_property(self.USERNAME)

            QMessageBox.warning(parent, 'Error', 'Username or password is incorrect.')
            return self.set_status(Status.Rejected)

        self.modeldb.race_table_model.set_race_property(self.USERNAME, username)

        # Start our update timer.
        self.remote_timer = QTimer(self)
        self.remote_timer.timeout.connect(self.remote_update)
        self.remote_timer.start(self.interval_ms)

        QMessageBox.information(parent, 'Setup Complete', 'Simulated Remote set up successfully.')
        return self.set_status(Status.Ok)

    def disconnect(self, parent):
        self.modeldb.race_table_model.delete_race_property(self.USERNAME)

        # Stop update timer.
        self.remote_timer.stop()
        self.remote_timer = None

        QMessageBox.information(parent, 'Disconnected',
                                'Simulated Remote disconnected successfully.')

    def submit_racer_update(self, update_list):
        """Submit a list of racer updates.

        Expects a list of dictionaries each with "bib", "start", and "finish" keys.
        """
        if random() > self.failure_rate:
            self.submit_success(update_list)
            status = Status.Ok
        else:
            self.submit_failure(update_list)
            status = Status.TimedOut

        return self.set_status(status)

    def submit_success(self, update_list):
        """Print a diagnostic debug message showing submit success."""
        print('Submit SUCCESS:')
        for update in update_list:
            print('    bib = %s, start = %s, finish = %s' %
                  (update['bib'], update['start'], update['finish']))

    def submit_failure(self, update_list):
        """Print a diagnostic debug message showing submit failure."""
        print('Submit FAILURE:')
        for update in update_list:
            print('    bib = %s, start = %s, finish = %s' %
                  (update['bib'], update['start'], update['finish']))

    def remote_update(self):
        """Iterate through all racers and push local updates to remote."""
        racer_table_model = self.modeldb.racer_table_model
        racer_status_column = racer_table_model.status_column

        submit_list = []

        # First, gather the list of updates and try pushing to remote.
        for row in range(racer_table_model.rowCount()):
            record = racer_table_model.record(row)

            bib = record.value(racer_table_model.BIB)
            start = record.value(racer_table_model.START)
            finish = record.value(racer_table_model.FINISH)
            status = record.value(racer_table_model.STATUS)

            if msecs_is_valid(start) and msecs_is_valid(finish) and (status != 'remote'):
                racer_update = {'bib': bib,
                                'start': start,
                                'finish': finish,
                                'row': row}

                submit_list.append(racer_update)

        # Only if remote push succeeds, we mark the status as "remote".
        if not submit_list or self.submit_racer_update(submit_list) != Status.Ok:
            return

        for racer_update in submit_list:
            index = racer_table_model.index(racer_update['row'], racer_status_column)
            racer_table_model.setData(index, 'remote')
            racer_table_model.dataChanged.emit(index, index)

class OnTheDayRemote(Remote):
    """OnTheDay.net remote, to be implemented."""
    name = 'OnTheDay.net Remote'
