#!/usr/bin/env python3

"""OnTheDay.net Classes

This module contains functions used for importing and synchronizing race data with OnTheDay.net
via its REST API.

Many calls need an authentication that requests.get understands.
For example, simple authentication: get_race_list(('username', 'password'))

"""

#pylint: disable=wrong-spelling-in-comment
#pylint: disable=wrong-spelling-in-docstring

import json
import os
from PyQt5.QtCore import QDate, QDateTime, QSettings, Qt, QTime
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

URL = 'https://ontheday.net'
HEADERS = {'User-Agent': '%s/%s' % (common.APPLICATION_NAME, common.VERSION)}
KEYRING_SERVICE = 'ontheday.net'
QSETTINGS_GROUP = 'ontheday'
QSETTINGS_KEY_USERNAME = 'username'

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
    race_list = []

    next_url = URL + '/api/races/'

    while next_url:
        response = requests.get(next_url, auth=auth, headers=HEADERS,
                                timeout=defaults.REQUESTS_TIMEOUT_SECS)
        if not response.ok:
            response.raise_for_status()
        response = json.loads(response.text)

        race_list += response['results']
        next_url = response['next']

    # For each race in the race list, get some details that are available in the race's event list.
    for race in race_list:
        url = race['url']
        response = requests.get(url, auth=auth, headers=HEADERS,
                                timeout=defaults.REQUESTS_TIMEOUT_SECS)
        if not response.ok:
            response.raise_for_status()
        response = json.loads(response.text)

        # Only time trials have a tt_watch_start_time.
        if 'tt_watch_start_time' in response.keys():
            race['tt_watch_start_time'] = response['tt_watch_start_time']

        race['bulk_update_url'] = response['bulk_update_url']
        race['bulk_update_limit'] = response['bulk_update_limit']
        race['bulk_update_fields'] = response['bulk_update_fields']

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
    }
    """
    racer_list = []

    url = field['category_start_list_url']

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
    racer_table_model = modeldb.racer_table_model

    field_list = get_field_list(auth, race)

    for field in field_list:
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
         'tt_dnf': False}

    To reset a result, use watch_finish_time of 00:00:00 and tt_dnf of False.
    To submit a DNF, tt_dnf should be True, and watch_finish_time should be 00:00:00.
    To submit a finish time, tt_dnf should be False, and watch_finish_time is a non-zero time.

    URL: https://ontheday.net/api/entry/tt_finish_time/
    """
    url = race['bulk_update_url']
    headers = {**HEADERS, **{'content-type': 'application/json'}}
    data = json.dumps(result_list)

    response = requests.post(url, auth=auth, headers=headers, data=data,
                             timeout=defaults.REQUESTS_TIMEOUT_SECS)
    if not response.ok:
        response.raise_for_status()

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
        password = keyring.get_password(KEYRING_SERVICE, username)
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

        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDefaultSuffix('rce')
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setLabelText(QFileDialog.Accept, 'New')
        file_dialog.setNameFilter('Race file (*.rce)')
        file_dialog.setOptions(QFileDialog.DontUseNativeDialog)
        file_dialog.setViewMode(QFileDialog.List)

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

        if 'tt_watch_start_time' in self.wizard().race.keys():
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
