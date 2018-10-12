#!/usr/bin/env python3

import argparse
import cmd
import os
import logging
import re
import sys
import raceops

from common import VERSION

logger = logging.getLogger(__name__)

def race_str(args, race):
    string = '%s' % (race['name'])

    if args.showdata:
        string += ', %s' % (race['data'])

    return string

def field_str(args, field):
    string = '%s' % (field['name'])

    if args.showdata:
        string += ', %s' % (field['data'])

    return string

def racer_str(args, racer):
    string = '%s, %s, %s, %s, %s, %s' % (racer['bib'],
                                         racer['name'],
                                         racer['team'],
                                         racer['field'],
                                         racer['start'],
                                         racer['finish'])

    if args.showdata:
        string += ', %s' % (racer['data'])

    return string

def race_show(args):
    race = raceops.race_get()

    print(race_str(args, race))

def race_set(args):
    race = raceops.race_get()
    race['name'] = args.name
    raceops.race_modify(race)

def field_list(args):
    list = raceops.field_get_list()

    for field in list:
        print(field_str(args, field))

def field_show(args):
    try:
        list = raceops.field_get_racer_list(args.name)
    except LookupError as e:
        print(str(e))

    for racer in list:
        print(racer_str(args, racer))

def field_add(args):
    try:
        raceops.field_new({'name': args.name})
    except ValueError as e:
        print(str(e))

def field_rename(args):
    try:
        raceops.field_rename(args.name, args.new_name)
    except (LookupError, ValueError) as e:
        print(str(e))

def field_rm(args):
    try:
        raceops.field_delete(args.name)
    except(LookupError, RuntimeError) as e:
        print(str(e))

def racer_list(args):
    list = raceops.racer_get_list()

    for racer in list:
        print(racer_str(args, racer))

def racer_add(args):
    try:
        raceops.aacer_new({'bib': args.bib,
                           'name': args.name,
                           'team': args.team,
                           'field': args.field})
    except (LookupError, ValueError) as e:
        print(str(e))

def racer_rebib(args):
    try:
        raceops.racer_rebib(args.bib, args.new_bib)
    except (LookupError, ValueError) as e:
        print(str(e))

def racer_rename(args):
    try:
        racer = raceops.racer_get(args.bib)

        racer['name'] = args.new_name
        raceops.racer_modify(racer)
    except LookupError as e:
        print(str(e))

def racer_reteam(args):
    try:
        racer = raceops.racer_get(args.bib)

        racer['team'] = args.new_team
        raceops.racer_modify(racer)
    except LookupError as e:
        print(str(e))

def racer_refield(args):
    try:
        racer = raceops.racer_get(args.bib)

        racer['field'] = args.new_field
        raceops.racer_modify(racer)
    except LookupError as e:
        print(str(e))

def racer_rm(args):
    try:
        raceops.racer_delete(args.bib)
    except LookupError as e:
        print(str(e))

def make_parser():
    parser = argparse.ArgumentParser(description='SexyThyme, a race tracking program')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('--showdata', action='store_true',
                        help='show model instance data')
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
    showdata = ''

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
        self.handle_command(self.showdata + 'racefile race ' + arg)

    def do_field(self, arg):
        self.handle_command(self.showdata + 'racefile field ' + arg)

    def do_racer(self, arg):
        self.handle_command(self.showdata + 'racefile racer ' + arg)

    def do_toggledata(self, arg):
        if self.showdata == '':
            print('showing model data')
            self.showdata = '--showdata '
        else:
            print('hiding model data')
            self.showdata = ''

    def do_exit(self, arg):
        return True

    def do_quit(self, arg):
        return True

if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()

    raceops.race_init(args.racefile)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        shell = Shell(parser)
        shell.cmdloop()

    raceops.race_cleanup()
