#!/usr/bin/env python3

"""Remote Classes

This module contains implementations for the optional remotes that can be used. A remote is a
remote service on which we can push results (typically, racer finishes).
"""

import json
from random import random
import sys
import threading
import time
from PyQt5.QtCore import QDateTime, QDate, QObject, QSettings, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QMessageBox, QWidget
from PyQt5.QtWidgets import QFormLayout, QVBoxLayout
import keyring
import requests
import common
import ontheday
from racemodel import InputError, Journal, msecs_is_valid, MSECS_DNF, MSECS_DNP

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

Status = common.enum(
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

    def __init__(self, modeldb):
        """Initialize the Remote instance."""
        super().__init__()

        self.modeldb = modeldb
        self.last_status = Status.Ok

    def connect(self, parent):
        """Connect to the remote. Return status of the connect operation.

        This base class just succeeds this operation.
        """
        del parent
        return self.setStatus(Status.Ok)

    def disconnect(self, parent):
        """Disconnect from the remote."""

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
        race_table_model = self.modeldb.race_table_model

        dialog = QDialog(parent=parent)
        dialog.setWindowModality(Qt.ApplicationModal)

        username_lineedit = QLineEdit()
        username = race_table_model.get_race_property(self.USERNAME)
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
            race_table_model.delete_race_property(self.USERNAME)

            QMessageBox.warning(parent, 'Error', 'Username or password is incorrect.')
            return self.set_status(Status.Rejected)

        race_table_model.set_race_property(self.USERNAME, username)

        # Start our update timer.
        self.remote_timer = QTimer(self)
        self.remote_timer.timeout.connect(self.remote_update)
        self.remote_timer.start(self.interval_ms)

        QMessageBox.information(parent, 'Setup Complete', 'Simulated Remote set up successfully.')
        return self.set_status(Status.Ok)

    def disconnect(self, parent):
        race_table_model = self.modeldb.race_table_model

        race_table_model.delete_race_property(self.USERNAME)

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

    USERNAME = 'username'
    TIMER_INTERVAL_MS = 1000 # 1 second

    WATCH_FINISH_TIME_TO_POST = '00:00:00'

    def __init__(self, modeldb):
        """Initialize the OnTheDayRemote instance."""
        super().__init__(modeldb)

        self.auth = None
        self.race = None
        self.timer = None

        # For results processing.
        self.pending_queue = []
        self.pending_queue_lock = threading.Lock()

        # For changes updates from remote.
        self.changes_list = []
        self.changes_list_lock = threading.Lock()

        # Thread that performs all ontheday.net network (REST) transactions.
        self.thread = OnTheDayThread(self)

        self.journal = Journal(modeldb.journal_table_model, 'ontheday')

    def connect(self, parent):
        race_table_model = self.modeldb.race_table_model

        # Present a dialog where the user can enter the OnTheDay.net user name and password.
        dialog = QDialog(parent=parent)
        dialog.setWindowModality(Qt.ApplicationModal)

        # Try to auto-fill the user name. First, we look in the race properties. Secondly, we look
        # at application-wide QSettings.
        username_lineedit = QLineEdit()
        username = race_table_model.get_race_property(self.USERNAME)
        if not username:
            settings = QSettings()
            settings.beginGroup(ontheday.QSETTINGS_GROUP)
            username = settings.value(ontheday.QSETTINGS_KEY_USERNAME)
            settings.endGroup()

        if username:
            username_lineedit.setText(username)

        # Try to auto-fill the password, only if we have auto-filled the user name (otherwise, it
        # doesn't make any sense). We look in the keyring to see if there's a password stored there.
        password_lineedit = QLineEdit()
        password_lineedit.setEchoMode(QLineEdit.Password)
        if username:
            password = None
            try:
                password = keyring.get_password(ontheday.KEYRING_SERVICE, username)
            except keyring.errors.KeyringLocked:
                pass
            if password:
                password_lineedit.setText(password)

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

        # Execute the dialog.
        if dialog.exec() == QDialog.Rejected:
            return self.set_status(Status.Rejected)

        # Check our authentication to see if it's good.
        username = username_lineedit.text()
        password = password_lineedit.text()
        auth = (username, password)
        try:
            if ontheday.check_auth(auth):
                status = Status.Ok
            else:
                status = Status.Rejected
        except (ConnectionError, IOError):
            status = Status.Rejected

        # Authentication failed. Oh well.
        if status != Status.Ok:
            QMessageBox.warning(parent, 'Error',
                                'OnTheDay.net remote connection failed.')
            return self.set_status(status)

        # Authentication succeeded. Save the user name in the race properties, the password in the
        # keyring, and stash away our authenticator so we can use it in subsequent ontheday module
        # function calls to post results!
        race_table_model.set_race_property(self.USERNAME, username)
        keyring.set_password(ontheday.KEYRING_SERVICE, username, password)
        self.auth = auth

        # Save the race, needed for results submission.
        self.race = json.loads(race_table_model.get_race_property('ontheday_race'))

        # Start our worker thread.
        self.thread.start()

        # Start our update timer.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_tick)
        self.timer.start(self.TIMER_INTERVAL_MS)

        QMessageBox.information(parent, 'Success',
                                'OnTheDay.net remote connected successfully.')

        return self.set_status(status)

    def stop(self):
        """Stop our worker thread."""
        self.thread.should_run = False

    def disconnect(self, parent):
        race_table_model = self.modeldb.race_table_model

        # We've been asked to disconnect (by the user). Forget our user name.
        race_table_model.delete_race_property(self.USERNAME)

        # Stop our update timer.
        self.timer.stop()
        self.timer = None

        # Stop our worker thread.
        self.stop()
        self.thread = None

        QMessageBox.information(parent, 'Disconnected',
                                'OnTheDay.net remote disconnected successfully.')

    def timer_tick(self):
        """Called by Qt every TIMER_INTERVAL_MS (1s) within the main event thread.

        Use this function to collect results to post to OnTheDay.net.
        """
        # If results queue is empty, try to fill it by scanning the racer list for pending results.
        self.collect_result_submits()

        # Process all done requests (by marking the status column).
        self.process_result_responses()

        self.process_remote_changes()

    def collect_result_submits(self):
        """Go through the racer table and find stuff that needs submitting.

        We collect the list of results that need submitting into self.pending_queue.

        The current implementation of this function won't do a collection until the pending_queue
        has been drained.
        """
        if self.pending_queue:
            return

        racer_table_model = self.modeldb.racer_table_model

        with self.pending_queue_lock:
            # Iterate through all racers and put pending results on the results queue.
            for row in range(racer_table_model.rowCount()):
                record = racer_table_model.record(row)

                if record.value(racer_table_model.STATUS) != 'local':
                    continue

                metadata = json.loads(record.value(racer_table_model.METADATA))

                # Stuff to go into the ontheday result submission.
                # If no ontheday metadata, this racer was not imported from ontheday.net, so skip.
                try:
                    ontheday_id = metadata['ontheday']['id']
                except KeyError:
                    continue

                finish = record.value(racer_table_model.FINISH)
                if msecs_is_valid(finish):
                    # Report time relative to reference clock (which means just use msecs since
                    # midnight).
                    reference_datetime = QDateTime(QDate.currentDate())

                    finish_time = reference_datetime.addMSecs(finish)
                    ontheday_watch_finish_time = finish_time.time().toString(Qt.ISODateWithMs)
                    ontheday_tt_dnf = False
                elif finish in (MSECS_DNF, MSECS_DNP):
                    ontheday_watch_finish_time = self.WATCH_FINISH_TIME_TO_POST
                    ontheday_tt_dnf = True
                else:
                    ontheday_watch_finish_time = self.WATCH_FINISH_TIME_TO_POST
                    ontheday_tt_dnf = False

                result = {'ontheday': {'id': ontheday_id,
                                       'watch_finish_time': ontheday_watch_finish_time,
                                       'tt_dnf': ontheday_tt_dnf,
                                       'status': None},
                          'row': row}

                self.pending_queue.append(result)

    def process_result_responses(self):
        """Go through the pending queue and remove the results that have been submitted.

        Also remove results that failed submission so that we don't resubmit them.
        """
        racer_table_model = self.modeldb.racer_table_model
        racer_status_column = racer_table_model.status_column

        with self.pending_queue_lock:
            old_pending_queue = self.pending_queue
            self.pending_queue = []

            for result in old_pending_queue:
                index = racer_table_model.index(result['row'], racer_status_column)
                result_status = result['ontheday']['status']

                # Result is processed. Mark as "remote".
                if result_status == ontheday.ResultStatus.Ok:
                    if ((result['ontheday']['watch_finish_time'] ==
                         self.WATCH_FINISH_TIME_TO_POST) and
                        (not result['ontheday']['tt_dnf'])):
                        racer_table_model.setData(index, '')
                    else:
                        racer_table_model.setData(index, 'remote')
                    racer_table_model.dataChanged.emit(index, index)

                # Result is rejected. Mark as "rejected", and emit list of errors to log.
                elif result_status == ontheday.ResultStatus.Rejected:
                    racer_table_model.setData(index, 'rejected')

                    result_errors = result['ontheday']['errors']
                    for error in result_errors:
                        self.journal.log(error)

                # Result is skipped. Don't do anything (let it be picked up again on the next
                # time around).
                else:
                    self.pending_queue.append(result)

    def process_remote_changes(self):
        """Update our views with a list of remote changes.

        A change dict is of the form:
            category_name: Name of the changed category.
            category_start: Collective start time for the category (or None).
            entry_list_checksum: The checksum of the field that changed.
            entry_list: The list of ontheday entry records in that field.
        """
        with self.changes_list_lock:
            ontheday_changes = self.changes_list
            self.changes_list = []

        field_table_model = self.modeldb.field_table_model
        racer_table_model = self.modeldb.racer_table_model

        for ontheday_change in ontheday_changes:
            for ontheday_entry in ontheday_change['entry_list']:
                bib = ontheday_entry['race_number']

                # We may not find this racer (if it was added after registration).
                try:
                    racer_metadata = json.loads(racer_table_model.get_racer_metadata(bib))
                except InputError:
                    ontheday.add_racer_to_modeldb(self.modeldb, ontheday_entry,
                                                  ontheday_change['category_name'],
                                                  ontheday_change['category_start'])
                    continue

                if (('checksum' in racer_metadata['ontheday']) and
                    (racer_metadata['ontheday']['checksum'] == ontheday_entry['checksum'])):
                    continue

                racer_metadata['ontheday']['checksum'] = ontheday_entry['checksum']

                # Adding an already existing racer will just update its entry.
                ontheday.add_racer_to_modeldb(self.modeldb, ontheday_entry,
                                              ontheday_change['category_name'],
                                              ontheday_change['category_start'])

            field_metadata = json.loads(
                field_table_model.get_field_metadata(ontheday_change['category_name']))
            field_metadata['ontheday']['checksum'] = ontheday_change['entry_list_checksum']
            field_table_model.set_field_metadata(ontheday_change['category_name'],
                                                 json.dumps(field_metadata))

class OnTheDayThread(threading.Thread):
    """OnTheDay.net worker actually does the REST call to submit a result.

    Doing REST calls and waiting synchronously for results to come back will block for an
    intolerably long time, so we do this in a separate thread such that we don't block the UI. This
    is important for latching finish times accurately.
    """

    def __init__(self, remote):
        """Initialize the OnTheDayRemoteWorker instance."""
        super().__init__()

        self.should_run = True
        self.remote = remote

    def run(self):
        """Dispatch a bunch of costly ontheday.net stuff."""
        while self.should_run:
            self.submit_results()
            self.collect_remote_changes()

            time.sleep(ontheday.POLLING_INTERVAL_SECS)

    def submit_results(self):
        """Submit a batch of results to OnTheDay.net."""
        ontheday_results_list = None
        limit = self.remote.race['bulk_update_limit']

        with self.remote.pending_queue_lock:
            ontheday_results_list = list(map(lambda result: result['ontheday'],
                                             self.remote.pending_queue[0:limit]))
        if ontheday_results_list:
            try:
                ontheday.submit_results(self.remote.auth, self.remote.race,
                                        ontheday_results_list)

                for ontheday_result in ontheday_results_list:
                    ontheday_result['submitted'] = True

                self.remote.set_status(Status.Ok)
            except requests.exceptions.HTTPError:
                self.remote.set_status(Status.Rejected)
            except requests.exceptions.ConnectionError:
                self.remote.set_status(Status.TimedOut)

    def collect_remote_changes(self):
        """Collect OnTheDay.net changes (from website, other clients, etc.)"""
        ontheday_changes = ontheday.get_changes(self.remote.auth, self.remote.modeldb)

        if not ontheday_changes:
            return

        with self.remote.changes_list_lock:
            self.remote.changes_list += ontheday_changes
