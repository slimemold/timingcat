#!/usr/bin/env python3

VERSION='1.0'

import argparse
import cmd
import importlib
import os
import logging
import peewee
import re
import sys
from racemodel import *

logger = logging.getLogger(__name__)

def race_show(args):
    with database_proxy.atomic():
        race = Race.get()

    print(race.name)

def race_set(args):
    with database_proxy.atomic():
        race = Race.get()
        race.name = args.name
        race.save()

def field_list(args):
    with database_proxy.atomic():
        query = (Field
                 .select()
                 .order_by(Field.name))

        for field in query:
            print(field.name)

def field_show(args):
    with database_proxy.atomic():
        try:
            field = Field.get(Field.name == args.name)
        except DoesNotExist:
            print('A field named ' + args.name + ' does not exist.')
            return

        for racer in field.racers.order_by(Racer.bib):
            print(racer)

def field_add(args):
    with database_proxy.atomic():
#        try:
            field = Field.create(name=args.name, data="")
#        except IntegrityError:
#            print('A field named ' + args.name + ' already exists.')

def field_rename(args):
    with database_proxy.atomic():
        try:
            field = Field.get(Field.name == args.name)
        except DoesNotExist:
            print('A field named ' + args.name + ' does not exist.')
            return

        field.name = args.new_name
        field.save()

def field_rm(args):
    with database_proxy.atomic():
        try:
            field = Field.get(Field.name == args.name)
        except DoesNotExist:
            print('A field named ' + args.name + ' does not exist.')
            return

        field.delete_instance()

def racer_list(args):
    with database_proxy.atomic():
        query = (Racer
                 .select()
                 .order_by(Racer.bib))

        for racer in query:
            print(racer)

def racer_add(args):
    with database_proxy.atomic():
        try:
            field = Field.get(Field.name == args.field)
        except DoesNotExist:
            print('A field named ' + args.field + ' does not exist.')
            return

        try:
            racer = Racer.create(bib=args.bib, name=args.name, team=args.team,
                                 field=field, data="")
        except IntegrityError:
            print('A racer with bib ' + args.bib + ' already exists.')

def racer_rebib(args):
    with database_proxy.atomic():
        try:
            racer = Racer.get(Racer.bib == args.bib)
        except DoesNotExist:
            print('A racer with bib ' + args.bib + ' does not exist.')
            return

        try:
            racer.bib = args.new_bib
            racer.save()
        except IntegrityError:
            print('A racer with bib ' + args.new_bib + ' already exists.')

def racer_rename(args):
    with database_proxy.atomic():
        try:
            racer = Racer.get(Racer.bib == args.bib)
        except DoesNotExist:
            print('A racer with bib ' + args.bib + ' does not exist.')
            return

        racer.name = args.new_name
        racer.save()

def racer_reteam(args):
    with database_proxy.atomic():
        try:
            racer = Racer.get(Racer.bib == args.bib)
        except DoesNotExist:
            print('A racer with bib ' + args.bib + ' does not exist.')
            return

        racer.team = args.new_team
        racer.save()

def racer_refield(args):
    with database_proxy.atomic():
        try:
            racer = Racer.get(Racer.bib == args.bib)
        except DoesNotExist:
            print('A racer with bib ' + args.bib + ' does not exist.')
            return

        try:
            field = Field.get(Field.name == args.new_field)
        except DoesNotExist:
            print('A field named ' + args.name + ' does not exist.')
            return

        racer.field = field
        racer.save()

def racer_rm(args):
    with database_proxy.atomic():
        try:
            racer = Racer.get(Racer.name == args.name)
        except DoesNotExist:
            print('A racer named ' + args.name + ' does not exist.')
            return

        racer.delete_instance()

def make_parser():
    parser = argparse.ArgumentParser(description='SexyThyme, a race tracking program')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('racefile', help='use the specified race file')
    subparsers = parser.add_subparsers(help='command help')

    # Create the parser for the "race" command.
    race_parser = subparsers.add_parser('race')
    race_subparsers = race_parser.add_subparsers(help='race command help')

    # Create the parser for the "race show" command.
    subparser = race_subparsers.add_parser('show')
    subparser.set_defaults(func=race_show)

    # Create the parser for the "race set" command.
    subparser = race_subparsers.add_parser('set')
    subparser.add_argument('name',
                           help='long, descriptive name')
    subparser.set_defaults(func=race_set)

    # Create the parser for the "field" command.
    field_parser = subparsers.add_parser('field')
    field_subparsers = field_parser.add_subparsers(help='field command help')

    # Create the parser for the "field list" command.
    subparser = field_subparsers.add_parser('list')
    subparser.set_defaults(func=field_list)

    # Create the parser for the "field show" command.
    subparser = field_subparsers.add_parser('show')
    subparser.add_argument('name', help='used to identify the field')
    subparser.set_defaults(func=field_show)

    # Create the parser for the "field add" command.
    subparser = field_subparsers.add_parser('add')
    subparser.add_argument('name', help='used to identify the field')
    subparser.set_defaults(func=field_add)

    # Create the parser for the "field rename" command.
    subparser = field_subparsers.add_parser('rename')
    subparser.add_argument('name', help='used to identify the field')
    subparser.add_argument('new_name', help='new name')
    subparser.set_defaults(func=field_rename)

    # Create the parser for the "field rm" command.
    subparser = field_subparsers.add_parser('rm')
    subparser.add_argument('name', help='used to identify the field')
    subparser.set_defaults(func=field_rm)

    # Create the parser for the "racer" command.
    racer_parser = subparsers.add_parser('racer')
    racer_subparsers = racer_parser.add_subparsers(help='racer command help')

    # Create the parser for the "racer list" command.
    subparser = racer_subparsers.add_parser('list')
    subparser.set_defaults(func=racer_list)

    # Create the parser for the "racer add" command.
    subparser = racer_subparsers.add_parser('add')
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('name', help='racer\'s full name')
    subparser.add_argument('team', help='racer\'s team name')
    subparser.add_argument('field', help='racer\'s field name')
    subparser.set_defaults(func=racer_add)

    # Create the parser for the "racer rebib" command.
    subparser = racer_subparsers.add_parser('rebib')
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_bib', help='new bib')
    subparser.set_defaults(func=racer_rebib)

    # Create the parser for the "racer rename" command.
    subparser = racer_subparsers.add_parser('rename')
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_name', help='new name')
    subparser.set_defaults(func=racer_rename)

    # Create the parser for the "racer reteam" command.
    subparser = racer_subparsers.add_parser('reteam')
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_team', help='new team')
    subparser.set_defaults(func=racer_reteam)

    # Create the parser for the "racer refield" command.
    subparser = racer_subparsers.add_parser('refield')
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_field', help='new field name')
    subparser.set_defaults(func=racer_refield)

    # Create the parser for the "racer rm" command.
    subparser = racer_subparsers.add_parser('rm')
    subparser.add_argument('name', help='used to identify the racer')
    subparser.set_defaults(func=racer_rm)

    return parser

class Shell(cmd.Cmd):
    intro = 'SexyThyme: Type help or ? to list commands.\n'
    prompt = '(sexythyme) '
    parser = None

    def __init__(self, parser):
        super().__init__()
        self.parser = parser
        self.parser.usage = 'Fish!'

    def handle_command(self, command):
        try:
            # Get list of arguments, honoring quotes.
            arg_list = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', command)

            # Strip outer quotes, if present.
            arg_list_removed_quotes = []
            for arg in arg_list:
                if (arg.startswith('"') and arg.endswith('"') or
                    arg.startswith(''') and arg.endswith(''')):
                    arg_list_removed_quotes.append(arg[1:-1])
                else:
                    arg_list_removed_quotes.append(arg)

            # Send the cleaned up argument list to the parser and call the
            # proper function..
            args = self.parser.parse_args(arg_list_removed_quotes)
            args.func(args)
        # Catch argparse exception only.
        except SystemExit:
            pass

    def do_race(self, arg):
        self.handle_command('racefile race ' + arg)

    def do_field(self, arg):
        self.handle_command('racefile field ' + arg)

    def do_racer(self, arg):
        self.handle_command('racefile racer ' + arg)

    def do_exit(self, arg):
        return True

    def do_quit(self, arg):
        return True

if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()

    database_filename = args.racefile

    database = peewee.SqliteDatabase(database_filename,
                                     pragmas={'foreign_keys': 1})
    database_proxy.initialize(database)

    # Create the database tables if it is a new file.
    create_racefile()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        shell = Shell(parser)
        shell.cmdloop()

    database_proxy.close()
