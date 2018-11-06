#!/usr/bin/env python3

"""SexyThyme launch script

This is the execution entry point for the app.
"""

import argparse
import sys
from PyQt5.QtWidgets import QApplication
from common import APPLICATION_NAME, VERSION
from gui import SexyThymeMainWindow

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
    """The main() function creates the main window and starts the event loop."""
    parser = argparse.ArgumentParser(description=APPLICATION_NAME)
    parser.add_argument('--version', action='version',
                        version=APPLICATION_NAME + ' v' + VERSION)
    parser.add_argument('racefile', nargs='?',
                        help='Optional racefile to load')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName(APPLICATION_NAME)

    main_window = SexyThymeMainWindow(filename=args.racefile)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
