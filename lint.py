#!/usr/bin/env python3

"""Linting helper script

This is just a wrapper for launching pylint on this package.
"""

import os
import pylint.lint
from common import VERSION

__author__ = 'Andrew Chew'
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
__credits__ = ['Andrew Chew', 'Colleen Chew']
__license__ = 'GPLv3'
__version__ = VERSION
__maintainer__ = 'Andrew Chew'
__email__ = 'andrew@5rcc.com'
__status__ = 'Development'

def main():
    """The main() function just runs pylint."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    run_dir, package_name = os.path.split(script_dir)

    os.chdir(run_dir)

    pylint_opts = []
    pylint_opts.append(package_name)
    pylint.lint.Run(pylint_opts)

if __name__ == '__main__':
    main()
