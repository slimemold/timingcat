#!/usr/bin/env python3

import logging
import sys
from PyQt5.QtWidgets import QApplication, QWidget

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = QWidget()
    w.show()
 
    sys.exit(app.exec_())

