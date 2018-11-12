#!/usr/bin/env python3

"""SexyThyme launch script

This is the execution entry point for the app.
"""

import argparse
import sys
from PyQt5.QtWidgets import QApplication
import common
from gui import SexyThymeMainWindow

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

def main():
    """The main() function creates the main window and starts the event loop."""
    parser = argparse.ArgumentParser(description=common.APPLICATION_NAME)
    parser.add_argument('--version', action='version',
                        version=common.APPLICATION_NAME + ' v' + common.VERSION)
    parser.add_argument('racefile', nargs='?',
                        help='Optional racefile to load')
    args = parser.parse_args()

    QApplication.setOrganizationName(common.ORGANIZATION_NAME)
    QApplication.setOrganizationDomain(common.ORGANIZATION_DOMAIN)
    QApplication.setApplicationName(common.APPLICATION_NAME)
    QApplication.setApplicationVersion(common.VERSION)

    app = QApplication(sys.argv)

    main_window = SexyThymeMainWindow(filename=args.racefile)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
