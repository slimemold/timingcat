#!/usr/bin/env python3

"""OnTheDay.net Classes

This module contains functions used for importing and synchronizing race data with OnTheDay.net
via its REST API.
"""

import itertools
import json
import requests

URL = 'https://ontheday.net'

def get_race_list(auth):
    """Gets the list of races that are visible from a particular authentication.

    Pass in an authentication that requests.get understands.
    For example, simple authentication: get_race_list(('username', 'password'))
    """
    api = '/api/races/'
    race_list = []

    for page in itertools.count(1):
        payload = {'page': page}

        r = requests.get(URL + api, auth=auth, params=payload, verify=True)
        if not r.ok:
            r.raise_for_status()

        api_races_reply = json.loads(r.content)
        race_list += api_races_reply['results']
        if not api_races_reply['next']:
            break

    return race_list
