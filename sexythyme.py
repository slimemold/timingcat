#!/usr/bin/env python3

"""SexyThyme launch script

This is the execution entry point for the app.
"""

import argparse
import sys
from PyQt5.QtWidgets import QApplication
from common import APPLICATION_NAME, VERSION
from gui import SexyThymeMainWindow

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
