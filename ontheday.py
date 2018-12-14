#!/usr/bin/env python3

"""OnTheDay.net Classes

This module contains functions used for importing and synchronizing race data with OnTheDay.net
via its REST API.

Many calls need an authentication that requests.get understands.
For example, simple authentication: get_race_list(('username', 'password'))

"""

#pylint: disable=wrong-spelling-in-comment
#pylint: disable=wrong-spelling-in-docstring

from datetime import datetime
import json
import requests
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

    url = URL + '/api/starts/category/' + str(field['id']) + '/'

    response = requests.get(url, auth=auth)
    if not response.ok:
        response.raise_for_status()
    response = json.loads(response.text)

    racer_list = response['entries']

    return racer_list

def import_race(auth, modeldb, race):
    """Import a race.

    The race is identified by passing a race record returned by get_race_list().

    All of the fields and their racers will be imported. This function will
    also set the race name and date.
    """
    # Import racers (fields will be implicitly imported).
    racer_table_model = modeldb.racer_table_model

    field_list = get_field_list(auth, race)

    for field in field_list:
        racer_list = get_racer_list(auth, field)

        for racer in racer_list:
            metadata = {'ontheday_id': racer['id']}
            racer_table_model.add_racer(racer['race_number'],
                                        racer['firstname'],
                                        racer['lastname'],
                                        field['name'],
                                        4, # category missing!
                                        racer['team'],
                                        racer['racing_age'],
                                        MSECS_UNINITIALIZED,
                                        MSECS_UNINITIALIZED,
                                        'local',
                                        json.dumps(metadata))

    # Set race data.
    race_table_model = modeldb.race_table_model
    race_table_model.set_race_property(race_table_model.NAME, race['name'])
    race_table_model.set_race_property(race_table_model.DATE, race['date'])

    notes = 'Imported from OnTheDay.net on %s' % str(datetime.now())
    race_table_model.set_race_property(race_table_model.NOTES, notes)
