#!/usr/bin/env python3

import argparse
import cmd
import os
import logging
import raceimport
import re
import sys
import raceops

from common import VERSION, ask_yes_no
from datetime import datetime, time

logger = logging.getLogger(__name__)

TIME_FORMAT='%H:%M:%S:%f'

def race_str(args, race):
    string = '%s, %s' % (race['key'], race['value'])

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
                                         time.strftime(racer['start'],
                                                       TIME_FORMAT),
                                         time.strftime(racer['finish'],
                                                       TIME_FORMAT))

    if args.showdata:
        string += ', %s' % (racer['data'])

    return string

def result_str(args, result):
    string = '%s, "%s", %s' % (result['id'],
                               result['scratchpad'],
                               time.strftime(result['finish'], TIME_FORMAT))

    if args.showdata:
        string += ', %s' % (result['data'])

    return string

def race_show(args):
    race = raceops.race_get()

    print('Fields: %s' % (raceops.field_get_count()))
    print('Racers: %s' % (raceops.racer_get_count()))
    print(race_str(args, race))

def race_set(args):
    race = raceops.race_get()
    race['key'] = args.key
    race['value'] = args.value
    raceops.race_modify(race)

def race_reset(args):
    print('This operation will delete %s fields and %s racers.' %
          (raceops.field_get_count(), raceops.racer_get_count()))
    if not ask_yes_no('Delete everything and start over?', default='no'):
        print('Aborted')
        return

    raceops.race_reset()

def field_list(args):
    list = raceops.field_get_list()

    for field in list:
        print(field_str(args, field))

    print('Total: ' + str(raceops.field_get_count()))

def field_show(args):
    try:
        list = raceops.field_get_racer_list(args.name)
    except LookupError as e:
        print(str(e))

    for racer in list:
        print(racer_str(args, racer))

    print('Total: ' + str(raceops.field_get_racer_count(args.name)))

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

def field_rmempty(args):
    if not ask_yes_no('Remove all empty field(s)?', default='no'):
        print('Aborted')
        return

    fields_not_deleted = raceops.field_delete_empty()

    print('%s fields not deleted (not empty)' % (fields_not_deleted))

def racer_list(args):
    list = raceops.racer_get_list()

    for racer in list:
        print(racer_str(args, racer))

    print('Total: ' + str(raceops.racer_get_count()))

def racer_add(args):
    try:
        raceops.racer_new({'bib': args.bib,
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

def racer_restart(args):
    try:
        racer = raceops.racer_get(args.bib)

        racer['start'] = datetime.time(datetime.strptime(args.new_start,
                                                         TIME_FORMAT))
        raceops.racer_modify(racer)
    except LookupError as e:
        print(str(e))

def racer_refinish(args):
    try:
        racer = raceops.racer_get(args.bib)

        racer['finish'] = datetime.time(datetime.strptime(args.new_finish,
                                                          TIME_FORMAT))
        raceops.racer_modify(racer)
    except LookupError as e:
        print(str(e))

def racer_rm(args):
    try:
        raceops.racer_delete(args.bib)
    except LookupError as e:
        print(str(e))

def racer_fieldrmall(args):
    count = raceops.field_get_racer_count(args.name)
    if not ask_yes_no('Remove all %s racer(s) from field "%s"?' % (count, args.name), default='no'):
        print('Aborted')
        return

    try:
        count = raceops.racer_delete_all_from_field(args.name)
    except LookupError as e:
        print(str(e))

    print('Removed %s racers' % count)

def racer_fieldrestart(args):
    count = raceops.field_get_racer_count(args.name)
    if not ask_yes_no('Set start time %s for all %s racer(s) from field "%s"?' % (args.new_start, count, args.name), default='no'):
        print('Aborted')
        return

    try:
        raceops.racer_set_start_from_field(args.name,
                                           datetime.time(datetime.strptime(args.new_start, TIME_FORMAT)))
    except LookupError as e:
        print(str(e))

    print('Set start time %s for %s racers' % (args.new_start, count))

def racer_fieldrefinish(args):
    count = raceops.field_get_racer_count(args.name)
    if not ask_yes_no('Set finish time %s for all %s racer(s) from field "%s"?' % (args.new_finish, count, args.name), default='no'):
        print('Aborted')
        return

    try:
        raceops.racer_set_finish_from_field(args.name,
                                            datetime.time(datetime.strptime(args.new_finish, TIME_FORMAT)))
    except LookupError as e:
        print(str(e))

    print('Set finish time %s for %s racers' % (args.new_finish, count))

def racer_rmall(args):
    count = raceops.racer_get_count()
    if not ask_yes_no('Remove all %s racer(s)?' % (count), default='no'):
        print('Aborted')
        return

    raceops.racer_delete_all()

def result_list(args):
    list = raceops.result_get_list()

    for result in list:
        print(result_str(args, result))

    print('Total: ' + str(raceops.result_get_count()))

def result_add(args):
    try:
        result = {}
        if args.scratchpad:
            result['scratchpad'] = args.scratchpad
        if args.finish:
            result['finish'] = datetime.time(datetime.strptime(args.finish,
                                                               TIME_FORMAT))
        raceops.result_new(result)
    except (LookupError, ValueError) as e:
        print(str(e))

def result_rescratchpad(args):
    try:
        result = raceops.result_get(args.id)

        result['scratchpad'] = args.new_scratchpad
        raceops.result_modify(result)
    except LookupError as e:
        print(str(e))

def result_refinish(args):
    try:
        result = raceops.result_get(args.id)

        result['finish'] = datetime.time(datetime.strptime(args.new_finish,
                                                           TIME_FORMAT))
        raceops.result_modify(result)
    except LookupError as e:
        print(str(e))

def result_rm(args):
    try:
        raceops.result_delete(args.id)
    except LookupError as e:
        print(str(e))

def result_rmall(args):
    count = raceops.result_get_count()
    if not ask_yes_no('Remove all %s result(s)?' % (count), default='no'):
        print('Aborted')
        return

    raceops.result_delete_all()

def result_commit(args):
    try:
        raceops.result_commit(args.id)
    except (LookupError, ValueError) as e:
        print(str(e))

def import_bikereg(args):
    if not os.path.isfile(args.csvfile):
        print('File %s does not exist' % (args.csvfile))
        return

    if not ask_yes_no('Overwrite race file %s with import data?' % (args.racefile), default='no'):
        print('Aborted')
        return

    raceops.race_cleanup()
    os.remove(args.racefile)
    raceops.race_init(args.racefile)

    importer = raceimport.BikeRegRaceImporter()
    with open(args.csvfile) as import_file:
        importer.read(import_file)

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
    race_parser.set_defaults(func=race_show)
    race_subparsers = race_parser.add_subparsers(help='race command help')

    # Create the parser for the "race show" command.
    subparser = race_subparsers.add_parser('show')
    subparser.set_defaults(func=race_show)

    # Create the parser for the "race set" command.
    subparser = race_subparsers.add_parser('set')
    subparser.set_defaults(func=race_set)
    subparser.add_argument('key', help='name of property')
    subparser.add_argument('value', help='value of property')

    # Create the parser for the "race reset" command.
    subparser = race_subparsers.add_parser('reset')
    subparser.set_defaults(func=race_reset)

    # Create the parser for the "field" command.
    field_parser = subparsers.add_parser('field')
    field_parser.set_defaults(func=field_list)
    field_subparsers = field_parser.add_subparsers(help='field command help')

    # Create the parser for the "field list" command.
    subparser = field_subparsers.add_parser('list')
    subparser.set_defaults(func=field_list)

    # Create the parser for the "field show" command.
    subparser = field_subparsers.add_parser('show')
    subparser.set_defaults(func=field_show)
    subparser.add_argument('name', help='used to identify the field')

    # Create the parser for the "field add" command.
    subparser = field_subparsers.add_parser('add')
    subparser.set_defaults(func=field_add)
    subparser.add_argument('name', help='used to identify the field')

    # Create the parser for the "field rename" command.
    subparser = field_subparsers.add_parser('rename')
    subparser.set_defaults(func=field_rename)
    subparser.add_argument('name', help='used to identify the field')
    subparser.add_argument('new_name', help='new name')

    # Create the parser for the "field rm" command.
    subparser = field_subparsers.add_parser('rm')
    subparser.set_defaults(func=field_rm)
    subparser.add_argument('name', help='used to identify the field')

    # Create the parser for the "field rmempty" command.
    subparser = field_subparsers.add_parser('rmempty')
    subparser.set_defaults(func=field_rmempty)

    # Create the parser for the "field racerrmall" command.
    # Note this is the same as "racer fieldrmall".
    subparser = field_subparsers.add_parser('racerrmall')
    subparser.set_defaults(func=racer_fieldrmall)
    subparser.add_argument('name', help='used to identify the field')

    # Create the parser for the "field racerrestart" command.
    # Note this is the same as "racer fieldrestart".
    subparser = field_subparsers.add_parser('racerrestart')
    subparser.set_defaults(func=racer_fieldrestart)
    subparser.add_argument('name', help='used to identify the field')
    subparser.add_argument('new_start', help='new start time')

    # Create the parser for the "field racerrefinish" command.
    # Note this is the same as "racer fieldrefinish".
    subparser = field_subparsers.add_parser('racerrefinish')
    subparser.set_defaults(func=racer_fieldrefinish)
    subparser.add_argument('name', help='used to identify the field')
    subparser.add_argument('new_finish', help='new finish time')

    # Create the parser for the "racer" command.
    racer_parser = subparsers.add_parser('racer')
    racer_parser.set_defaults(func=racer_list)
    racer_subparsers = racer_parser.add_subparsers(help='racer command help')

    # Create the parser for the "racer list" command.
    subparser = racer_subparsers.add_parser('list')
    subparser.set_defaults(func=racer_list)

    # Create the parser for the "racer add" command.
    subparser = racer_subparsers.add_parser('add')
    subparser.set_defaults(func=racer_add)
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('name', help='racer\'s full name')
    subparser.add_argument('team', help='racer\'s team name')
    subparser.add_argument('field', help='racer\'s field name')

    # Create the parser for the "racer rebib" command.
    subparser = racer_subparsers.add_parser('rebib')
    subparser.set_defaults(func=racer_rebib)
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_bib', help='new bib')

    # Create the parser for the "racer rename" command.
    subparser = racer_subparsers.add_parser('rename')
    subparser.set_defaults(func=racer_rename)
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_name', help='new name')

    # Create the parser for the "racer reteam" command.
    subparser = racer_subparsers.add_parser('reteam')
    subparser.set_defaults(func=racer_reteam)
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_team', help='new team')

    # Create the parser for the "racer refield" command.
    subparser = racer_subparsers.add_parser('refield')
    subparser.set_defaults(func=racer_refield)
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_field', help='new field name')

    # Create the parser for the "racer restart" command.
    subparser = racer_subparsers.add_parser('restart')
    subparser.set_defaults(func=racer_restart)
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_start', help='new start time')

    # Create the parser for the "racer refinish" command.
    subparser = racer_subparsers.add_parser('refinish')
    subparser.set_defaults(func=racer_refinish)
    subparser.add_argument('bib', help='used to identify the racer')
    subparser.add_argument('new_finish', help='new finish time')

    # Create the parser for the "racer rm" command.
    subparser = racer_subparsers.add_parser('rm')
    subparser.set_defaults(func=racer_rm)
    subparser.add_argument('name', help='used to identify the racer')

    # Create the parser for the "racer fieldrmall" command.
    subparser = racer_subparsers.add_parser('fieldrmall')
    subparser.set_defaults(func=racer_fieldrmall)
    subparser.add_argument('name', help='used to identify the field')

    # Create the parser for the "racer fieldrestartrmall" command.
    subparser = racer_subparsers.add_parser('fieldrestart')
    subparser.set_defaults(func=racer_fieldrestart)
    subparser.add_argument('name', help='used to identify the field')
    subparser.add_argument('new_start', help='new start time')

    # Create the parser for the "racer fieldrefinishrmall" command.
    subparser = racer_subparsers.add_parser('fieldrefinish')
    subparser.set_defaults(func=racer_fieldrefinish)
    subparser.add_argument('name', help='used to identify the field')
    subparser.add_argument('new_finish', help='new finish time')

    # Create the parser for the "racer rmall" command.
    subparser = racer_subparsers.add_parser('rmall')
    subparser.set_defaults(func=racer_rmall)

    # Create the parser for the "result" command.
    result_parser = subparsers.add_parser('result')
    result_parser.set_defaults(func=result_list)
    result_subparsers = result_parser.add_subparsers(help='result command help')

    # Create the parser for the "result list" command.
    subparser = result_subparsers.add_parser('list')
    subparser.set_defaults(func=result_list)

    # Create the parser for the "result add" command.
    subparser = result_subparsers.add_parser('add')
    subparser.set_defaults(func=result_add)
    subparser.add_argument('scratchpad', nargs='?', help='bib scratchpad')
    subparser.add_argument('finish', nargs='?', help='result\'s full name')

    # Create the parser for the "result rescratchpad" command.
    subparser = result_subparsers.add_parser('rescratchpad')
    subparser.set_defaults(func=result_rescratchpad)
    subparser.add_argument('id', help='used to identify the result')
    subparser.add_argument('new_scratchpad', help='new scratchpad')

    # Create the parser for the "result refinish" command.
    subparser = result_subparsers.add_parser('refinish')
    subparser.set_defaults(func=result_refinish)
    subparser.add_argument('id', help='used to identify the result')
    subparser.add_argument('new_finish', help='new finish')

    # Create the parser for the "result rm" command.
    subparser = result_subparsers.add_parser('rm')
    subparser.set_defaults(func=result_rm)
    subparser.add_argument('id', help='used to identify the result')

    # Create the parser for the "result rmall" command.
    subparser = result_subparsers.add_parser('rmall')
    subparser.set_defaults(func=result_rmall)

    # Create the parser for the "result commit" command.
    subparser = result_subparsers.add_parser('commit')
    subparser.set_defaults(func=result_commit)
    subparser.add_argument('id', help='result id')

    # Create the parser for the "import" command.
    import_parser = subparsers.add_parser('import')
    import_subparsers = import_parser.add_subparsers(help='import command help')

    # Create the parser for the "import bikereg" command.
    subparser = import_subparsers.add_parser('bikereg')
    subparser.set_defaults(func=import_bikereg)
    subparser.add_argument('csvfile', help='bikereg csv file')

    return parser

class Shell(cmd.Cmd):
    intro = 'SexyThyme: Type help or ? to list commands.\n'
    prompt = '(sexythyme) '
    parser = None
    racefile = None
    showdata = ''

    def __init__(self, parser, racefile):
        super().__init__()
        self.parser = parser
        self.racefile = racefile
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
        self.handle_command(self.showdata + self.racefile + ' race ' + arg)

    def do_field(self, arg):
        self.handle_command(self.showdata + self.racefile + ' field ' + arg)

    def do_racer(self, arg):
        self.handle_command(self.showdata + self.racefile + ' racer ' + arg)

    def do_result(self, arg):
        self.handle_command(self.showdata + self.racefile + ' result ' + arg)

    def do_import(self, arg):
        self.handle_command(self.showdata + self.racefile + ' import ' + arg)

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
        shell = Shell(parser, args.racefile)
        shell.cmdloop()

    raceops.race_cleanup()
