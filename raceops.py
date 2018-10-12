#!/usr/bin/env python3

import json
import peewee
from datetime import datetime, time, timedelta
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

DEFAULT_RACE_NAME = '(needs description)'
DEFAULT_DATA = json.dumps({})
DEFAULT_TIME = peewee.TimeField(time(hour=0, minute=0, second=0, microsecond=0))
DEFAULT_RESULT_SCRATCHPAD = ''

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
            Race.create(name=DEFAULT_RACE_NAME, data=DEFAULT_DATA)

def race_reset():
    with database_proxy.atomic():
        racers_deleted = racer_delete_all()
        fields_deleted = field_delete_empty()

        race_model = Race.get()
        race_model.name = DEFAULT_RACE_NAME
        race_model.data = DEFAULT_DATA
        race_model.save()

    return (racers_deleted, fields_deleted)

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
        race_model.data = race['data']
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

# Fast way to get a field count if we don't need the list of fields.
def field_get_count():
    with database_proxy.atomic():
        return (Field
                .select()
                .count())

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

# Fast way to get a field's racer count if we don't need the list of racers.
def field_get_racer_count(name):
    with database_proxy.atomic():
        try:
            field_model = Field.get(Field.name == name)
        except DoesNotExist:
            raise LookupError('Field with name ' + name + ' does not exist.')

        return (field_model.racers
                .select()
                .count())

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

def field_delete_empty():
    field_list = field_get_list()
    field_count = field_get_count()

    for field in field_list:
        if field_get_racer_count(field['name']) == 0:
            field_delete(field['name'])
            field_count -= 1

    return field_count

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

# Fast way to get a racer count if we don't need the list of racers.
def racer_get_count():
    with database_proxy.atomic():
        return (Racer
                .select()
                .count())

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
        racer_model.start = racer['start']
        racer_model.finish = racer['finish']
        racer_model.data = racer['data']
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

def racer_delete_all_from_field(name):
    with database_proxy.atomic():
        # Field model is not found.
        try:
            field_model = Field.get(Field.name == name)
        except DoesNotExist:
            raise LookupError('Field with name ' + name + ' does not exist.')

        count = (field_model.racers
                 .select()
                 .count())
        (Racer
         .delete()
         .where(Racer.field == field_model)
         .execute())

    return count

def racer_delete_all():
    with database_proxy.atomic():
        (Racer
         .delete()
         .execute())

def result_get_list():
    list = []

    with database_proxy.atomic():
        query = (Result
                 .select()
                 .order_by(Result.bib))

        for result_model in query:
            list.append({'id': result_model.id,
                         'finish': result_model.finish,
                         'scratchpad': result_model.scratchpad,
                         'data': result_model.data})

    return list

# Fast way to get a result count if we don't need the list of results.
def result_get_count():
    with database_proxy.atomic():
        return (Result
                .select()
                .count())

def result_get(id):
    with database_proxy.atomic():
        # Result model is not found.
        try:
            result_model = Result.get(Result.id == id)
        except DoesNotExist:
            raise LookupError('Result with id ' + id + ' does not exist.')

    return {'id': result_model.id,
            'finish': result_model.finish,
            'scratchpad': result_model.scratchpad,
            'data': result_model.data}

def result_new(result):
    with database_proxy.atomic():
        # This create should normally succeed, since there is no chance of 
        # a unique key collision (we don't care about the value of the primary
        # key "id", and so we don't expose it to the caller of this API, and
        # instead just let peewee manage it under the hood.
        #
        # If no scratchpad text is given, we just make it blank.
        #
        # Also, if we try to create a result without specifying the finish
        # time, use the current time (now).
        #
        # In other words, it seems that you don't need to feed anything into
        # making a result.
        result_model = Result.create(finish=result.get('finish', datetime.time(datetime.now())),
                                     scratchpad=result.get('scratchpad', DEFAULT_RESULT_SCRATCHPAD),
                                     data=result.get('data', DEFAULT_DATA))

def result_modify(result):
    with database_proxy.atomic():
        # Result model is not found.
        try:
            result_model = Result.get(Result.id == result['id'])
        except DoesNotExist:
            raise LookupError('Result with id ' + result['id'] +
                              ' does not exist.')

        result_model.finish = result['finish']
        result_model.scratchpad = result['scratchpad']
        result_model.data = result['data']
        result_model.save()

def result_delete(id):
    with database_proxy.atomic():
        # Result model is not found.
        try:
            result_model = Result.get(Result.id == id)
        except DoesNotExist:
            raise LookupError('A result with id ' + id + ' does not exist.')

        result_model.delete_instance()

def result_delete_all():
    with database_proxy.atomic():
        (Result
         .delete()
         .execute())
