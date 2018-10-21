from PyQt5.QtWidgets import *
from common import *
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

class FieldProxyModel(QIdentityProxyModel):
    FINISHED_SECTION = 0
    TOTAL_SECTION = 1

    def columnCount(self, parent):
        return self.sourceModel().columnCount(parent) + 2

    def fieldIndex(self, field_name):
        return self.sourceModel().fieldIndex(field_name)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if (section - self.sourceModel().columnCount())  == self.FINISHED_SECTION:
                return 'Finished'
            elif (section - self.sourceModel().columnCount()) == self.TOTAL_SECTION:
                return 'Total'

        return self.sourceModel().headerData(section, orientation, role)

    def data(self, model_index, role):
#        print('col %s row %s' % (model_index.column(), model_index.row()))
        section = model_index.column()

        if role == Qt.DisplayRole:
            if (section - self.sourceModel().columnCount())  == self.FINISHED_SECTION:
                print("Squish")
                return "3"
            elif (section - self.sourceModel().columnCount()) == self.TOTAL_SECTION:
                print("Squish2")
                return "5"

        fish = self.sourceModel().data(model_index, role)
        print(fish)
        return fish

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

        self.model().setHeaderData(1, Qt.Horizontal, 'Field')

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
    def __init__(self, racer_model, parent=None):
        super().__init__(parent=parent)

        self.setModel(racer_model)

        self.setWindowTitle('Racers')

        # Set up our view.
        self.setItemDelegate(QSqlRelationalDelegate())
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True) # Allow sorting by column
        self.setSelectionBehavior(QTableView.SelectRows)
        self.sortByColumn(self.model().fieldIndex(RacerTableModel.BIB),
                          Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.hideColumn(self.model().fieldIndex(RacerTableModel.ID))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        self.resize(600, 800)

    def hideEvent(self, event):
        self.visibleChanged.emit(False)

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
        model.select()

        # Selection changed because of this deletion, but for some reason,
        # this widget class doesn't emit the selectionChanged signal in this
        # case. Let's emit it ourselves.
        #
        # Not gonna bother calculating selected and deselected. Hopefully,
        # slots that receive this signal won't care...
        self.selectionModel().selectionChanged.emit(QItemSelection(),
                                                    item_selection)

    def handleCommit(self):
        model = self.selectionModel().model()
        selection_list = self.selectionModel().selectedRows()
        for selection in selection_list:
            try:
                model.commitResult(selection.row())
                model.deleteResult(selection.row())
            except InputError as e:
                QMessageBox.warning(self, 'Error', str(e))

        # Model retains blank rows until we select() again.
        model.select()
