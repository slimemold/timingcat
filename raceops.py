#!/usr/bin/env python3

import json
import peewee
from datetime import time, timedelta
from racemodel import *

# This module hides the database queries behind a set of simple functions.
# The various objects (Race, Field, Racer) are represented by dictionaries:
#
# Race:
#   { 'name', 'data' }
#
# Field:
#   { 'name', 'data' }
#
# Racer:
#   { 'bib', 'name', 'team', 'field', 'start', 'finish', 'data' }
#
# Objects are generally retrieved by the first member.
#
# Race is a singleton, and is meant to hold miscellaneous information about
# a race, mainly for documentation and presentation purposes.
#
# In this module's implementation, variables that are various models from
# racemodel are named ending in _model, to avoid collision with raceops object
# names, which are named in the plain.

DEFAULT_DATA = json.dumps({})
DEFAULT_TIME = peewee.TimeField(time(hour=0, minute=0, second=0, microsecond=0))

def race_init(racefile):
    # Initialize the database proxy for our peewee models.
    database = peewee.SqliteDatabase(racefile,
                                     pragmas={'foreign_keys': 1})
    database_proxy.initialize(database)

    # Create the database tables if it is a new file.
    create_tables()

    database_proxy.connect()

    if Race.get_or_none() is None:
        with database_proxy.atomic():
            Race.create(name='(needs description)', data="{}")

def race_cleanup():
    database_proxy.close()

# Returns a Race model
def race_get():
    with database_proxy.atomic():
        race_model = Race.get()

    return {'name': race_model.name,
            'data': race_model.data}

# Modifies the existing Race model.
def race_modify(race):
    with database_proxy.atomic():
        race_model = Race.get()
        race_model.name = race['name']
        race_model.data = race.get('data', DEFAULT_DATA)
        race_model.save()

# Gets a list of Field models.
def field_get_list():
    list = []

    with database_proxy.atomic():
        query = (Field
                 .select()
                 .order_by(Field.name))

        for field_model in query:
            list.append({'name': field_model.name,
                         'data': field_model.data})

    return list

# Gets a Field model, given a field name.
def field_get(name):
    with database_proxy.atomic():
        # Field model is not found.
        try:
            field_model = Field.get(Field.name == name)
        except DoesNotExist:
            return None

    return {'name': field_model.name,
            'data': field_model.data}

# Adds a Field model.
def field_new(field):
    with database_proxy.atomic():
        # Probably duplicate name.
        try:
            field_model = Field.create(name=field['name'],
                                       data=field.get('data', DEFAULT_DATA))
        except IntegrityError:
            raise ValueError('Field with name ' + field['name'] +
                             ' already exists.')

def field_get_racer_list(name):
    list = []

    with database_proxy.atomic():
        try:
            field_model = Field.get(Field.name == name)
        except DoesNotExist:
            raise LookupError('Field with name ' + name + ' does not exist.')

        for racer_model in field_model.racers.order_by(Racer.bib):
            list.append({'bib': racer_model.bib,
                         'name': racer_model.name,
                         'team': racer_model.team,
                         'field': racer_model.field.name,
                         'start': racer_model.start,
                         'finish': racer_model.finish,
                         'data': racer_model.data})

    return list

# Modifies a Field model.
def field_modify(field):
    with database_proxy.atomic():
        # Field model is not found.
        try:
            field_model = Field.get(Field.name == field['name'])
        except DoesNotExist:
            raise LookupError('Field with name ' + field['name'] +
                              ' does not exist.')

        field_model.data = field['data']
        field_model.save()

# Renames a Field model.
def field_rename(old_name, new_name):
    with database_proxy.atomic():
        # Field model is not found.
        try:
            field_model = Field.get(Field.name == old_name)
        except DoesNotExist:
            raise LookupError('Field with name ' + old_name +
                              ' does not exist.')

        if Field.get_or_none(Field.name == new_name) is not None:
            raise ValueError('New name ' + new_name +
                             ' is used by another field.')

        field_model.name = new_name
        field_model.save()

# Deletes a Field model.
def field_delete(name):
    with database_proxy.atomic():
        # Field model is not found.
        try:
            field_model = Field.get(Field.name == name)
        except DoesNotExist:
            raise LookupError('Field with name ' + name + ' does not exist.')

        # Only allowed to delete a field if there are no racers in it.
        if field_model.racers.objects():
            raise RuntimeError('Field with name ' + name + ' is not empty')

        field_model.delete_instance()

# Gets a list of Field models.
def racer_get_list():
    list = []

    with database_proxy.atomic():
        query = (Racer
                 .select()
                 .order_by(Racer.bib))

        for racer_model in query:
            list.append({'bib': racer_model.bib,
                         'name': racer_model.name,
                         'team': racer_model.team,
                         'field': racer_model.field.name,
                         'start': racer_model.start,
                         'finish': racer_model.finish,
                         'data': racer_model.data})

    return list

# Gets a Racer model, given a racer bib.
def racer_get(bib):
    with database_proxy.atomic():
        # Racer model is not found.
        try:
            racer_model = Racer.get(Racer.bib == bib)
        except DoesNotExist:
            raise LookupError('Racer with bib ' + bib + ' does not exist.')

    return {'bib': racer_model.bib,
            'name': racer_model.name,
            'team': racer_model.team,
            'field': racer_model.field.name,
            'start': racer_model.start,
            'finish': racer_model.finish,
            'data': racer_model.data}

# Adds a Racer model.
def racer_new(racer):
    with database_proxy.atomic():
        # Racer model's specified field does not exist.
        try:
            field_model = Field.get(Field.name == racer['field'])
        except DoesNotExist:
            raise LookupError('Field named ' + racer['field'] +
                              ' does not exist.')

        # Probably duplicate bib.
        try:
            racer_model = Racer.create(bib=racer['bib'],
                                       name=racer['name'],
                                       team=racer['team'],
                                       field=field_model,
                                       start=racer.get('start', DEFAULT_TIME),
                                       finish=racer.get('finish', DEFAULT_TIME),
                                       data=racer.get('data', DEFAULT_DATA))
        except IntegrityError:
            raise ValueError('Racer with bib ' + racer['bib'] +
                             ' already exists.')

def racer_modify(racer):
    with database_proxy.atomic():
        # Racer model's specified field does not exist.
        try:
            field_model = Field.get(Field.name == racer['field'])
        except DoesNotExist:
            raise LookupError('Field named ' + racer['field'] +
                              ' does not exist.')

        # Racer model is not found.
        try:
            racer_model = Racer.get(Racer.bib == racer['bib'])
        except DoesNotExist:
            raise LookupError('Racer with bib ' + racer['bib'] +
                              ' does not exist.')

        racer_model.name = racer['name']
        racer_model.team = racer['team']
        racer_model.field = field_model
        racer_model.start = racer.get('start', DEFAULT_TIME)
        racer_model.finish = racer.get('finish', DEFAULT_TIME)
        racer_model.data = racer.get('data', DEFAULT_DATA)
        racer_model.save()

def racer_rebib(old_bib, new_bib):
    with database_proxy.atomic():
        # Racer model is not found.
        try:
            racer_model = Racer.get(Racer.bib == old_bib)
        except DoesNotExist:
            raise LookupError('Racer with bib ' + old_bib + ' does not exist.')

        # New bib is occupied.
        if Racer.get_or_none(Racer.bib == new_bib) is not None:
            raise ValueError('New bib ' + new_bib + ' is used by other racer.')

        racer_model.bib = new_bib
        racer_model.save()

def racer_delete(bib):
    with database_proxy.atomic():
        # Racer model is not found.
        try:
            racer_model = Racer.get(Racer.bib == bib)
        except DoesNotExist:
            raise LookupError('A racer with bib ' + bib + ' does not exist.')

        racer_model.delete_instance()

