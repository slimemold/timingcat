#!/usr/bin/env python3

"""BikeReg Classes

This module contains helper functions for importing race data from BikeReg.com.
"""

import csv
import common

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

def import_csv(modeldb, filename):
    """Import a BikeReg csv racers list export file.

    Open BikeReg csv export file and populate the field and racer lists.
    """
    racer_table_model = modeldb.racer_table_model

    with open(filename) as import_file:
        reader = csv.reader(import_file)

        # Skip the heading row.
        next(reader)

        for row in reader:
            age, bib, field, _, first_name, _, last_name, _, team, category, *_ = row

            # BikeReg lists One-day License holders twice, and the second
            # listing is missing the bib#, and instead has:
            # "License - 1/1/2018 - One-day License" as the field. Skip over
            # these entries.
            if 'One-day License' in field:
                continue

            racer_table_model.add_racer(bib, first_name, last_name, field, category, team, age)
