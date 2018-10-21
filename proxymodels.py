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
