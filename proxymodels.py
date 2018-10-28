from PyQt5.QtCore import *

class ExtraColumnsProxyModel(QIdentityProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.extra_headers = []
        self.layout_change_persistent_indexes = []
        self.layout_change_proxy_columns = []
        self.proxyIndexes = []

    def appendColumn(self, header):
        self.extra_headers.append(header)

    def removeExtraColumn(self, idx):
        del self.extra_headers[idx]

    def extraColumnData(self, parent, row, extra_column, role=Qt.DisplayRole):
        raise NotImplemented

    def setExtraColumnData(self, parent, row, extra_column, data, role):
        return False

    def extraColumnDataChanged(self, parent, row, extra_column, roles):
        idx = QModelIndex(row, self.proxyColumnForExtraColumn(extra_column), parent)
        self.dataChanged.emit(idx, idx, roles)

    def mapToSource(self, proxy_index):
        if not proxy_index.isValid():
            return QModelIndex()

        column = proxy_index.column()
        if column >= self.sourceModel().columnCount():
            print('Returning invalid index in mapToSource')
            return QModelIndex()

        return super().mapToSource(proxy_index)

    def buddy(self, proxy_index):
        column = proxy_index.column()
        if column >= self.sourceModel().columnCount():
            return proxy_index

        return super().buddy(proxy_index)

    def sibling(self, row, column, idx):
        if row == idx.row() and column == idx.column():
            return idx

        return self.index(row, column, self.parent(idx))

    def mapSelectionToSource(self, selection):
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

            range = QItemSelectionRange(self.mapToSource(top_left), self.mapToSource(bottom_right))
            new_selection = []
            new_selectiom.append(range)
            source_selection.merge(new_selection, QItemSelectionModel.Select)

        return source_selection

    def columnCount(self, parent):
        return super().columnCount(parent) + len(self.extra_headers)

    def data(self, index, role):
        extra_col = self.extraColumnForProxyColumn(index.column())
        if extra_col >= 0 and self.extra_headers:
            return self.extraColumnData(index.parent(), index.row(), extra_col, role);

        return self.sourceModel().data(self.mapToSource(index), role);

    def setData(self, index, value, role):
        extra_col = self.extraColumnForProxyColumn(index.column())
        if extra_col >= 0 and self.extra_headers:
            return self.setExtraColumnData(index.parent(), index.row(), extra_col, role);

        return self.sourceModel().setData(self.mapToSource(index), value, role)

    def flags(self, index):
        extra_col = self.extraColumnForProxyColumn(index.column())
        if extra_col >= 0 and self.extra_headers:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

        return self.sourceModel().flags(self.mapToSource(index))

    def hasChildren(self, index):
        if index.column() > 0:
            return False

        return super().hasChildren(index)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            extra_col = self.extraColumnForProxyColumn(section)
            if extra_col >= 0:
                if role == Qt.DisplayRole:
                    return self.extra_headers[extra_col]
                return None

        return super().headerData(section, orientation, role)

    def index(self, row, column, parent):
        extra_col = self.extraColumnForProxyColumn(column)
        if extra_col >= 0:
            return self.createIndex(row, column, super().index(row, 0, parent).internalPointer());

        return super().index(row, column, parent);

    def parent(self, child):
        extra_col = self.extraColumnForProxyColumn(child.column());
        if extra_col >= 0:
            # Create an index for column 0 and use that to get the parent.
            proxySibling = self.createIndex(child.row(), 0, child.internalPointer());
            return super().parent(proxySibling)

        return super().parent(child);

    def extraColumnForProxyColumn(self, proxy_column):
        source_column_count = self.sourceModel().columnCount()
        if proxy_column >= source_column_count:
            return proxy_column - source_column_count

        return -1

    def proxyColumnForExtraColumn(self, extra_column):
        return self.sourceModel().columnCount() + extra_column

    def fieldIndex(self, field_name):
        return self.sourceModel().fieldIndex(field_name)

class RearrangeColumnsProxyModel(QIdentityProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.source_columns = []

    def setSourceColumns(self, columns):
        self.source_columns = columns

    def columnCount(self, parent):
        if not self.sourceModel():
            return 0

        return len(self.source_columns)

    def rowCount(self, parent):
        if not self.sourceModel():
            return 0;

        # The parent in the source model is on column 0, whatever swapping we are doing
        source_parent = self.mapToSource(parent).sibling(parent.row(), 0)
        return self.sourceModel().rowCount(source_parent)

    # We derive from QIdentityProxyModel simply to be able to use
    # its mapFromSource method which has friend access to createIndex() in the source model.

    def index(self, row, column, parent):
        # The parent in the source model is on column 0, whatever swapping we are doing
        source_parent = self.mapToSource(parent).sibling(parent.row(), 0)

        # Find the child in the source model, we need its internal pointer
        source_index = self.sourceModel().index(row, self.sourceColumnForProxyColumn(column), source_parent)
        if not source_index.isValid():
            return QModelIndex()

        return self.createIndex(row, column, source_index.internalPointer())

    def parent(self, child):
        source_index = self.mapToSource(child)
        source_parent = source_index.parent()
        if not source_parent.isValid():
            return QModelIndex()

        return createIndex(sourceParent.row(), 0, sourceParent.internalPointer());

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            source_col = self.sourceColumnForProxyColumn(section)
            return self.sourceModel().headerData(source_col, orientation, role)
        else:
            return super().headerData(section, orientation, role)

    def sibling(self, row, column, idx):
        if column >= self.source_columns.count():
            return QModelIndex()

        return self.index(row, column, idx.parent());

    def mapFromSource(self, source_index):
        if not source_index.isValid():
            return QModelIndex()

        proxy_column = self.proxyColumnForSourceColumn(source_index.column())
        return self.createIndex(source_index.row(), proxy_column, source_index.internalPointer())

    def mapToSource(self, proxy_index):
        if not proxy_index.isValid():
            return QModelIndex()

        # This is just an indirect way to call sourceModel.createIndex(row, source_column, pointer)
        fake_index = self.createIndex(proxy_index.row(), self.sourceColumnForProxyColumn(proxy_index.column()), proxy_index.internalPointer())
        return super().mapToSource(fake_index)

    def proxyColumnForSourceColumn(self, source_column):
        # If this is too slow, we could add a second QVector with index=logical_source_column value=desired_pos_in_proxy.
        try:
            return self.source_columns.index(source_column);
        except ValueError:
            return -1

    def sourceColumnForProxyColumn(self, proxy_column):
        return self.source_columns[proxy_column];

class SqlExtraColumnsProxyModel(ExtraColumnsProxyModel):
    def fieldIndex(self, field_name):
        try:
            extra_col = self.extra_headers.index(field_name)
        except ValueError:
            return self.sourceModel().fieldIndex(field_name)

        return self.proxyColumnForExtraColumn(extra_col)

class SqlRearrangeColumnsProxyModel(RearrangeColumnsProxyModel):
    def fieldIndex(self, field_name):
        try:
            return self.proxyColumnForSourceColumn(self.sourceModel().fieldIndex(field_name))
        except ValueError:
            return -1

class SqlSortFilterProxyModel(QSortFilterProxyModel):
    def fieldIndex(self, field_name):
        return self.sourceModel().fieldIndex(field_name)
