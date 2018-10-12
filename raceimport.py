#!/usr/bin/env python3

import argparse
import csv
import os
import raceops
import sys

from common import ask_yes_no, VERSION

class RaceImporter(object):
    pass

class FileRaceImporter(RaceImporter):
    def read(self, in_file):
        raise NotImplemented()

class BikeRegRaceImporter(FileRaceImporter):
    def read(self, in_file):
        reader = csv.reader(in_file)

        # Skip the heading row.
        next(reader)

        for row in reader:
            _, bib, field, _, first_name, _, last_name, _, team, *_ = row
            name = first_name + ' ' + last_name

            # BikeReg lists One-day License holders twice, and the second
            # listing is missing the bib#, and instead has:
            # "License - 1/1/2018 - One-day License" as the field. Skip over
            # these entries.
            if 'One-day License' in field:
                continue

            # Add new field if we haven't seen it before.
            if not raceops.field_get(field):
                raceops.field_new({'name': field})

            raceops.racer_new({'bib': bib,
                       'name': name,
                       'team': team,
                       'field': field})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SexyThyme race importer tool')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('racefile', help='race file to import into')
    parser.add_argument('--bikeregfile', help='file to import from')

    args = parser.parse_args()

    if os.path.isfile(args.racefile):
        if ask_yes_no('Race file %s already exists. Overwrite?' %
                         (args.racefile), default="no"):
            os.remove(args.racefile)
        else:
            sys.exit(0)

    if args.bikeregfile:
        importer = BikeRegRaceImporter()
        import_filename = args.bikeregfile

    if not os.path.isfile(import_filename):
        print('File %s does not exist' % (args.bikeregfile))
        usage()

    if not importer:
        print('No importer found. Need one of --bikeregfile')
        usage()

    with open(import_filename) as import_file:
        raceops.race_init(args.racefile)
        importer.read(import_file)
        raceops.race_cleanup()
