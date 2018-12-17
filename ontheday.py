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
from PyQt5.QtCore import QDate, QDateTime, QSettings, Qt, QTime
from PyQt5.QtWidgets import QAbstractItemView, QFileDialog, QLabel, QLineEdit, QPushButton, \
                            QTableWidget, QTableWidgetItem, QWidget
from PyQt5.QtWidgets import QWizard, QWizardPage
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QVBoxLayout
import requests
import keyring
import common
from racemodel import MSECS_UNINITIALIZED

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

def get_race_list(auth):
    """Gets the list of races that are visible from a particular authentication.

    The returned race records are of the following form:
    {
        "url": URL to this race's event list
        "name": Printable name of the race
        "date": yyyy-mm-dd of the race
    }
    """
    race_list = []

    next_url = URL + '/api/races/'

    while next_url:
        response = requests.get(next_url, auth=auth)
        if not response.ok:
            response.raise_for_status()
        response = json.loads(response.text)

        race_list += response['results']
        next_url = response['next']

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

    response = requests.get(url, auth=auth)
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
    }
    """
    racer_list = []

    url = field['category_start_list_url']

    response = requests.get(url, auth=auth)
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
        start_clock = QDateTime(QDate.currentDate(),
                                QTime.fromString(field['time_start'], Qt.ISODate))

        # Delta msecs from reference clock.
        start = reference_clock.msecsTo(start_clock)

        racer_list = get_racer_list(auth, field)

        for racer in racer_list:
            metadata = {'ontheday_id': racer['id']}
            racer_table_model.add_racer(str(racer['race_number']),
                                        racer['firstname'],
                                        racer['lastname'],
                                        field['name'],
                                        racer['category'],
                                        racer['team'],
                                        racer['racing_age'],
                                        start,
                                        MSECS_UNINITIALIZED,
                                        'local',
                                        json.dumps(metadata))

    # Set race data.
    race_table_model = modeldb.race_table_model
    race_table_model.set_race_property(race_table_model.NAME, race['name'])
    race_table_model.set_race_property(race_table_model.DATE, race['date'])

    notes = 'Imported from OnTheDay.net on %s' % QDateTime.currentDateTime()
    race_table_model.set_race_property(race_table_model.NOTES, notes)

class IntroductionPage(QWizardPage):
    """Introductory page of the import wizard that describes what we are about to do."""
    def __init__(self, parent=None):
        """Initialize the IntroductionPage instance."""
        super().__init__(parent=parent)

        self.setTitle('Introduction')

        label = QLabel('This wizard will authenticate with OnTheDay.net and import an existing '
                       'race configuration. Optionally, a remote connection to the race will be '
                       'established (or this can be done at a later time).')
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

    KEYRING_SERVICE = 'ontheday.net'

    USERNAME_QSETTING = 'username'

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
        group_name = __name__
        settings = QSettings()
        settings.beginGroup(group_name)
        username = settings.value(self.USERNAME_QSETTING)
        settings.endGroup()
        if not username:
            return

        # Autofill the username.
        self.setField(self.USERNAME_FIELD, username)

        # See if we have a password in our keyring for this username.
        password = keyring.get_password(self.KEYRING_SERVICE, username)
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

        self.wizard().auth = auth
        self.wizard().race_list = race_list

        # Cache the username, and stick the password into the keyring.
        group_name = __name__
        settings = QSettings()
        settings.beginGroup(group_name)
        settings.setValue(self.USERNAME_QSETTING, username)
        settings.endGroup()

        keyring.set_password(self.KEYRING_SERVICE, username, password)

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

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.file_lineedit)
        self.layout().addWidget(browse_button)

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
        return len(self.file_lineedit.text()) > 0

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

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(label)

        self.setButtonText(QWizard.FinishButton, 'Finish')

    def initializePage(self): #pylint: disable=invalid-name
        """Initialize page fields."""
        self.setSubTitle('Preparing to import %s' % (self.wizard().race['name'] + ' ' +
                                                     self.wizard().race['date']))

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
        self.setWindowTitle("OnTheDay.net race config import")
        self.addPage(IntroductionPage())
        self.addPage(AuthenticationPage())
        self.addPage(RaceSelectionPage())
        self.addPage(FileSelectionPage())
        self.addPage(ImportPage())
