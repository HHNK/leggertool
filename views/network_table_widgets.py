""" The (tree)tables of the legger network tool"""

import logging

from legger.qt_models.area_tree import AreaTreeModel
from legger.qt_models.legger_tree import LeggerTreeModel
from qgis.PyQt import QtGui, QtWidgets
from qgis.PyQt.QtCore import QEvent, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (QApplication, QTableView, QTreeView)

log = logging.getLogger('legger.' + __name__)

try:
    _encoding = QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)


class VariantenTable(QTableView):
    """Table with varianten"""
    # hoverExitRow = pyqtSignal(int)
    hoverExitAllRows = pyqtSignal()  # exit the whole widget
    # hoverEnterRow = pyqtSignal(int)

    def __init__(self, parent=None, variant_model=None):
        super(VariantenTable, self).__init__(parent)

        self._last_hovered_row = None

        if variant_model is not None:
            self.setModel(variant_model)

        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)

        self.setStyleSheet("QTableView::item:hover{background-color:#FFFF00;}")

    def destroy(self, event):
        """
        overwrite of QDockWidget class to emit signal
        :param event: QEvent
        """
        self.setMouseTracking(False)
        self.viewport().removeEventFilter(self)
        super(VariantenTable, self).destroy(event)
        event.accept()

    def eventFilter(self, widget, event):
        if widget is self.viewport():
            if QEvent is None:
                return QTableView.eventFilter(self, widget, event)
            elif event.type() == QEvent.MouseMove:
                row = self.indexAt(event.pos()).row()
                if row == 0 and self.model() and row > self.model().rowCount():
                    row = None
            elif event.type() == QEvent.Leave:
                row = None
                self.hoverExitAllRows.emit()
            else:
                row = self._last_hovered_row

            if row != self._last_hovered_row:
                if self._last_hovered_row is not None:
                    try:
                        self.hover_exit(self._last_hovered_row)
                        # self.hoverExitRow.emit(self._last_hovered_row)
                    except IndexError:
                        log.warning("Hover row index %s out of range",
                                    self._last_hovered_row)
                if row is not None:
                    try:
                        self.hover_enter(row)
                        # self.hoverEnterRow.emit(row)
                    except IndexError:
                        log.warning("Hover row index %s out of range", row),
                self._last_hovered_row = row

        return QTableView.eventFilter(self, widget, event)

    def hover_exit(self, row_nr):
        if row_nr >= 0:
            item = self.model().rows[row_nr]
            item.hover.value = False
            if not item.active.value:
                item.color.value = list(item.color.value)[:3] + [80]

    def hover_enter(self, row_nr):
        if row_nr >= 0:
            item = self.model().rows[row_nr]
            item.hover.value = True
            if not item.active.value:
                item.color.value = list(item.color.value)[:3] + [200]

    def setModel(self, model):
        super(VariantenTable, self).setModel(model)

        self.resizeColumnsToContents()
        self.model().set_column_sizes_on_view(self)


class StartpointTreeWidget(QTreeView):
    """ TreeView with startpoints """
    # hoverExitIndex = pyqtSignal(QModelIndex)
    hoverExitAll = pyqtSignal()  # exit the whole widget
    # hoverEnterIndex = pyqtSignal(QModelIndex)

    def __init__(self, parent=None, startpoint_model=None, on_select=None):
        super(StartpointTreeWidget, self).__init__(parent)
        self.on_select = on_select

        self._last_hovered_item = None

        if startpoint_model is None:
            startpoint_model = AreaTreeModel()
        self.setModel(startpoint_model)

        # set signals
        self.clicked.connect(self.click_leaf)

        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)

        # set other
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

    def closeEvent(self, event):
        """
        overwrite of QDockWidget class to emit signal
        :param event: QEvent
        """
        self.clicked.disconnect(self.click_leaf)
        self.setMouseTracking(False)
        self.viewport().removeEventFilter(self)
        super(StartpointTreeWidget, self).closeEvent(event)
        event.accept()

    def click_leaf(self, index):

        if index.column() == 0:
            item = self.model().data(index, Qt.UserRole)
            if item.area.get('selected'):
                # deselect
                self.model().setDataItemKey(item, 'selected', Qt.Unchecked)
            else:
                # select
                self.model().setDataItemKey(item, 'selected', Qt.Checked)

    def eventFilter(self, widget, event):
        if widget is self.viewport():
            if QEvent is None:
                return QTreeView.eventFilter(self, widget, event)
            elif event.type() == QEvent.MouseMove:
                index = self.indexAt(event.pos())
                if not index.isValid():
                    index = None
            elif event.type() == QEvent.Leave:
                index = None
                self.hoverExitAll.emit()
            else:
                index = self._last_hovered_item

            if index != self._last_hovered_item:
                if self._last_hovered_item is not None:
                    try:
                        # self.hoverExitIndex.emit(self._last_hovered_item)
                        self.hover_exit(self._last_hovered_item)
                    except IndexError:
                        log.warning("Hover row index %s out of range",
                                    self._last_hovered_item)

                if index is not None:
                    try:
                        self.hover_enter(index)
                        # self.hoverEnterIndex.emit(index)
                    except IndexError:
                        log.warning("Hover row index %s out of range", index.row()),
                self._last_hovered_item = index

        return QTreeView.eventFilter(self, widget, event)

    def hover_exit(self, index):
        item = index.internalPointer()
        self.model().setDataItemKey(item, 'hover', Qt.Unchecked)

    def hover_enter(self, index):
        item = index.internalPointer()
        self.model().setDataItemKey(item, 'hover', True)

    def setModel(self, model):
        super(StartpointTreeWidget, self).setModel(model)

        self.model().set_column_sizes_on_view(self)


class LeggerTreeWidget(QTreeView):
    """TreeView with network of hydroobjects"""
    # hoverExitIndex = pyqtSignal(QModelIndex)
    hoverExitAll = pyqtSignal()  # exit the whole widget
    # hoverEnterIndex = pyqtSignal(QModelIndex)

    def __init__(self, parent=None, legger_model: LeggerTreeModel=None):
        super(LeggerTreeWidget, self).__init__(parent)

        self._last_hovered_item = None

        if legger_model is None:
            legger_model = LeggerTreeModel()
        self.setModel(legger_model)

        # set signals
        self.clicked.connect(self.click_leaf)
        # self.Resized.connect(self.on_resize)

        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)

        # set other
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self.header().sectionClicked.connect(self.on_header_click)
        self.header().setSectionsClickable(True)

    def on_header_click(self, column):

        if column == 0:
            if self.model().allCollapsed:
                self.collapseAll()
            else:
                self.expandAll()

            self.model().allCollapsed = not self.model().allCollapsed

    def closeEvent(self, event):
        """
        overwrite of QDockWidget class to emit signal
        :param event: QEvent
        """
        self.clicked.disconnect(self.click_leaf)
        self.header().sectionClicked.disconnect(self.on_header_click)
        self.setMouseTracking(False)
        self.viewport().removeEventFilter(self)
        # super(LeggerTreeWidget, self).closeEvent(event)
        event.accept()

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)
        self.do_resize()

    def do_resize(self):
        if self.model() is None:
            return
        width = self.width()
        self.model().set_column_sizes_on_view(self, width=width)


    def click_leaf(self, index):

        if index.column() == 0:
            item = self.model().data(index, Qt.UserRole)
            if item.hydrovak.get('soort_vak') in [3, 4]:
                return

            if item.hydrovak.get('selected'):
                # deselect
                self.model().setDataItemKey(item, 'selected', Qt.Unchecked)
            else:
                # select
                self.model().setDataItemKey(item, 'selected', Qt.Checked)

    def eventFilter(self, widget, event):
        if widget is self.viewport():
            if QEvent is None:
                return QTreeView.eventFilter(self, widget, event)
            elif event.type() == QEvent.MouseMove:
                index = self.indexAt(event.pos())
                if not index.isValid():
                    index = None
            elif event.type() == QEvent.Leave:
                index = None
                self.hoverExitAll.emit()
            else:
                index = self._last_hovered_item

            if index != self._last_hovered_item:
                if self._last_hovered_item is not None:
                    try:
                        # self.hoverExitIndex.emit(self._last_hovered_item)
                        self.hover_exit(self._last_hovered_item)
                    except IndexError:
                        log.warning("Hover row index %s out of range",
                                    self._last_hovered_item)

                if index is not None:
                    try:
                        self.hover_enter(index)
                        # self.hoverEnterIndex.emit(index)
                    except IndexError:
                        log.warning("Hover row index %s out of range", index.row()),
                self._last_hovered_item = index

        return QTreeView.eventFilter(self, widget, event)

    def hover_exit(self, index):
        item = index.internalPointer()
        self.model().setDataItemKey(item, 'hover', Qt.Unchecked)

    def hover_enter(self, index):
        item = index.internalPointer()
        self.model().setDataItemKey(item, 'hover', Qt.Checked)

    def setModel(self, model):
        super(LeggerTreeWidget, self).setModel(model)

        self.model().set_column_sizes_on_view(self)
