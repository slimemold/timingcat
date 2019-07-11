#!/usr/bin/env python3

"""SexyThyme launch script

This is the execution entry point for the app.
"""

import argparse
import os
import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
import common
from gui import SexyThymeMainWindow

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

def excepthook(exc_type, exc_value, exc_traceback):
    """Show the exception in an error dialog.

    Also, call the old except hook to get the normal behavior as well.
    """
    exception_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    QMessageBox.critical(None, exc_type.__name__,
                         'Unhandled exception (please send to %s)!\n\n%s' % (common.EMAIL,
                                                                             exception_str))

    sys.excepthook = sys.__excepthook__
    sys.excepthook(exc_type, exc_value, exc_traceback)

# Install our custom exception hook.
sys.excepthook = excepthook

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

    # Set our current working directory to the documents folder. We need to do this because running
    # a pyinstaller version of this app has the current working directory as "/" (at least, on OS X)
    # which is always wrong. Therefore, always just start it off at somewhere sane and writable.
    os.chdir(common.get_documents_dir())

    main_window = SexyThymeMainWindow(filename=args.racefile)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
