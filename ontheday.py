#!/usr/bin/env python3

"""OnTheDay.net Classes

This module contains functions used for importing and synchronizing race data with OnTheDay.net
via its REST API.

Many calls need an authentication that requests.get understands.
For example, simple authentication: get_race_list(('username', 'password'))

"""

#pylint: disable=wrong-spelling-in-comment
#pylint: disable=wrong-spelling-in-docstring

import argparse
import fnmatch
from getpass import getpass
import json
import os
import sys
import threading
from PyQt5.QtCore import QDate, QDateTime, QObject, QSettings, Qt, QTime, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QAbstractItemView, QCheckBox, QFileDialog, QHeaderView, QLabel, \
                            QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QWidget
from PyQt5.QtWidgets import QWizard, QWizardPage
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QVBoxLayout
import requests
import keyring
import common
import defaults
from racemodel import MSECS_DNP, MSECS_UNINITIALIZED

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

URL = 'https://ontheday.net'
HEADERS = {'User-Agent': '%s/%s' % (common.APPLICATION_NAME, common.VERSION)}
KEYRING_SERVICE = 'ontheday.net'
QSETTINGS_GROUP = 'ontheday'
QSETTINGS_KEY_USERNAME = 'username'

ResultStatus = common.enum(
    Ok=0,
    Rejected=1
)

def check_auth(auth):
    """Check that the authenticator is good.

    For this, we can do a simple transaction and make sure it comes back with
    something.
    """
    return len(get_race_list(auth)) > 0

def get_race_list(auth):
    """Gets the list of races that are visible from a particular authentication.

    The returned race records are of the following form:
    {
        "url": URL to this race's event list
        "name": Printable name of the race
        "date": yyyy-mm-dd of the race
        "tt_watch_start_time": reference clock (for time trials only)
        "bulk_update_url": URL for posting results
        "bulk_update_limit": number of results that can be posted in a single transaction
        "bulk_update_fields": fields in a result dict
    }
    """
    full_race_list = []

    next_url = URL + '/api/races/'

    while next_url:
        response = requests.get(next_url, auth=auth, headers=HEADERS,
                                timeout=defaults.REQUESTS_TIMEOUT_SECS)
        if not response.ok:
            response.raise_for_status()
        response = json.loads(response.text)

        full_race_list += response['results']
        next_url = response['next']

    # For each race in the full race list, filter out unsupported races, and get some details.

    race_list = []

    for race in full_race_list:
        # Parse out the race id. This is a handy identifier to use to uniquely identify the race.
        # url is of the form "https://ontheday.net/api/races/179/".
        race['id'] = race['url'].rsplit('/', 2)[1]

        # This stuff is available in the race's event list.
        url = race['url']
        response = requests.get(url, auth=auth, headers=HEADERS,
                                timeout=defaults.REQUESTS_TIMEOUT_SECS)
        if not response.ok:
            response.raise_for_status()
        response = json.loads(response.text)

        # Only time trials have a tt_watch_start_time.
        if not 'tt_watch_start_time' in response.keys():
            continue

        race['tt_watch_start_time'] = response['tt_watch_start_time']
        race['bulk_update_url'] = response['bulk_update_url']
        race['bulk_update_limit'] = response['bulk_update_limit']
        race['bulk_update_fields'] = response['bulk_update_fields']

        race_list.append(race)

    return race_list

def get_field_list(auth, race):
    """Gets the list of fields for a particular race.

    The race is identified by passing a race record returned by get_race_list().

    The returned field records are of the following form:
    {
        "name": Printable name of the field
        "slug": OnTheDay.net slug line
        "id": OnTheDay.net category ID
        "category_index": OnTheDay.net category list index (unique within the event)
        "number_start": First possible bib number
        "number_stop": Last possible bib number
        "time_start": Start time of the field
        "entry_list_checksum": Checksum of the field (will change if racer results etc. change)
    }
    """
    field_list = []

    url = race['url']

    response = requests.get(url, auth=auth, headers=HEADERS,
                            timeout=defaults.REQUESTS_TIMEOUT_SECS)
    if not response.ok:
        response.raise_for_status()
    response = json.loads(response.text)

    events = response['events']
    for event in events:
        categories = event['categories']
        # We don't care about OnTheDay.net's concept of an event, but the event
        # has the category/field start time, so trickle that down into the
        # category/field.
        for category in categories:
            category['time_start'] = event['time_start']

        field_list += categories

    return field_list

def get_racer_list(auth, field):
    """Gets the list of racers for a particular field.

    The field is identified by passing a field record returned by get_field_list().

    The returned racer records are of the following form:
    {
        "id": Racer ID, used for submitting results
        "race_number": Bib number
        "prereg": Pre-reged? (true/false)
        "lastname": Racer last name
        "firstname": Racer first name
        "license": Racer USAC license number
        "team": Racer team name
        "racing_age": Racer racing age
        "gender": Racer gender
        "watch_start_time": Start time relative to reference clock
        "watch_finish_time": Finish time relative to reference clock
        "elapsed_time": Delta of start and finish, expressed as a time
        "tt_dnf": True if DNF
    }
    """
    racer_list = []

    url = field['category_entry_list_url']

    response = requests.get(url, auth=auth, headers=HEADERS,
                            timeout=defaults.REQUESTS_TIMEOUT_SECS)
    if not response.ok:
        response.raise_for_status()
    response = json.loads(response.text)

    racer_list = response['entries']

    return racer_list

def import_race(modeldb, auth, race):
    """Import a race.

    The race is identified by passing a race record returned by get_race_list().

    All of the fields and their racers will be imported. This function will
    also set the race name and date.
    """
    # Import racers (fields will be implicitly imported).
    field_table_model = modeldb.field_table_model
    racer_table_model = modeldb.racer_table_model

    field_list = get_field_list(auth, race)

    for field in field_list:
        # Add the field here. In case there are no racers in the field, we want the field added
        # anyway.
        # Also, we need to keep field metadata (especially the checksum, which we will use to
        # check if there are any changes in the field).
        metadata = {'ontheday': {'url': field['category_entry_list_url'],
                                 'checksum': field['entry_list_checksum']}}
        field_table_model.add_field(field['name'], '', json.dumps(metadata))

        # This is wall clock, date of today, which is what the reference clock
        # is by default (before it's set to something else).
        reference_clock = modeldb.race_table_model.get_reference_clock_datetime()

        # This is start time expressed as wall time, from OnTheDay.net.
        # i.e. start_clock is the actual start time (not relative to reference).
        start_clock = QDateTime(QDate.currentDate(),
                                QTime.fromString(field['time_start'], Qt.ISODateWithMs))

        # Delta msecs from reference clock.
        start = reference_clock.msecsTo(start_clock)

        racer_list = get_racer_list(auth, field)

        for racer in racer_list:
            # Racers without a tt_finish_time_url are placeholder entries and should not show
            # up in our racer list.
            if not 'tt_finish_time_url' in racer:
                continue

            metadata = {'ontheday': {'id': racer['id'],
                                     'tt_finish_time_url': racer['tt_finish_time_url']}}

            ontheday_watch_finish_time = racer['watch_finish_time']
            ontheday_tt_dnf = racer['tt_dnf']

            if ontheday_tt_dnf:
                finish = MSECS_DNP
            elif ontheday_watch_finish_time == '00:00:00':
                finish = MSECS_UNINITIALIZED
            else:
                reference_datetime = QDateTime(QDate.currentDate())

                date = reference_datetime.date()
                time = QTime.fromString(ontheday_watch_finish_time, Qt.ISODateWithMs)
                if time.isValid():
                    datetime = QDateTime(date, time)
                    finish = reference_datetime.msecsTo(datetime)
                else:
                    finish = MSECS_UNINITIALIZED

            if finish == MSECS_UNINITIALIZED:
                status = ''
            else:
                status = 'remote'

            racer_table_model.add_racer(str(racer['race_number']),
                                        racer['firstname'],
                                        racer['lastname'],
                                        field['name'],
                                        racer['category'],
                                        racer['team'],
                                        racer['racing_age'],
                                        start,
                                        finish,
                                        status,
                                        json.dumps(metadata))

    # Set race data.
    race_table_model = modeldb.race_table_model
    race_table_model.set_race_property(race_table_model.NAME, race['name'])
    race_table_model.set_race_property(race_table_model.DATE, race['date'])
    race_table_model.set_race_property('ontheday_race', json.dumps(race))

    notes = 'Imported from OnTheDay.net on %s.' % QDateTime.currentDateTime().toString(Qt.ISODate)
    race_table_model.set_race_property(race_table_model.NOTES, notes)

def submit_results(auth, race, result_list):
    """Submits a list of results.

    A result is a dict that takes the following form:
        {'id': 137217,
         'watch_finish_time': '00:18:30.9',
         'tt_dnf': False,
         'status': None}

    To reset a result, use watch_finish_time of 00:00:00 and tt_dnf of False.
    To submit a DNF, tt_dnf should be True, and watch_finish_time should be 00:00:00.
    To submit a finish time, tt_dnf should be False, and watch_finish_time is a non-zero time.

    Upon completion of this call, the status will have the following value:
        ResultStatus.Ok means that the result has been committed.
        ResultStatus.Rejected means the result has failed, and should not be resubmitted as is.
        None means the result was not processed, and should be resubmitted.

    URL: https://ontheday.net/api/entry/tt_finish_time/
    """
    url = race['bulk_update_url']
    headers = {**HEADERS, **{'content-type': 'application/json'}}
    data = json.dumps(result_list)
    response = requests.post(url, auth=auth, headers=headers, data=data,
                             timeout=defaults.REQUESTS_TIMEOUT_SECS)

    _process_response_list(result_list, json.loads(response.text))

    if not response.ok:
        response.raise_for_status()

def _process_response_list(result_list, response_list):
    """Process list of result responses.

    The REST response is a list, where each list entry corresponds to a submitted result. Process
    each result response.
    """
    for result, response in zip(result_list, response_list):
        _process_response(result, response)

def _process_response(result, response):
    """Process individual response.

    'non_field_errors' in the response is a list of strings, where those strings are JSON encodings
    of dicts. Store this list of strings in 'error' key of the result.
    """
    if 'non_field_errors' in response.keys():
        result['status'] = ResultStatus.Rejected
        result['errors'] = response['non_field_errors']
    elif response.keys():
        result['status'] = ResultStatus.Ok

class IntroductionPage(QWizardPage):
    """Introductory page of the import wizard that describes what we are about to do."""
    def __init__(self, intro_text, parent=None):
        """Initialize the IntroductionPage instance."""
        super().__init__(parent=parent)

        self.setTitle('Introduction')

        label = QLabel(intro_text)
        label.setWordWrap(True)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(label)

class AuthenticationPage(QWizardPage):
    """Authentication page of the import wizard to get the OnTheDay.net username and password.

    This class will look for a cached username, and if one exists, will auto-enter it into the
    username field. It will then look for a password via keyring, and if exists, will auto-fill
    the password field.
    """
    USERNAME_FIELD = 'Username'
    PASSWORD_FIELD = 'Password'

    def __init__(self, parent=None):
        """Initialize the AuthenticationPage instance."""
        super().__init__(parent=parent)

        self.setTitle('Authentication')
        self.setSubTitle('Please provide OnTheDay.net account login credentials.')

        self.username_lineedit = QLineEdit()

        self.password_lineedit = QLineEdit()
        self.password_lineedit.setEchoMode(QLineEdit.Password)

        form_widget = QWidget()
        form_widget.setLayout(QFormLayout())
        form_widget.layout().addRow(self.USERNAME_FIELD, self.username_lineedit)
        form_widget.layout().addRow(self.PASSWORD_FIELD, self.password_lineedit)

        self.status_label = QLabel()
        self.status_label.setStyleSheet('QLabel{color:red;}')

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(form_widget)
        self.layout().addWidget(self.status_label)

        # Register wizard page fields.
        self.registerField(self.USERNAME_FIELD + '*', self.username_lineedit)
        self.registerField(self.PASSWORD_FIELD + '*', self.password_lineedit)

    def initializePage(self): #pylint: disable=invalid-name
        """Initialize page fields."""
        self.setField(self.USERNAME_FIELD, '')
        self.setField(self.PASSWORD_FIELD, '')
        self.status_label.setText('')

        # See if we have an OnTheDay.net username cached in our application settings.
        settings = QSettings()
        settings.beginGroup(QSETTINGS_GROUP)
        username = settings.value(QSETTINGS_KEY_USERNAME)
        settings.endGroup()
        if not username:
            return

        # Autofill the username.
        self.setField(self.USERNAME_FIELD, username)

        # See if we have a password in our keyring for this username.
        password = None
        try:
            password = keyring.get_password(KEYRING_SERVICE, username)
        except keyring.errors.KeyringLocked:
            pass
        if not password:
            return

        self.setField(self.PASSWORD_FIELD, password)

    def validatePage(self): #pylint: disable=invalid-name
        """Tries to access OnTheDay.net to make sure the account login credentials are okay.

        Since we need to perform some kind of OnTheDay.net REST API operation, we might as well
        try to grab the race list.
        """
        username = self.field(self.USERNAME_FIELD)
        password = self.field(self.PASSWORD_FIELD)
        auth = (username, password)

        try:
            race_list = get_race_list(auth)
        except requests.exceptions.HTTPError:
            self.status_label.setText('Authentication failure')
            return False
        except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout):
            self.status_label.setText('Timeout')
            return False

        self.wizard().auth = auth
        self.wizard().race_list = race_list

        # Cache the username, and stick the password into the keyring.
        settings = QSettings()
        settings.beginGroup(QSETTINGS_GROUP)
        settings.setValue(QSETTINGS_KEY_USERNAME, username)
        settings.endGroup()

        keyring.set_password(KEYRING_SERVICE, username, password)

        return True

class RaceSelectionPage(QWizardPage):
    """Race selection page of the import wizard to choose a race to import.

    This class presents the list of races known by the logged in OnTheDay.net account. The user
    is expected to choose a race to import.
    """

    NAME_COLUMN = 0
    DATE_COLUMN = 1

    def __init__(self, parent=None):
        """Initialize the RaceSelectionPage instance."""
        super().__init__(parent=parent)

        self.setTitle('Race Selection')
        self.setSubTitle('Please select a race to import.')

        self.race_table_widget = QTableWidget()
        self.race_table_widget.setColumnCount(2)
        self.race_table_widget.setAlternatingRowColors(True)
        self.race_table_widget.setHorizontalHeaderLabels(['Race', 'Date'])
        self.race_table_widget.horizontalHeader().setHighlightSections(False)
        self.race_table_widget.horizontalHeader().setStretchLastSection(True)
        self.race_table_widget.verticalHeader().setVisible(False)
        self.race_table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.race_table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.race_table_widget.itemSelectionChanged.connect(self.completeChanged)
        self.race_table_widget.itemSelectionChanged.connect(self.check_race_date)

        self.status_label = QLabel()
        self.status_label.setStyleSheet('QLabel{color:red;}')

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.race_table_widget)
        self.layout().addWidget(self.status_label)

    def initializePage(self): #pylint: disable=invalid-name
        """Initialize page fields."""
        self.race_table_widget.clearContents()
        self.race_table_widget.setRowCount(len(self.wizard().race_list))

        # Qt warns us that inserting items while sorting is enabled will mess with the insertion
        # order, so disable sorting before populating the list, and then re-enable sorting
        # afterwards.
        self.race_table_widget.setSortingEnabled(False)
        for row, race in enumerate(self.wizard().race_list):
            # Make our name item (non-editable).
            name_item = QTableWidgetItem(race['name'])
            name_item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)
            name_item.setData(Qt.UserRole, race)
            self.race_table_widget.setItem(row, self.NAME_COLUMN, name_item)

            # Make our date item (non-editable).
            date_item = QTableWidgetItem(race['date'])
            date_item.setFlags(date_item.flags() ^ Qt.ItemIsEditable)
            date_item.setData(Qt.UserRole, race)
            self.race_table_widget.setItem(row, self.DATE_COLUMN, date_item)
        self.race_table_widget.setSortingEnabled(True)

        self.race_table_widget.sortByColumn(self.DATE_COLUMN, Qt.DescendingOrder)

        self.race_table_widget.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)

    def isComplete(self): #pylint: disable=invalid-name
        """Make sure a race is selected."""
        return len(self.race_table_widget.selectedItems()) > 0

    def validatePage(self): #pylint: disable=invalid-name
        """No validation actually done here. Just store the selected race."""
        if not self.race_table_widget.selectedItems():
            return False

        race = self.race_table_widget.selectedItems()[0].data(Qt.UserRole)
        self.wizard().race = race

        return True

    def check_race_date(self):
        """See if the selected race is in the past, and update status label."""
        race_date = None

        for item in self.race_table_widget.selectedItems():
            if item.column() == self.DATE_COLUMN:
                race_date = QDate.fromString(item.text(), Qt.ISODate)
                break

        if race_date is None:
            return

        if race_date < QDate.currentDate():
            self.status_label.setText('Warning: Race date is in the past.')
        else:
            self.status_label.setText('')

class FileSelectionPage(QWizardPage):
    """File selection page of the import wizard to choose a save file."""

    def __init__(self, parent=None):
        """Initialize the FileSelectionPage instance."""
        super().__init__(parent=parent)

        self.setTitle('Save File')
        self.setSubTitle('Please choose a save file for this race.')

        self.file_lineedit = QLineEdit()

        browse_button = QPushButton('Browse...')

        file_browse_widget = QWidget()
        file_browse_widget.setLayout(QHBoxLayout())
        file_browse_widget.layout().addWidget(self.file_lineedit)
        file_browse_widget.layout().addWidget(browse_button)

        self.status_label = QLabel()
        self.status_label.setStyleSheet('QLabel{color:red;}')

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(file_browse_widget)
        self.layout().addWidget(self.status_label)

        file_dialog = common.FileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDefaultSuffix('rce')
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setLabelText(QFileDialog.Accept, 'New')
        file_dialog.setNameFilter('Race file (*.rce)')

        browse_button.clicked.connect(file_dialog.exec)
        file_dialog.fileSelected.connect(self.file_lineedit.setText)
        self.file_lineedit.textChanged.connect(self.completeChanged)

    def initializePage(self): #pylint: disable=invalid-name
        """Initialize page fields."""
        default_filename = (self.wizard().race['name'] + ' ' +
                            self.wizard().race['date'] + '.rce')

        self.file_lineedit.setText(default_filename)

    def isComplete(self): #pylint: disable=invalid-name
        """Make sure a race is selected."""
        filename = self.file_lineedit.text()
        if not filename:
            return False

        if os.path.isfile(filename):
            self.status_label.setText('Warming: File already exists!')
        else:
            self.status_label.setText('')

        return True

    def validatePage(self): #pylint: disable=invalid-name
        """No validation actually done here. Just store the selected filename."""
        self.wizard().filename = self.file_lineedit.text()
        return True

class ImportPage(QWizardPage):
    """Page that shows import progress and status."""

    def __init__(self, parent=None):
        """Initialize the FileSelectionPage instance."""
        super().__init__(parent=parent)

        self.setTitle('Importing OnTheDay.net race')

        label = QLabel('Import setup complete. Click "Finish" to begin the race import operation.')
        label.setWordWrap(True)

        self.reference_clock_checkbox = QCheckBox()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(label)
        self.layout().addWidget(self.reference_clock_checkbox)

        self.setButtonText(QWizard.FinishButton, 'Finish')

    def initializePage(self): #pylint: disable=invalid-name
        """Initialize page fields."""
        self.setSubTitle('Preparing to import %s' % (self.wizard().race['name'] + ' ' +
                                                     self.wizard().race['date']))

        if ('tt_watch_start_time' in self.wizard().race.keys() and
            self.wizard().race['tt_watch_start_time']):
            self.reference_clock_checkbox.show()
            self.reference_clock_checkbox.setChecked(True)

            text = ('Import reference clock setting of %s' %
                    self.wizard().race['tt_watch_start_time'])
            self.reference_clock_checkbox.setText(text)
        else:
            self.reference_clock_checkbox.hide()

    def validatePage(self): #pylint: disable=invalid-name
        """No validation actually done here. Just store the reference clock import preferences."""
        self.wizard().enable_reference_clock = self.reference_clock_checkbox.isChecked()
        if self.wizard().enable_reference_clock:
            reference_clock_date = QDate.currentDate()
            reference_clock_time = QTime.fromString(self.wizard().race['tt_watch_start_time'],
                                                    Qt.ISODateWithMs)
            self.wizard().reference_clock = QDateTime(reference_clock_date, reference_clock_time)

        return True

class ImportWizard(QWizard):
    """OnTheDay.net import wizard.

    The import wizard presents a number of pages that walks the user through importing an
    OnTheDay.net race config.

    The user will be asked for authentication information. A list of races will then be presented
    for selection.

    When the dialog completes, race will hold the race to be imported, filename will hold the
    filename to use for the race data, and auth will hold an authentication thing that can be
    used as the authenticator for the various REST functions.
    """
    def __init__(self, parent=None):
        """Initialize the ImportWizard instance."""
        super().__init__(parent=parent)

        self.filename = None
        self.auth = None
        self.race = None

        # Create the race selection page.
        race_selection_page = QWizardPage()
        race_selection_page.setTitle('Race Selection')

        # Create the wizard and add our pages.
        self.setWindowTitle('OnTheDay.net race config import')
        self.addPage(IntroductionPage('This wizard will authenticate with OnTheDay.net and import '
                                      'an existing race configuration. Optionally, a remote '
                                      'connection to the race will be established (or this can be '
                                      'done at a later time).'))
        self.addPage(AuthenticationPage())
        self.addPage(RaceSelectionPage())
        self.addPage(FileSelectionPage())
        self.addPage(ImportPage())

class RemoteSetupWizard(QWizard):
    """OnTheDay.net remote setup wizard.

    """
    def __init__(self, race, parent=None):
        """Initialize the RemoteSetupWizard instance."""
        super().__init__(parent=parent)

        self.setWindowTitle('OnTheDay.net remote setup')
        self.addPage(IntroductionPage('This wizard will set up the OnTheDay.net remote connection, '
                                      'allowing race results to be pushed up to the OnTheDay.net '
                                      'server as they are committed.'))
        self.addPage(AuthenticationPage())
        self.addPage(RaceSelectionPage(race))

class FieldStatisticsTable(QTableWidget):
    """QTableWidget subclass that shows statistics for the various fields in a race."""

    WINDOW_TITLE = 'Field Statistics Monitor'
    INTERVAL_SECS = 5 # Seconds between update end and next update start.

    NAME_COLUMN = 0
    FINISHED_COLUMN = 1
    TOTAL_COLUMN = 2

    def __init__(self, auth, race, interval_secs=INTERVAL_SECS, parent=None):
        """Initialize the FieldStatisticsTable instance."""
        super().__init__(parent=parent)

        self.setWindowTitle(' - '.join([self.WINDOW_TITLE, race['name']]))

        self.auth = auth

        field_list = get_field_list(self.auth, race)
        self.field_list_lock = threading.Lock()

        # Set up the table.
        self.setColumnCount(3)
        self.setAlternatingRowColors(True)
        self.setHorizontalHeaderLabels(['Field', 'Finished', 'Total'])
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionMode(QAbstractItemView.NoSelection)

        self.clearContents()
        self.setRowCount(len(field_list))

        # Qt warns us that inserting items while sorting is enabled will mess with the insertion
        # order, so disable sorting before populating the list, and then re-enable sorting
        # afterwards.
        self.setSortingEnabled(False)
        for row, field in enumerate(field_list):
            # Make our name item. Stash our field dict into this item to associate the field with
            # this row, even if the table gets resorted.
            item = QTableWidgetItem(field['name'])
            item.field = field
            self.setItem(row, self.NAME_COLUMN, item)

            # Make our finished item.
            item = QTableWidgetItem(0)
            self.setItem(row, self.FINISHED_COLUMN, item)

            # Make our total item.
            item = QTableWidgetItem(0)
            self.setItem(row, self.TOTAL_COLUMN, item)

        self.setSortingEnabled(True)
        self.sortByColumn(self.NAME_COLUMN, Qt.AscendingOrder)
        self.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)

        self.read_settings()

        # Make our single-shot update timer.
        self.timer = QTimer(self)
        self.timer.setInterval(interval_secs * 1000)
        self.timer.setTimerType(Qt.VeryCoarseTimer)
        self.timer.setSingleShot(True)

        self.timer.timeout.connect(self.schedule_work)

        # Simulate a timer timeout so that we immediately schedule work.
        self.schedule_work()

    def close(self):
        """Handle window close."""
        self.write_settings()

    def schedule_work(self):
        """Make our worker thread."""
        worker_thread = self.WorkerThread(self)
        worker_thread.done.connect(self.update_table)
        worker_thread.start()

    def update_table(self):
        """Update field statistics."""
        for row in range(self.rowCount()):
            field = self.item(row, self.NAME_COLUMN).field

            with self.field_list_lock:
                finished = field['finished']
                total = field['total']

            # Set finished and total.
            self.item(row, self.FINISHED_COLUMN).setData(Qt.DisplayRole, finished)
            self.item(row, self.TOTAL_COLUMN).setData(Qt.DisplayRole, total)

            # Pick a background color for this row, depending on finished and total.
            if total > 0:
                if finished == 0:
                    brush = None
                elif 0 < finished < total:
                    brush = QBrush(Qt.yellow)
                elif finished == total:
                    brush = QBrush(Qt.green)
                else:
                    brush = QBrush(Qt.red) # To show that something is horribly wrong.
            else:
                brush = None

            for column in range(self.columnCount()):
                self.item(row, column).setData(Qt.BackgroundRole, brush)

        self.timer.start()

    def read_settings(self):
        """Read settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        if settings.contains('size'):
            self.resize(settings.value('size'))
        if settings.contains('pos'):
            self.move(settings.value('pos'))

        if settings.contains('horizontal_header_state'):
            self.horizontalHeader().restoreState(settings.value('horizontal_header_state'))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())

        settings.endGroup()

    class WorkerThread(QObject, threading.Thread):
        """Worker thread that does the REST calls to gather the field statistics."""
        def __init__(self, parent):
            """Initialize the OnTheDayRemoteWorker instance."""
            super().__init__()

            self.parent = parent

        def run(self):
            """Submit a batch of results to OnTheDay.net."""
            for row in range(self.parent.rowCount()):
                field = self.parent.item(row, self.parent.NAME_COLUMN).field

                racer_list = get_racer_list(self.parent.auth, field)

                total = len(racer_list)

                finished = 0
                for racer in racer_list:
                    if racer['watch_finish_time'] != '00:00:00' or racer['tt_dnf']:
                        finished += 1

                with self.parent.field_list_lock:
                    field['finished'] = finished
                    field['total'] = total

            self.done.emit()

        done = pyqtSignal()

class CommandLineTool():
    """Class that supports command-line ontheday.net tools."""
    def __init__(self):
        """Command-line entry point to some useful OnTheDay.net stuff."""
        # Define top-level parser.
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-v', action='version',
                            version=common.APPLICATION_NAME + ' v' + common.VERSION)
        parser.add_argument('--username', '-u')
        parser.add_argument('--password', '-p')
        parser.set_defaults(func=parser.print_help)
        subparsers = parser.add_subparsers()

        # Define 'list' parser.
        list_parser = subparsers.add_parser('list')
        list_parser.set_defaults(func=list_parser.print_help)
        list_subparsers = list_parser.add_subparsers()

        # Define 'list races' parser.
        list_races_parser = list_subparsers.add_parser('races')
        list_races_parser.set_defaults(func=self.list_races)

        # Define 'list fields' parser.
        list_fields_parser = list_subparsers.add_parser('fields')
        list_fields_parser.set_defaults(func=self.list_fields)
        list_fields_parser.add_argument('race_id')

        # Define 'list racers' parser.
        list_racers_parser = list_subparsers.add_parser('racers')
        list_racers_parser.set_defaults(func=self.list_racers)
        list_racers_parser.add_argument('race_id')
        list_racers_parser.add_argument('field_name')

        monitor_parser = subparsers.add_parser('monitor')
        monitor_parser.set_defaults(func=self.monitor)
        monitor_parser.add_argument('--interval', type=int, dest='monitor_interval',
                                    default=FieldStatisticsTable.INTERVAL_SECS,
                                    help='Interval in seconds between updates')
        monitor_parser.add_argument('race_id')

        self.args = parser.parse_args()
        self.args.func()

    def get_auth(self):
        """Get authentication information from the user."""
        username = self.args.username
        if not username:
            username = input('Username: ')

        password = self.args.password
        if not password:
            password = getpass('Password: ')

        return (username, password)

    def list_races(self):
        """List the supported races visible under the authenticated account.

        Only time trials are currently supported.

        If args.full, then also do a (full) dump of fields.
        """
        auth = self.get_auth()
        race_list = get_race_list(auth)

        print('%-8s%-11s%s' % ('race_id', 'date', 'name'))
        print('======= ========== ====================================')
        for race in race_list:
            print('%-8s%-11s%s' % (race['id'], race['date'], race['name']))

    def list_fields(self):
        """List the fields of a specified race.

        self.args.race_id is expected to have an (optionally) wildcarded race_id. All races that
        match will have their fields listed.
        """
        auth = self.get_auth()
        race_id = self.args.race_id

        race_list = get_race_list(auth)
        matching_race_list = list(filter(lambda race: fnmatch.fnmatchcase(race['id'], race_id),
                                         race_list))
        if len(matching_race_list) > 1:
            field_indent = 4
        else:
            field_indent = 0

        for race in matching_race_list:
            # If more than one matching race, print the race name.
            if len(matching_race_list) > 1:
                print(race['name'])

            field_list = get_field_list(auth, race)
            for field in field_list:
                print((' ' * field_indent) + field['name'])

    def list_racers(self):
        """List the racers of a specified race and field.

        self.args.race_id is expected to have an (optionally) wildcarded race_id. All races that
        match will have their racers listed.

        self.args.field_name is expected to have an (optionally) wildcarded field_name. All fields
        that match will have their racers listed.
        """
        auth = self.get_auth()
        race_id = self.args.race_id
        field_name = self.args.field_name

        race_list = get_race_list(auth)
        matching_race_list = list(filter(lambda race: fnmatch.fnmatchcase(race['id'], race_id),
                                         race_list))
        if len(matching_race_list) > 1:
            field_indent = 4
        else:
            field_indent = 0

        for race in matching_race_list:
            # If more than one matching race, print the race name.
            if len(matching_race_list) > 1:
                print(race['name'])

            field_list = get_field_list(auth, race)
            matching_field_list = list(filter(lambda field: fnmatch.fnmatchcase(field['name'],
                                                                                field_name),
                                              field_list))
            if len(matching_field_list) > 1:
                racer_indent = field_indent + 4
            else:
                racer_indent = field_indent

            for field in matching_field_list:
                if len(matching_field_list) > 1:
                    print((' ' * field_indent) + field['name'])

                racer_list = get_racer_list(auth, field)

                for racer in racer_list:
                    print((' ' * racer_indent) + racer['firstname'] + ' ' + racer['lastname'])

    def monitor(self):
        """Launch a table view of fields and field statistics."""
        auth = self.get_auth()
        race_id = self.args.race_id

        race_list = get_race_list(auth)
        matching_race_list = list(filter(lambda race: fnmatch.fnmatchcase(race['id'], race_id),
                                         race_list))
        if len(matching_race_list) > 1:
            sys.stderr.write('Ambiguous race id %s, can match: %s.\n' %
                  (race_id, ', '.join(map(lambda race: race['id'], matching_race_list))))
            sys.exit(-1)
        race = matching_race_list[0]

        QApplication.setOrganizationName(common.ORGANIZATION_NAME)
        QApplication.setOrganizationDomain(common.ORGANIZATION_DOMAIN)
        QApplication.setApplicationName(common.APPLICATION_NAME)
        QApplication.setApplicationVersion(common.VERSION)

        app = QApplication(sys.argv)

        main_window = FieldStatisticsTable(auth, race, self.args.monitor_interval)
        main_window.show()
        retcode = app.exec_()

        main_window.close()
        sys.exit(retcode)

if __name__ == '__main__':
    try:
        CommandLineTool()
    except requests.exceptions.HTTPError as e:
        print(str(e))
