#!/usr/bin/env python3

"""Proxy Model Classes

This module contains proxy model subclasses. Some provide novel functionality (such as the
extra columns proxy model and the rearrange columns proxy model). Some are just QSqlTableModel
versions of proxy models (basically implementing the fieldIndex() method so that code can pretend
it is talking to a QSqlTableModel when it's really talking to one of our proxy models).

The ExtraColumnsProxyModel and RearrangeColumnsProxyModel are sloppily ported from C++ versions
gotten from https://github.com/KDE/kitemmodels.
"""

from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtCore import QItemSelection, QItemSelectionModel, QItemSelectionRange
from PyQt5.QtCore import QIdentityProxyModel, QSortFilterProxyModel
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

class ExtraColumnsProxyModel(QIdentityProxyModel):
    """ExtraColumnsProxyModel

    This proxy appends extra columns (after all existing columns).

    The proxy supports source models that have a tree structure.
    It also supports editing, and propagating changes from the source model.
    Row insertion/removal, column insertion/removal in the source model are supported.

    Not supported: adding/removing extra columns at runtime; having a different number of columns
    in subtrees; drag-n-drop support in the extra columns; moving columns.

    Derive from KExtraColumnsProxyModel, call appendColumn (typically in the constructor) for each
    extra column, and reimplement extraColumnData() to allow KExtraColumnsProxyModel to retrieve
    the data to show in the extra columns.

    If you want your new column(s) to be somewhere else than at the right of the existing columns,
    you can use a KRearrangeColumnsProxyModel on top.

    Author: David Faure, KDAB
    @since 5.13
    """

    def __init__(self, parent=None):
        """Base class constructor

        Remember to call setSourceModel afterwards, and appendColumn.
        """
        super().__init__(parent)

        self.extra_headers = []
        self.layout_change_persistent_indexes = []
        self.layout_change_proxy_columns = []

    def appendColumn(self, header): #pylint: disable=invalid-name
        """Append an extra column.

        @param header an optional text for the horizontal header
        This does not emit any signals - do it in the initial setup phase
        """
        self.extra_headers.append(header)

    def removeExtraColumn(self, index): #pylint: disable=invalid-name
        """Removes an extra column.

        @param index index of the extra column (starting from 0).
        This does not emit any signals - do it in the initial setup phase
        @since 5.24
        """
        del self.extra_headers[index]

    def extraColumnData(self, parent, row, extra_column, role=Qt.DisplayRole): #pylint: disable=invalid-name
        """Called by data() for extra columns.

        Reimplement this method to return the data for the extra columns.

        @param parent the parent model index in the proxy model (only useful in tree models)
        @param row the row number for which the proxy model is querying for data (child of @p
               parent, if set)
        @param extraColumn the number of the extra column, starting at 0 (this doesn't require
               knowing how many columns the source model has)
        @param role the role being queried
        @return the data at @p row and @p extraColumn
        """
        del parent, row, extra_column, role
        raise NotImplementedError

    def setExtraColumnData(self, parent, row, extra_column, data, role): #pylint: disable=invalid-name
        """Called by setData() for extra columns.

        Reimplement this method to set the data for the extra columns, if editing is supported.
        Remember to call extraColumnDataChanged() after changing the data storage.
        The default implementation returns false.
        """
        del parent, row, extra_column, data, role
        return False

    def extraColumnDataChanged(self, parent, row, extra_column, roles): #pylint: disable=invalid-name
        """Emit dataChanged signal for extra column.

        This method can be called by your derived class when the data in an extra column has
        changed. The use case is data that changes "by itself", unrelated to setData.
        """

        idx = QModelIndex(row, self.proxyColumnForExtraColumn(extra_column), parent)
        self.dataChanged.emit(idx, idx, roles)

    def mapToSource(self, proxy_index): #pylint: disable=invalid-name
        """Reimplemented."""
        if not proxy_index.isValid():
            return QModelIndex()

        column = proxy_index.column()
        if column >= self.sourceModel().columnCount():
            print('Returning invalid index in mapToSource')
            return QModelIndex()

        return super().mapToSource(proxy_index)

    def buddy(self, proxy_index):
        """Reimplemented."""
        column = proxy_index.column()
        if column >= self.sourceModel().columnCount():
            return proxy_index

        return super().buddy(proxy_index)

    def sibling(self, row, column, idx):
        """Reimplemented."""
        if row == idx.row() and column == idx.column():
            return idx

        return self.index(row, column, self.parent(idx))

    def mapSelectionToSource(self, selection): #pylint: disable=invalid-name
        """Reimplemented."""
        source_selection = QItemSelection()

        if not self.sourceModel():
            return source_selection

        source_column_count = self.sourceModel().columnCount()
        for item in selection:
            top_left = item.topLeft()
            top_left = top_left.sibling(top_left.row(), 0)

            bottom_right = item.bottomRight()
            if bottom_right.column() >= source_column_count:
                bottom_right = bottom_right.sibling(bottom_right.row(), source_column_count - 1)

            selection_range = QItemSelectionRange(self.mapToSource(top_left),
                                                  self.mapToSource(bottom_right))
            new_selection = []
            new_selection.append(selection_range)
            source_selection.merge(new_selection, QItemSelectionModel.Select)

        return source_selection

    def columnCount(self, parent): #pylint: disable=invalid-name
        """Reimplemented."""
        return super().columnCount(parent) + len(self.extra_headers)

    def data(self, index, role):
        """Reimplemented."""
        extra_col = self.extraColumnForProxyColumn(index.column())
        if extra_col >= 0 and self.extra_headers:
            return self.extraColumnData(index.parent(), index.row(), extra_col, role)

        return self.sourceModel().data(self.mapToSource(index), role)

    def setData(self, index, value, role): #pylint: disable=invalid-name
        """Reimplemented."""
        extra_col = self.extraColumnForProxyColumn(index.column())
        if extra_col >= 0 and self.extra_headers:
            return self.setExtraColumnData(index.parent(), index.row(), extra_col, value, role)

        return self.sourceModel().setData(self.mapToSource(index), value, role)

    def flags(self, index):
        """Reimplemented."""
        extra_col = self.extraColumnForProxyColumn(index.column())
        if extra_col >= 0 and self.extra_headers:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

        return self.sourceModel().flags(self.mapToSource(index))

    def hasChildren(self, index): #pylint: disable=invalid-name
        """Reimplemented."""
        if index.column() > 0:
            return False

        return super().hasChildren(index)

    def headerData(self, section, orientation, role): #pylint: disable=invalid-name
        """Reimplemented."""
        if orientation == Qt.Horizontal:
            extra_col = self.extraColumnForProxyColumn(section)
            if extra_col >= 0:
                if role == Qt.DisplayRole:
                    return self.extra_headers[extra_col]
                return None

        return super().headerData(section, orientation, role)

    def index(self, row, column, parent):
        """Reimplemented."""
        extra_col = self.extraColumnForProxyColumn(column)
        if extra_col >= 0:
            return self.createIndex(row, column, super().index(row, 0, parent).internalPointer())

        return super().index(row, column, parent)

    def parent(self, child):
        """Reimplemented."""
        extra_col = self.extraColumnForProxyColumn(child.column())
        if extra_col >= 0:
            # Create an index for column 0 and use that to get the parent.
            proxy_sibling = self.createIndex(child.row(), 0, child.internalPointer())
            return super().parent(proxy_sibling)

        return super().parent(child)

    def extraColumnForProxyColumn(self, proxy_column): #pylint: disable=invalid-name
        """Returns the extra column number (0, 1, ...) for a given column number of the proxy model.

        This basically means subtracting the amount of columns in the source model.
        """
        source_column_count = self.sourceModel().columnCount()
        if proxy_column >= source_column_count:
            return proxy_column - source_column_count

        return -1

    def proxyColumnForExtraColumn(self, extra_column): #pylint: disable=invalid-name
        """Returns the proxy column number for a given extra column number (starting at 0).

        This basically means adding the amount of columns in the source model.
        """
        return self.sourceModel().columnCount() + extra_column

class RearrangeColumnsProxyModel(QIdentityProxyModel):
    """RearrangeColumnsProxyModel

    This proxy shows specific columns from the source model, in any order.
    This allows to reorder columns, as well as not showing all of them.

    The proxy supports source models that have a tree structure.
    It also supports editing, and propagating changes from the source model.

    Showing the same source column more than once is not supported.

    Author: David Faure, KDAB
    @since 5.12
    """

    def __init__(self, parent=None):
        """Create a KRearrangeColumnsProxyModel proxy.

        Remember to call setSourceModel afterwards.
        """
        super().__init__(parent)

        self.source_columns = []

    def setSourceColumns(self, columns): #pylint: disable=invalid-name
        """Set the chosen source columns.

        Set the chosen source columns, in the desired order for the proxy columns
        columns[proxyColumn=0] is the source column to show in the first proxy column, etc.

        Example: [2, 1]
        This examples configures the proxy to hide column 0, show column 2 from the source model,
        then show column 1 from the source model.
        """
        self.source_columns = columns

    def columnCount(self, parent): #pylint: disable=invalid-name
        """Reimplemented."""
        del parent

        if not self.sourceModel():
            return 0

        return len(self.source_columns)

    def rowCount(self, parent): #pylint: disable=invalid-name
        """Reimplemented."""
        if not self.sourceModel():
            return 0

        # The parent in the source model is on column 0, whatever swapping we are doing
        source_parent = self.mapToSource(parent).sibling(parent.row(), 0)
        return self.sourceModel().rowCount(source_parent)

    # We derive from QIdentityProxyModel simply to be able to use
    # its mapFromSource method which has friend access to createIndex() in the source model.

    def index(self, row, column, parent):
        """Reimplemented."""
        # The parent in the source model is on column 0, whatever swapping we are doing
        source_parent = self.mapToSource(parent).sibling(parent.row(), 0)

        # Find the child in the source model, we need its internal pointer
        source_index = self.sourceModel().index(row, self.sourceColumnForProxyColumn(column),
                                                source_parent)
        if not source_index.isValid():
            return QModelIndex()

        return self.createIndex(row, column, source_index.internalPointer())

    def parent(self, child):
        """Reimplemented."""
        source_index = self.mapToSource(child)
        source_parent = source_index.parent()
        if not source_parent.isValid():
            return QModelIndex()

        return self.createIndex(source_parent.row(), 0, source_parent.internalPointer())

    def headerData(self, section, orientation, role): #pylint: disable=invalid-name
        """Reimplemented."""
        if orientation == Qt.Horizontal:
            source_col = self.sourceColumnForProxyColumn(section)
            return self.sourceModel().headerData(source_col, orientation, role)
        else:
            return super().headerData(section, orientation, role)

    def sibling(self, row, column, idx):
        """Reimplemented."""
        if column >= self.source_columns.count():
            return QModelIndex()

        return self.index(row, column, idx.parent())

    def mapFromSource(self, source_index): #pylint: disable=invalid-name
        """Reimplemented."""
        if not source_index.isValid():
            return QModelIndex()

        proxy_column = self.proxyColumnForSourceColumn(source_index.column())
        return self.createIndex(source_index.row(), proxy_column, source_index.internalPointer())

    def mapToSource(self, proxy_index): #pylint: disable=invalid-name
        """Reimplemented."""
        if not proxy_index.isValid():
            return QModelIndex()

        # This is just an indirect way to call sourceModel.createIndex(row, source_column, pointer)
        column = self.sourceColumnForProxyColumn(proxy_index.column())
        fake_index = self.createIndex(proxy_index.row(), column, proxy_index.internalPointer())
        return super().mapToSource(fake_index)

    def proxyColumnForSourceColumn(self, source_column): #pylint: disable=invalid-name
        """Return proxy column, given source column."""
        # If this is too slow, we could add a second list with index=logical_source_column
        # value=desired_pos_in_proxy.
        try:
            return self.source_columns.index(source_column)
        except ValueError:
            return -1

    def sourceColumnForProxyColumn(self, proxy_column): #pylint: disable=invalid-name
        """Return source column, given proxy column."""
        return self.source_columns[proxy_column]

class SqlExtraColumnsProxyModel(ExtraColumnsProxyModel):
    """SqlExtraColumnsProxyModel

    This is just ExtraColumnsProxyModel, but with fieldIndex(), so that it looks like a
    QSqlTableModel.
    """

    def fieldIndex(self, field_name): #pylint: disable=invalid-name
        """Call sourceModel().fieldIndex()

        We assume that the source model is a QSqlTableModel (which is the whole point of this
        class).
        """
        try:
            extra_col = self.extra_headers.index(field_name)
        except ValueError:
            return self.sourceModel().fieldIndex(field_name)

        return self.proxyColumnForExtraColumn(extra_col)

class SqlRearrangeColumnsProxyModel(RearrangeColumnsProxyModel):
    """SqlRearrangeColumnsProxyModel

    This is just RearrangeColumnsProxyModel, but with fieldIndex(), so that it looks like a
    QSqlTableModel.
    """

    def fieldIndex(self, field_name): #pylint: disable=invalid-name
        """Call sourceModel().fieldIndex()

        We assume that the source model is a QSqlTableModel (which is the whole point of this
        class).
        """
        try:
            return self.proxyColumnForSourceColumn(self.sourceModel().fieldIndex(field_name))
        except ValueError:
            return -1

class SqlSortFilterProxyModel(QSortFilterProxyModel):
    """SqlSortFilterProxyModel

    This is just QSortFilterProxyModel, but with fieldIndex(), so that it looks like a
    QSqlTableModel.
    """

    def fieldIndex(self, field_name): #pylint: disable=invalid-name
        """Call sourceModel().fieldIndex()

        We assume that the source model is a QSqlTableModel (which is the whole point of this
        class).
        """
        return self.sourceModel().fieldIndex(field_name)
