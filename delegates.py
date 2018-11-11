#!/usr/bin/env python3

"""Delegate Classes

These are Qt delegate classes, for presenting/editing model items (for when a standard delegate
class just doesn't cut the mustard).
"""

from PyQt5.QtCore import QAbstractProxyModel, Qt
from PyQt5.QtSql import QSqlRelationalDelegate, QSqlRelationalTableModel
from PyQt5.QtWidgets import QComboBox, QItemDelegate
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

class SqlRelationalDelegate(QSqlRelationalDelegate):
    """QSqlRelationalDelegate that's corrected to work with proxy models

    The original QSqlRelationalDelegate doesn't work if you have any proxy model (even a
    QIdentityProxyModel) between your source model and your view.

    This one does work. It's gotten from:
    https://wiki.qt.io/QSqlRelationalDelegate-subclass-for-QSqlRelationalTableModel
    """

    def createEditor(self, parent, option, index): #pylint: disable=invalid-name
        """Return a combo box instance.

        The returned combo box instance should point to the proper relation model column.
        """
        sql_model = None
        if isinstance(index.model(), QSqlRelationalTableModel):
            sql_model = index.model()

        if sql_model:
            child_model = sql_model.relationModel(index.column())
        else:
            child_model = None

        if not child_model:
            proxy_model = None
            if isinstance(index.model(), QAbstractProxyModel):
                proxy_model = index.model()

            if proxy_model:
                sql_model = None
                if isinstance(proxy_model.sourceModel(), QSqlRelationalTableModel):
                    sql_model = proxy_model.sourceModel()

                if sql_model:
                    child_model = sql_model.relationModel(index.column())
                else:
                    child_model = None

        if not child_model:
            return QItemDelegate.createEditor(self, parent, option, index)

        column = child_model.fieldIndex(sql_model.relation(index.column()).displayColumn())

        combobox = QComboBox(parent)
        combobox.setModel(child_model)
        combobox.setModelColumn(column)
        combobox.installEventFilter(self)

        return combobox

    def setEditorData(self, editor, index): #pylint: disable=invalid-name
        """Populate the combo box.

        Set the current index of the combo box to be the current value in the model.
        """
        str_val = ''

        sql_model = None
        if isinstance(index.model(), QSqlRelationalTableModel):
            sql_model = index.model()

        if not sql_model:
            proxy_model = None
            if isinstance(index.model(), QAbstractProxyModel):
                proxy_model = index.model()

            if proxy_model:
                str_val = proxy_model.data(index)
        else:
            str_val = sql_model.data(index)

        if isinstance(editor, QComboBox):
            combobox = editor

        if not str_val or not isinstance(str_val, str) or not combobox:
            QItemDelegate.setEditorData(self, editor, index)
            return

        combobox.setCurrentIndex(combobox.findText(str_val))

    def setModelData(self, editor, model, index): #pylint: disable=invalid-name
        """Take the value in the combo box and write it to the model."""
        if not index.isValid():
            return

        sql_model = None
        if isinstance(model, QSqlRelationalTableModel):
            sql_model = model

        proxy_model = None
        if not sql_model:
            proxy_model = None
            if isinstance(model, QAbstractProxyModel):
                proxy_model = model

            if proxy_model:
                sql_model = proxy_model.sourceModel()

        if sql_model:
            child_model = sql_model.relationModel(index.column())
        else:
            child_model = None

        combobox = editor

        if not child_model or not combobox:
            QItemDelegate.setModelData(self, editor, model, index)
            return

        current_item = combobox.currentIndex()

        child_col_index = child_model.fieldIndex(sql_model.relation(index.column()).displayColumn())
        child_edit_index = child_model.fieldIndex(sql_model.relation(index.column()).indexColumn())

        child_col_data = child_model.data(child_model.index(current_item, child_col_index),
                                          Qt.DisplayRole)
        child_edit_data = child_model.data(child_model.index(current_item, child_edit_index),
                                           Qt.EditRole)

        if proxy_model:
            proxy_model.setData(index, child_col_data, Qt.DisplayRole)
            proxy_model.setData(index, child_edit_data, Qt.EditRole)
        else:
            sql_model.setData(index, child_col_data, Qt.DisplayRole)
            sql_model.setData(index, child_edit_data, Qt.EditRole)
