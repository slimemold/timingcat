from PyQt5.QtGui import *
from racemodel import *

def generate_finish_report(field_name):
    html = '<h1>Hello</h1>'
    html += '%s' % field_name

    document = QTextDocument()
    document.setHtml(html)

    return document
