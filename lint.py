#!/usr/bin/env python3

"""Linting helper script

This is just a wrapper for launching pylint on this package.
"""

import os
import pylint.lint
import common

__copyright__ = '''
    Copyright (C) 2018-2019 Andrew Chew

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

def main():
    """The main() function just runs pylint."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    run_dir, package_name = os.path.split(script_dir)

    os.chdir(run_dir)

    pylint_opts = []
    pylint_opts.append('--spelling-private-dict-file=%s' %
                       os.path.join(script_dir, 'pylint.dict'))
    pylint_opts.append(package_name)
    pylint.lint.Run(pylint_opts)

if __name__ == '__main__':
    main()
