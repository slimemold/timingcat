#!/usr/bin/env python3

"""SQL Table View Classes

This module contains the various Qt SQL Table Views (field table view, racer table views,
result scratch pad table view), as well as whatever proxy models are stacked between the views
and the models.
"""

from PyQt5.QtCore import QItemSelection, QModelIndex, QRegExp, QSettings, QTime, Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from PyQt5.QtSql import QSqlRelationalDelegate
from PyQt5.QtWidgets import QMessageBox, QTableView
from common import APPLICATION_NAME, VERSION, pluralize, pretty_list
import defaults
from proxymodels import SqlExtraColumnsProxyModel, SqlSortFilterProxyModel
from racemodel import DatabaseError, InputError, FieldTableModel, JournalTableModel, \
                      RacerTableModel, ResultTableModel

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

class JournalTableView(QTableView):
    """Table view for the journal table model."""

    def __init__(self, modeldb, parent=None):
        """Initialize the JournalTableView instance."""
        super().__init__(parent=parent)

        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.modeldb = modeldb

        self.setModel(self.modeldb.journal_table_model)

        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex(JournalTableModel.ID))

        self.read_settings()

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Handle hide event."""
        del event
        self.write_settings()
        self.visibleChanged.emit(False)

    def read_settings(self):
        """Read settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        self.resize(settings.value('size', defaults.RESULT_TABLE_VIEW_SIZE))
        if settings.contains('pos'):
            self.move(settings.value('pos'))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())

        settings.endGroup()

    # Signals.
    visibleChanged = pyqtSignal(bool)

# Add a "Finished" column for total racers that have a finish time, and a
# "Total" column to show total racers in that field.
class FieldProxyModel(SqlExtraColumnsProxyModel):
    """Proxy model for the field table model.

    This proxy model adds extra columns to the field table. Extra columns include number of racers
    finished, number of racers total, and completion status.
    """

    FINISHED_SECTION = 0
    TOTAL_SECTION = 1
    STATUS_SECTION = 2

    def __init__(self):
        """Initialize the FieldProxyModel instance."""
        super().__init__()

        self.appendColumn('Finished')
        self.appendColumn('Total')
        self.appendColumn('Status')

    def extraColumnData(self, parent, row, extra_column, role=Qt.DisplayRole):
        """Provide extra columns for racers finished, total racers, and field status."""
        if role == Qt.DisplayRole:
            field_table_model = self.sourceModel()
            racer_table_model = self.sourceModel().modeldb.racer_table_model

            field_name = field_table_model.record(row).value(FieldTableModel.NAME)

            total = racer_table_model.racer_count_total_in_field(field_name)
            finished = racer_table_model.racer_count_finished_in_field(field_name)

            if extra_column == self.FINISHED_SECTION:
                return finished
            elif extra_column == self.TOTAL_SECTION:
                return total
            elif extra_column == self.STATUS_SECTION:
                if total == 0:
                    return 'Empty'
                elif finished < total:
                    return 'In Progress (%s%%)' % int(round(finished * 100 / total))
                else:
                    return 'Complete'

        return None

    def data(self, index, role):
        """Color-code the row according to whether no, some, or all racers have finished."""
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
    """Table view for the field table model."""

    def __init__(self, modeldb, parent=None):
        """Initialize the FieldTableView instance."""
        super().__init__(parent=parent)

        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.modeldb = modeldb

        self.setModel(self.modeldb.field_table_model)
        self.setup_proxy_model()

        self.setWindowTitle('Fields')

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(self.model().fieldIndex(FieldTableModel.NAME), Qt.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex(FieldTableModel.ID))

        # For each field, we make a racer in field table view ahead of time.
        # Note that we call dataChanged here because the initial reading of
        # the model is not considered a data change, but we need to do this
        # anyway to populate racer_in_field_table_view_dict.
        self.racer_in_field_table_view_dict = {}
        self.dataChanged(QModelIndex(), QModelIndex(), [])

        # Signals/slots to handle racer in field table views.
        self.modeldb.racer_table_model.dataChanged.connect(self.update_non_model_columns)
        self.doubleClicked.connect(self.handle_show_racer_in_field_table_view)

        self.read_settings()

    def setup_proxy_model(self):
        """Use a proxy model so we can add some interesting columns."""
        proxy_model = FieldProxyModel()
        proxy_model.setSourceModel(self.model())

        self.setModel(proxy_model)

    def keyPressEvent(self, event): #pylint: disable=invalid-name
        """Handle key presses."""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.handle_delete()

        return super().keyPressEvent(event)

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Handle hide event."""
        del event
        self.write_settings()
        self.visibleChanged.emit(False)

    def handle_delete(self):
        """Handle delete key press.

        On delete key press, delete the selection.
        """
        model = self.selectionModel().model()
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

    def dataChanged(self, top_left, bottom_right, roles): #pylint: disable=invalid-name
        """Handle model data changed.

        One big thing we need to do here is make new field-specific racer table views (or remove
        existing ones) if a field was added, renamed, or removed. We basically keep a dictionary
        of field_id:racer_table_view of all field-specific racer table views, and in this method,
        we scan through the list of fields and update this dictionary accordingly.
        """
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
        new_racer_table_view_dict = {}

        for row in range(field_table_model.rowCount()):
            record = field_table_model.record(row)
            field_id = record.value(FieldTableModel.ID)
            if field_id in self.racer_in_field_table_view_dict:
                new_racer_table_view_dict[field_id] = self.racer_in_field_table_view_dict[field_id]
                new_racer_table_view_dict[field_id].update_field_name()
            else:
                new_racer_table_view_dict[field_id] = RacerTableView(self.modeldb, field_id)

        self.racer_in_field_table_view_dict = new_racer_table_view_dict

    def handle_show_racer_in_field_table_view(self, model_index):
        """Handle activation of a field row.

        On activation of a field row, we show its field-specific racer table view.
        """
        field_table_model = self.modeldb.field_table_model
        field_name_column = field_table_model.fieldIndex(FieldTableModel.NAME)
        field_subfields_column = field_table_model.fieldIndex(FieldTableModel.SUBFIELDS)

        # Don't allow using the first two columns to pop up the racer in field
        # table view, because it's likely the user just wants to edit the
        # field name.
        if (model_index.column() == field_name_column or
            model_index.column() == field_subfields_column):
            return

        field_id = field_table_model.record(model_index.row()).value(FieldTableModel.ID)

        self.racer_in_field_table_view_dict[field_id].show()

        self.clearSelection()

    def update_non_model_columns(self, *args):
        """Handle racer table model change.

        On racer table model change, we tickle our dataChanged() slot to induce this table view
        to take another look at the extra columns, since the values in these extra columns depends
        on racer state.

        Our non-model columns (provided by FieldProxyModel(ExtraColumnsProxyModel)) uses stuff from
        the racer table model to provide its contents. Therefore, when the racer model changes, we
        need to pretend our model changed.
        """
        # We don't care about the incoming top_left and bottom_right indexes.
        del args

        field_table_model = self.modeldb.field_table_model

        row_start = 0
        row_end = field_table_model.rowCount()
        extra_column_start = field_table_model.columnCount()
        extra_column_end = self.model().columnCount(QModelIndex()) - 1

        top_left = self.model().index(row_start, extra_column_start, QModelIndex())
        bottom_right = self.model().index(row_end, extra_column_end, QModelIndex())

        # TODO: Use extraColumnDataChanged for this.
        self.dataChanged(top_left, bottom_right, [Qt.DisplayRole])

    def read_settings(self):
        """Read settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        self.resize(settings.value('size', defaults.FIELD_TABLE_VIEW_SIZE))
        if settings.contains('pos'):
            self.move(settings.value('pos'))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())

        settings.endGroup()

    # Signals.
    visibleChanged = pyqtSignal(bool)

class RacerProxyModel(SqlSortFilterProxyModel):
    """Proxy model for racer table model.

    This proxy model filters the racer table by field. It is used by field table views that want
    to only show racers that belong to a given field.
    """

    def __init__(self):
        """Initialize the RacerProxyModel instance."""
        super().__init__()
        self.remote = None

    def data(self, index, role):
        """Color-code the row according to whether the racer has finished or not.

        If a remote is connected, also show a different color for local result vs. result that
        has been submitted successfully to the remote.
        """
        if role == Qt.BackgroundRole:
            source_index = self.mapToSource(index)
            row = source_index.row()
            column = source_index.column()

            racer_table_model = self.sourceModel()

            record = racer_table_model.record(row)

            start = QTime.fromString(record.value(RacerTableModel.START))
            finish = QTime.fromString(record.value(RacerTableModel.FINISH))

            # No start time. Paint the cell red.
            if (column == self.fieldIndex(RacerTableModel.START) and
                not start.isValid()):
                return QBrush(Qt.red)

            # Finish time is before the start time. Paint the cell red.
            if (column == self.fieldIndex(RacerTableModel.FINISH) and
                finish.isValid() and
                finish < start):
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

    def set_remote(self, remote):
        """Do everything needed for a remote that has just been connected."""
        self.remote = remote

        # Make views repaint cell backgrounds to reflect remote.
        self.sourceModel().dataChanged.emit(QModelIndex(), QModelIndex(), [Qt.BackgroundRole])

class RacerTableView(QTableView):
    """Table view for the racer table model."""

    def __init__(self, modeldb, field_id=None, parent=None):
        """Initialize the RacerTableView instance."""
        super().__init__(parent=parent)

        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.modeldb = modeldb
        self.remote = None

        self.field_id = field_id
        model = self.modeldb.racer_table_model

        self.setModel(RacerProxyModel())
        self.model().setSourceModel(model)
        self.model().setFilterKeyColumn(model.fieldIndex(RacerTableModel.FIELD_ALIAS))

        self.update_field_name()

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(model.fieldIndex(RacerTableModel.BIB), Qt.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(model.fieldIndex(RacerTableModel.ID))
        if self.field_id:
            self.hideColumn(model.fieldIndex(RacerTableModel.FIELD_ALIAS))
        # Hide the status by default. Show it if we have a remote
        # set up for this race.
        self.hideColumn(model.fieldIndex(RacerTableModel.STATUS))

        self.read_settings()

    def keyPressEvent(self, event): #pylint: disable=invalid-name
        """Handle key presses."""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.handle_delete()

        super().keyPressEvent(event)

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Handle hide event."""
        del event
        self.write_settings()
        self.visibleChanged.emit(False)

    def handle_delete(self):
        """Handle delete key press.

        On delete key press, delete the selection.
        """
        model = self.selectionModel().model()
        selection_list = self.selectionModel().selectedRows()

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

    def update_field_name(self):
        """Update the window title.

        Update the window title with the field name corresponding to the field_id which we are
        using to filter our racer table view. If this is the general racer table view (not a field-
        specific one), then there's really not much to be done...the window title will always
        be the same.
        """
        if self.field_id:
            field_name = self.modeldb.field_table_model.name_from_id(self.field_id)
            self.setWindowTitle('Racers (%s)' % field_name)
            self.model().setFilterRegExp(QRegExp(field_name, Qt.CaseSensitive, QRegExp.FixedString))
        else:
            self.setWindowTitle('Racers')

    def set_remote(self, remote):
        """Do everything needed for a remote that has just been connected."""
        self.remote = remote
        self.model().set_remote(remote)

        if self.remote:
            self.showColumn(self.model().fieldIndex(RacerTableModel.STATUS))
        else:
            self.hideColumn(self.model().fieldIndex(RacerTableModel.STATUS))

    def read_settings(self):
        """Read settings."""
        group_name = self.__class__.__name__
        if self.field_id:
            field_name = self.modeldb.field_table_model.name_from_id(self.field_id)
            group_name = '_'.join([group_name, field_name])
        settings = QSettings()
        settings.beginGroup(group_name)

        self.resize(settings.value('size', defaults.RACER_TABLE_VIEW_SIZE))
        if settings.contains('pos'):
            self.move(settings.value('pos'))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        if self.field_id:
            field_name = self.modeldb.field_table_model.name_from_id(self.field_id)
            group_name = '_'.join([group_name, field_name])
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())

        settings.endGroup()

    # Signals.
    visibleChanged = pyqtSignal(bool)

class ResultTableView(QTableView):
    """Table view for the result table model."""

    RESULT_TABLE_POINT_SIZE = 20

    def __init__(self, modeldb, parent=None):
        """Initialize the ResultTableView instance."""
        super().__init__(parent=parent)

        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.modeldb = modeldb

        self.setModel(self.modeldb.result_table_model)

        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False) # Don't allow sorting.
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(self.model().fieldIndex(ResultTableModel.FINISH), Qt.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex(ResultTableModel.ID))

        font = self.font()
        font.setPointSize(self.RESULT_TABLE_POINT_SIZE)
        self.setFont(font)

        self.read_settings()

    def keyPressEvent(self, event): #pylint: disable=invalid-name
        """Handle key presses."""
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.handle_delete()

        return super().keyPressEvent(event)

    def hideEvent(self, event): #pylint: disable=invalid-name
        """Handle hide event."""
        del event
        self.write_settings()
        self.visibleChanged.emit(False)

    def handle_delete(self):
        """Handle delete key press.

        On delete key press, delete the selection.
        """
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

        # Emit resultDeleted signal.
        self.resultDeleted.emit()

    # Signals.
    resultDeleted = pyqtSignal()

    def handle_submit(self):
        """Handle submit button click.

        On submit button click, we try to push the finish times for the selected rows to the
        corresponding racer. For each selection that succeeds, we remove that row from this table.
        """
        model = self.selectionModel().model()
        selection_list = self.selectionModel().selectedRows()

        # Remove rows from large to small, because the rows are removed
        # immediately, and cause the rest of the rows to shift, invalidating
        # any row number that's higher than the currently removed one.
        selection_list.sort(key=lambda selection: selection.row(), reverse=True)
        deleted_selection = QItemSelection()
        for selection in selection_list:
            try:
                # Only try to submit it if it's a non-negative integer.
                # Else, it is obviously a work in progress, so don't even
                # bother.
                record = model.record(selection.row())
                scratchpad = record.value(ResultTableModel.SCRATCHPAD)
                if scratchpad.isdigit():
                    model.submit_result(selection.row())
                    deleted_selection.select(selection, selection)
            except InputError as e:
                QMessageBox.warning(self, 'Error', str(e))

        # Model retains blank rows until we select() again.
        if not model.select():
            raise DatabaseError(model.lastError().text())

        # Surprisingly, when the model changes such that our selection changes
        # (for example, when the selected result gets submitted to the racer
        # table model and gets deleted from the result table model), the
        # selectionChanged signal is NOT emitted. So, we have to emit that
        # ourselves here.
        self.selectionModel().selectionChanged.emit(QItemSelection(), deleted_selection)

    def read_settings(self):
        """Read settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        self.resize(settings.value('size', defaults.RESULT_TABLE_VIEW_SIZE))
        if settings.contains('pos'):
            self.move(settings.value('pos'))

        settings.endGroup()

    def write_settings(self):
        """Write settings."""
        group_name = self.__class__.__name__
        settings = QSettings()
        settings.beginGroup(group_name)

        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())

        settings.endGroup()

    # Signals.
    visibleChanged = pyqtSignal(bool)
