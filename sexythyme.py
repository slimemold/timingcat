#!/usr/bin/env python3

import argparse
import sys
from PyQt5.QtWidgets import QApplication
from common import CONST_APPLICATION_NAME, CONST_VERSION
from gui import SexyThymeMainWindow

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=CONST_APPLICATION_NAME)
    parser.add_argument('--version', action='version',
                        version=CONST_APPLICATION_NAME + ' v' + CONST_VERSION)
    parser.add_argument('racefile', nargs='?',
                        help='Optional racefile to load')
    args = parser.parse_args()

    app = QApplication(sys.argv)

    main = SexyThymeMainWindow(filename=args.racefile)
    main.show()

    sys.exit(app.exec_())
