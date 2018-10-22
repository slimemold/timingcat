from PyQt5.QtWidgets import *
from common import *
from proxymodels import *
from racemodel import *

class RaceTableView(QTableView):
    def __init__(self, race_model, parent=None):
        super().__init__(parent=parent)

        self.setModel(race_model)

        self.setWindowTitle('Race Info')

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setVisible(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        self.visibleChanged.emit(False)

    # Signals.
    visibleChanged = pyqtSignal(bool)

# Add a "Finished" column for total racers that have a finish time, and a
# "Total" column to show total racers in that field.
class FieldProxyModel(ExtraColumnsProxyModel):
    FINISHED_SECTION = 0
    TOTAL_SECTION = 1

    def __init__(self):
        super().__init__()

        self.appendColumn('Finished')
        self.appendColumn('Total')

    def extraColumnData(self, parent, row, extraColumn, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            field_table_model = self.sourceModel()
            racer_table_model = self.sourceModel().modeldb.racer_table_model

            field_id = field_table_model.recordAtRow(row)[RacerTableModel.ID]

            if extraColumn == self.FINISHED_SECTION:
                return racer_table_model.racerCountFinishedInField(field_id)
            elif extraColumn == self.TOTAL_SECTION:
                return racer_table_model.racerCountTotalInField(field_id)

        return None

class FieldTableView(QTableView):
    def __init__(self, field_model, parent=None):
        super().__init__(parent=parent)

        self.setModel(field_model)
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

    def setupProxyModel(self):
        # Use a proxy model so we can add some interesting columns.
        proxyModel = FieldProxyModel()
        proxyModel.setSourceModel(self.model())

        self.setModel(proxyModel)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        self.visibleChanged.emit(False)

    # Signals.
    visibleChanged = pyqtSignal(bool)

class RacerTableView(QTableView):
    def __init__(self, racer_model, field_id=None, parent=None):
        super().__init__(parent=parent)

        self.field_id = field_id
        model = racer_model

        if self.field_id:
            self.setModel(QSortFilterProxyModel())
            self.model().setSourceModel(model)
            self.model().setFilterKeyColumn(model.fieldIndex(RacerTableModel.FIELD_ALIAS))
            self.updateFieldName()
        else:
            self.setModel(model)

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

    def setupProxyModel(self, field_id):
        # Use a proxy model so we can add some interesting columns.
        proxyModel = RacerInFieldFilterProxyModel(field_id)
        proxyModel.setSourceModel(self.model())

        self.setModel(proxyModel)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        self.resize(600, 800)

    def hideEvent(self, event):
        self.visibleChanged.emit(False)

    def updateFieldName(self):
        if self.field_id:
            field_name = self.model().sourceModel().fieldNameFromId(self.field_id)
            self.setWindowTitle('Racers (%s)' % field_name)
            self.model().setFilterRegExp(QRegExp(field_name, Qt.CaseSensitive, QRegExp.FixedString))
        else:
            self.setWindowTitle('Racers')

    # Signals.
    visibleChanged = pyqtSignal(bool)

class ResultTableView(QTableView):
    RESULT_TABLE_POINT_SIZE = 20

    def __init__(self, result_model, parent=None):
        super().__init__(parent=parent)

        self.setModel(result_model)

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
        if event.key() == Qt.Key_Backspace:
            self.handleDelete()

        return super().keyPressEvent(event)

    def handleDelete(self):
        model = self.selectionModel().model()
        item_selection = self.selectionModel().selection()
        selection_list = self.selectionModel().selectedRows()
        for selection in selection_list:
            model.deleteResult(selection.row())

        # Model retains blank rows until we select() again.
        if not model.select():
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
        for selection in selection_list:
            try:
                model.submitResult(selection.row())
                model.deleteResult(selection.row())
            except InputError as e:
                QMessageBox.warning(self, 'Error', str(e))

        # Model retains blank rows until we select() again.
        if not model.select():
            raise DatabaseError(model.lastError().text())
