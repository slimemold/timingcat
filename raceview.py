from PyQt5.QtGui import *
from PyQt5.QtSql import QSqlRelationalDelegate
from PyQt5.QtWidgets import *
from common import *
from proxymodels import *
from racemodel import *

# Add a "Finished" column for total racers that have a finish time, and a
# "Total" column to show total racers in that field.
class FieldProxyModel(SqlExtraColumnsProxyModel):
    FINISHED_SECTION = 0
    TOTAL_SECTION = 1
    STATUS_SECTION = 2

    def __init__(self):
        super().__init__()

        self.appendColumn('Finished')
        self.appendColumn('Total')
        self.appendColumn('Status')

    def extraColumnData(self, parent, row, extraColumn, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            field_table_model = self.sourceModel()
            racer_table_model = self.sourceModel().modeldb.racer_table_model

            field_name = field_table_model.record(row).value(FieldTableModel.NAME)

            total = racer_table_model.racer_count_total_in_field(field_name)
            finished = racer_table_model.racer_count_finished_in_field(field_name)

            if extraColumn == self.FINISHED_SECTION:
                return finished
            elif extraColumn == self.TOTAL_SECTION:
                return total
            elif extraColumn == self.STATUS_SECTION:
                if total == 0:
                    return 'Empty'
                elif (finished < total):
                    return 'In Progress (%s%%)' % int(round(finished * 100 / total))
                else:
                    return 'Complete'

        return None

    def data(self, index, role):
        if role == Qt.BackgroundRole:
            row = index.row()

            field_table_model = self.sourceModel()
            racer_table_model = self.sourceModel().modeldb.racer_table_model

            field_name = field_table_model.record(row).value(FieldTableModel.NAME)

            total = racer_table_model.racer_count_total_in_field(field_name)
            finished = racer_table_model.racer_count_finished_in_field(field_name)

            if total != 0:
                if finished == total:
                    return QBrush(Qt.green)
                elif finished > 0:
                    return QBrush(Qt.yellow)

        return super().data(index, role)

class FieldTableView(QTableView):
    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.setModel(self.modeldb.field_table_model)
        self.setupProxyModel()

        self.setWindowTitle('Fields')

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(self.model().fieldIndex(FieldTableModel.NAME),
                          Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex(FieldTableModel.ID))

        # For each field, we make a racer in field table view ahead of time.
        # Note that we call dataChanged here because the initial reading of
        # the model is not considered a data change, but we need to do this
        # anyway to populate racer_in_field_table_view_dict.
        self.racer_in_field_table_view_dict = {}
        self.dataChanged()

        # Signals/slots to handle racer in field table views.
        self.modeldb.racer_table_model.dataChanged.connect(self.updateNonModelColumns)
        self.doubleClicked.connect(self.handleShowRacerInFieldTableView)


    def setupProxyModel(self):
        # Use a proxy model so we can add some interesting columns.
        proxyModel = FieldProxyModel()
        proxyModel.setSourceModel(self.model())

        self.setModel(proxyModel)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.handleDelete()

        return super().keyPressEvent(event)

    def showEvent(self, event):
        self.resize(520, 600)

    def hideEvent(self, event):
        self.visibleChanged.emit(False)

    def handleDelete(self):
        model = self.selectionModel().model()
        item_selection = self.selectionModel().selection()
        selection_list = self.selectionModel().selectedRows()

        field_table_model = self.modeldb.field_table_model
        racer_table_model = self.modeldb.racer_table_model

        field_count = len(selection_list)
        racer_count = 0
        for selection in selection_list:
            field_record = field_table_model.record(selection.row())
            field_id = field_record.value(FieldTableModel.ID)

            racer_count += racer_table_model.racer_count_total_in_field(field_id)

        # Confirm deletion.
        msg_box = QMessageBox()
        msg_box.setWindowTitle(APPLICATION_NAME)
        msg_box.setText('Deleting %s' %
                        pretty_list([pluralize('field', field_count),
                                     pluralize('racer', racer_count)]))
        msg_box.setInformativeText('Do you really want to delete?')
        msg_box.setStandardButtons(QMessageBox.Ok |
                                   QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Cancel)
        msg_box.setIcon(QMessageBox.Information)

        if msg_box.exec() != QMessageBox.Ok:
            return

        # Remove rows from large to small, because the rows are removed
        # immediately, and cause the rest of the rows to shift, invalidating
        # any row number that's higher than the currently removed one.
        selection_list.sort(key=lambda selection: selection.row(), reverse=True)
        for selection in selection_list:
            field_record = field_table_model.record(selection.row())
            field_id = field_record.value(FieldTableModel.ID)

            racer_in_field_table_view = self.racer_in_field_table_view_dict[field_id]
            racer_in_field_table_model = racer_in_field_table_view.model()

            # Have to remove one row at a time from the proxy model. For some
            # reason, a ranged removeRows() fails.
            # Also, the removal is immediate, so we keep removing index 0.
            for row in reversed(range(racer_in_field_table_model.rowCount())):
                racer_in_field_table_model.removeRow(row)

            model.removeRow(selection.row())

        # Model retains blank rows until we select() again.
        if not self.modeldb.field_table_model.select():
            raise DatabaseError(model.lastError().text())

    def dataChanged(self, top_left=QModelIndex(), bottom_right=QModelIndex(), roles=[]):
        super().dataChanged(top_left, bottom_right, roles)

        field_table_model = self.modeldb.field_table_model

        # When roles is empty, it means everything has changed
        if roles and Qt.DisplayRole not in roles:
            return

        if (top_left.isValid() and
            (top_left.column() > field_table_model.fieldIndex(FieldTableModel.NAME))):
            return

        # Field table model changed. Go through the model to see if we need to
        # make any new racer-in-field-table-views. Drop the ones we don't
        # need anymore.
        new_racer_in_field_table_view_dict = {}

        for row in range(field_table_model.rowCount()):
            record = field_table_model.record(row)
            field_id = record.value(FieldTableModel.ID)
            if field_id in self.racer_in_field_table_view_dict:
                new_racer_in_field_table_view_dict[field_id] = self.racer_in_field_table_view_dict[field_id]
                new_racer_in_field_table_view_dict[field_id].updateFieldName()
            else:
                new_racer_in_field_table_view_dict[field_id] = RacerTableView(self.modeldb, field_id)

        self.racer_in_field_table_view_dict = new_racer_in_field_table_view_dict

    def handleShowRacerInFieldTableView(self, model_index):
        # Don't allow using the first column to pop up the racer in field
        # table view, because it's likely the user just wants to edit the
        # field name.
        if (model_index.column() == self.modeldb.field_table_model.fieldIndex(FieldTableModel.NAME) or
            model_index.column() == self.modeldb.field_table_model.fieldIndex(FieldTableModel.SUBFIELDS)):
            return

        field_id = self.modeldb.field_table_model.record(model_index.row()).value(FieldTableModel.ID)

        self.racer_in_field_table_view_dict[field_id].show()

        self.clearSelection()

    # Our non-model columns (provided by FieldProxyModel(ExtraColumnsProxyModel))
    # uses stuff from the racer table model to provide its contents. Therefore,
    # when the racer model changes, we need to pretend our model changed.
    def updateNonModelColumns(self, *args):
        top_left = self.model().index(0, self.modeldb.field_table_model.columnCount(), QModelIndex())
        bottom_right = self.model().index(self.modeldb.field_table_model.rowCount(), self.model().columnCount(QModelIndex())-1, QModelIndex())
        self.dataChanged(top_left, bottom_right, [Qt.DisplayRole])

    # Signals.
    visibleChanged = pyqtSignal(bool)

class RacerProxyModel(SqlSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.remote = None

    def data(self, index, role):
        if role == Qt.BackgroundRole:
            row = self.mapToSource(index).row()

            racer_table_model = self.sourceModel()

            record = racer_table_model.record(row)

            start = QTime.fromString(record.value(RacerTableModel.START))
            finish = QTime.fromString(record.value(RacerTableModel.FINISH))

            if not start.isValid():
                return QBrush(Qt.red)

            if finish.isValid():
                if self.remote:
                    if record.value(RacerTableModel.STATUS) == 'local':
                        return QBrush(Qt.yellow)
                    elif record.value(RacerTableModel.STATUS) == 'remote':
                        return QBrush(Qt.green)
                else:
                    return QBrush(Qt.green)

        return super().data(index, role)

    def setRemote(self, remote):
        self.remote = remote

        # Make views repaint cell backgrounds to reflect remote.
        self.sourceModel().dataChanged.emit(QModelIndex(), QModelIndex(), [Qt.BackgroundRole])

class RacerTableView(QTableView):
    def __init__(self, modeldb, field_id=None, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb
        self.remote = None

        self.field_id = field_id
        model = self.modeldb.racer_table_model

        self.setModel(RacerProxyModel())
        self.model().setSourceModel(model)
        self.model().setFilterKeyColumn(model.fieldIndex(RacerTableModel.FIELD_ALIAS))

        self.updateFieldName()

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(model.fieldIndex(RacerTableModel.BIB),
                          Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(model.fieldIndex(RacerTableModel.ID))
        if self.field_id:
            self.hideColumn(model.fieldIndex(RacerTableModel.FIELD_ALIAS))
        # Hide the status by default. Show it if we have a remote
        # set up for this race.
        self.hideColumn(model.fieldIndex(RacerTableModel.STATUS))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.handleDelete()

        super().keyPressEvent(event)

    def showEvent(self, event):
        self.resize(1000, 800)

    def hideEvent(self, event):
        self.visibleChanged.emit(False)

    def handleDelete(self):
        model = self.selectionModel().model()
        item_selection = self.selectionModel().selection()
        selection_list = self.selectionModel().selectedRows()

        racer_table_model = self.modeldb.racer_table_model

        racer_count = len(selection_list)

        # Confirm deletion.
        msg_box = QMessageBox()
        msg_box.setWindowTitle(APPLICATION_NAME)
        msg_box.setText('Deleting %s' % pluralize('racer', racer_count))
        msg_box.setInformativeText('Do you really want to delete?')
        msg_box.setStandardButtons(QMessageBox.Ok |
                                   QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Cancel)
        msg_box.setIcon(QMessageBox.Information)

        if msg_box.exec() != QMessageBox.Ok:
            return

        # Remove rows from large to small, because the rows are removed
        # immediately, and cause the rest of the rows to shift, invalidating
        # any row number that's higher than the currently removed one.
        selection_list.sort(key=lambda selection: selection.row(), reverse=True)
        for selection in selection_list:
            model.removeRow(selection.row())

        # Model retains blank rows until we select() again.
        if not self.modeldb.racer_table_model.select():
            raise DatabaseError(model.lastError().text())

    def updateFieldName(self):
        if self.field_id:
            field_name = self.modeldb.field_table_model.name_from_id(self.field_id)
            self.setWindowTitle('Racers (%s)' % field_name)
            self.model().setFilterRegExp(QRegExp(field_name, Qt.CaseSensitive, QRegExp.FixedString))
        else:
            self.setWindowTitle('Racers')

    def setRemote(self, remote):
        self.remote = remote
        self.model().setRemote(remote)

        if self.remote:
            self.showColumn(self.model().fieldIndex(RacerTableModel.STATUS))
        else:
            self.hideColumn(self.model().fieldIndex(RacerTableModel.STATUS))

    # Signals.
    visibleChanged = pyqtSignal(bool)

class ResultTableView(QTableView):
    RESULT_TABLE_POINT_SIZE = 20

    def __init__(self, modeldb, parent=None):
        super().__init__(parent=parent)

        self.modeldb = modeldb

        self.setModel(self.modeldb.result_table_model)

        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False) # Don't allow sorting.
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(self.model().fieldIndex(ResultTableModel.FINISH),
                          Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex(ResultTableModel.ID))

        font = self.font()
        font.setPointSize(self.RESULT_TABLE_POINT_SIZE)
        self.setFont(font)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.handleDelete()

        return super().keyPressEvent(event)

    def handleDelete(self):
        model = self.selectionModel().model()
        item_selection = self.selectionModel().selection()
        selection_list = self.selectionModel().selectedRows()

        # Remove rows from large to small, because the rows are removed
        # immediately, and cause the rest of the rows to shift, invalidating
        # any row number that's higher than the currently removed one.
        selection_list.sort(key=lambda selection: selection.row(), reverse=True)
        for selection in selection_list:
            model.removeRow(selection.row())

        # Model retains blank rows until we select() again.
        if not self.modeldb.result_table_model.select():
            raise DatabaseError(model.lastError().text())

        # Selection changed because of this deletion, but for some reason,
        # this widget class doesn't emit the selectionChanged signal in this
        # case. Let's emit it ourselves.
        #
        # Not gonna bother calculating selected and deselected. Hopefully,
        # slots that receive this signal won't care...
        self.selectionModel().selectionChanged.emit(QItemSelection(),
                                                    item_selection)

    def handleSubmit(self):
        model = self.selectionModel().model()
        selection_list = self.selectionModel().selectedRows()

        # Remove rows from large to small, because the rows are removed
        # immediately, and cause the rest of the rows to shift, invalidating
        # any row number that's higher than the currently removed one.
        selection_list.sort(key=lambda selection: selection.row(), reverse=True)
        for selection in selection_list:
            try:
                # Only try to submit it if it's a non-negative integer.
                # Else, it is obviously a work in progress, so don't even
                # bother.
                record = model.record(selection.row())
                scratchpad = record.value(ResultTableModel.SCRATCHPAD)
                if scratchpad.isdigit():
                    model.submit_result(selection.row())
            except InputError as e:
                QMessageBox.warning(self, 'Error', str(e))

        # Model retains blank rows until we select() again.
        if not model.select():
            raise DatabaseError(model.lastError().text())
