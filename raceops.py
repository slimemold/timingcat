#!/usr/bin/env python3

import peewee
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

def race_init(racefile):
    # Initialize the database proxy for our peewee models.
    database = peewee.SqliteDatabase(racefile,
                                     pragmas={'foreign_keys': 1})
    database_proxy.initialize(database)

    # Create the database tables if it is a new file.
    create_tables()

def race_cleanup():
    database_proxy.close()

# Sanity check a Race model.
def race_check(race):
    # Race model is incomplete.
    if not race['name']:
        raise KeyError('Race is missing name')
    if not race['data']:
        raise KeyError('Race is missing data')

# Returns a Race model
def race_get():
    with database_proxy.atomic():
        race_model = Race.get()

    return {'name': race_model.name,
            'data': race_model.data}

# Modifies the existing Race model.
def race_modify(race):
    race_check(race)

    with database_proxy.atomic():
        race_model = Race.get()
        race_model.name = race['name']
        race_model.data = race['data']
        race_model.save()

# Sanity check a Field model.
def field_check(field):
    # Field model is incomplete.
    if not field['name']:
        raise KeyError('Field is missing name')
    if not field['data']:
        raise KeyError('Field is missing data')

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
            raise LookupError('Field with name ' + name + ' does not exist.')

    return {'name': field_model.name,
            'data': field_model.data}

# Adds a Field model.
def field_new(field):
    field_check(field)

    with database_proxy.atomic():
        # Probably duplicate name.
        try:
            field_model = Field.create(name=field['name'], data=field['data'])
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
    field_check(field)

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

# Sanity check a Racer model.
def racer_check(racer):
    # Racer model is incomplete.
    # Note that start and finish can be absent.
    if not racer['bib']:
        raise KeyError('Racer is missing bib')
    if not racer['name']:
        raise KeyError('Racer is missing name')
    if not racer['team']:
        raise KeyError('Racer is missing team')
    if not racer['field']:
        raise KeyError('Racer is missing field')
    if not racer['data']:
        raise KeyError('Racer is missing data')

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
def racer_get():
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
    racer_check(racer)

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
                                       start=racer['start'],
                                       finish=racer['finish'],
                                       data=racer['data'])
        except IntegrityError:
            raise ValueError('Racer with bib ' + racer['bib'] +
                             ' already exists.')

def racer_modify(racer):
    racer_check(racer)

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

        racer.name = racer['name']
        racer.team = racer['team']
        racer.field = field
        racer.start = racer['start']
        racer.finish = racer['finish']
        racer.data = racer['data']
        racer.save()

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
        racer.save()

def racer_delete(bib):
    with database_proxy.atomic():
        # Racer model is not found.
        try:
            racer_model = Racer.get(Racer.bib == bib)
        except DoesNotExist:
            raise LookupError('A racer with bib ' + bib + ' does not exist.')

        racer_model.delete_instance()

