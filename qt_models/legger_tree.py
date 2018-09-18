from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QBrush, QColor, QIcon
from legger import settings

CHECKBOX_FIELD = 1

HORIZONTAL_HEADERS = ({'field': 'hydro_id', 'column_width': 150},
                      # {'field': 'feat_id', 'column_width': 25},
                      {'field': 'sp', 'field_type': CHECKBOX_FIELD, 'column_width': 25, 'single_selection': True},
                      {'field': 'ep', 'field_type': CHECKBOX_FIELD, 'column_width': 25, 'single_selection': True},
                      {'field': 'selected', 'field_type': CHECKBOX_FIELD, 'show': False, 'column_width': 50,
                       'single_selection': True},
                      {'field': 'hover', 'field_type': CHECKBOX_FIELD, 'show': False, 'column_width': 50},
                      {'field': 'distance', 'header': 'afstand', 'show': False, 'column_width': 50},
                      {'field': 'flow', 'header': 'debiet', 'column_width': 50},
                      {'field': 'target_level', 'show': False, 'column_width': 50},
                      {'field': 'depth', 'header': 'diepte', 'column_width': 50},
                      {'field': 'width', 'header': 'breedte', 'column_width': 50},
                      {'field': 'variant_min', 'show': False, 'column_width': 60},
                      {'field': 'variant_max', 'show': False, 'column_width': 60},
                      {'field': 'selected_depth', 'header': 'prof d', 'column_width': 60},
                      {'field': 'selected_depth_tmp', 'header': 'sel', 'column_width': 50},
                      {'field': 'selected_width', 'header': 'prof b', 'column_width': 60},
                      {'field': 'over_depth', 'header': 'over d', 'column_width': 60},
                      {'field': 'over_width', 'header': 'over b', 'column_width': 60},
                      {'field': 'score', 'column_width': 50},
                      )

HEADER_DICT = dict([(h['field'], h) for h in HORIZONTAL_HEADERS])


class hydrovak_class(object):
    """
    a trivial custom data object
    """

    def __init__(self, data_dict, feature, startpoint_feature, endpoint_feature):
        """

        data_dict (dict):
        """
        self.feature = feature
        self.startpoint_feature = startpoint_feature
        self.endpoint_feature = endpoint_feature

        self.feature_keys = {}
        self.data_dict = data_dict

    def __repr__(self):
        return "hydrovak - %s" % (self.get('hydro_id'))

    def data(self, column_nr, qvalue=False):
        # required
        if column_nr <= len(HORIZONTAL_HEADERS):
            if qvalue:
                if HORIZONTAL_HEADERS[column_nr].get('field_type') == CHECKBOX_FIELD:
                    if self.get(HORIZONTAL_HEADERS[column_nr]['field']):
                        return Qt.Checked
                    else:
                        return Qt.Unchecked
            return self.get(HORIZONTAL_HEADERS[column_nr]['field'])
        else:
            return None

    def setData(self, column, value, role):
        if HORIZONTAL_HEADERS[column].get('field_type') == CHECKBOX_FIELD:
            if type(value) == bool:
                value = value
            elif value == Qt.Checked:
                value = True
            elif value == Qt.Unchecked:
                value = False

        if value == self.get(HORIZONTAL_HEADERS[column]['field']):
            return False
        else:
            return self.set(HORIZONTAL_HEADERS[column]['field'], value)

    def get(self, key, default_value=None):
        if key == 'feature':
            return self.feature
        elif key == 'startpoint':
            return self.startpoint_feature
        elif key == 'endpoint':
            return self.endpoint_feature
        elif key == 'icon':
            if not self.endpoint_feature:
                return QIcon()
            elif self.endpoint_feature.attributes()[2] == 'target':
                return QIcon(':/plugins/legger/media/circle_blue.png')
            elif self.endpoint_feature.attributes()[2] == 'end':
                return QIcon(':/plugins/legger/media/circle_white.png')
            else:
                return QIcon()
        elif key in self.feature_keys:
            return self.feature[key]
        else:
            return self.data_dict.get(key, default_value)

    def set(self, key, value):

        # if key in self.feature_keys:
        #     return False  # not implemented yet
        # else:
        self.data_dict[key] = value
        return True


class TreeItem(object):
    """
    a python object used to return row/column data, and keep note of
    it's parents and/or children
    """

    def __init__(self, hydrovak, parent):
        self.hydrovak = hydrovak
        self.parent_item = parent
        self.childs = []

    def __repr__(self):
        return "%s - %i childs" % (self.hydrovak, len(self.childs))

    def appendChild(self, item):
        self.childs.append(item)
        if item.parent() != self:
            item.setParent(self)

    def insertChild(self, index, item):
        self.childs.insert(index, item)
        if item.parent() != self:
            item.setParent(self)

    def clearChilds(self):
        self.childs = []

    def setParent(self, parent_item):
        self.parent_item = parent_item
        if self not in parent_item.childs:
            self.appendChild(self)

    def child(self, row):
        return self.childs[row]

    def childCount(self):
        return len(self.childs)

    def columnCount(self):
        return len(HORIZONTAL_HEADERS)

    def data(self, column, qvalue=False):
        if self.hydrovak is None:
            if column == 0:
                return 'root'
            if column == 1:
                return ""
        else:
            return self.hydrovak.data(column, qvalue)
        return None

    def setData(self, column, value, role, signal=True):
        ret = self.hydrovak.setData(column, value, role)
        # if signal and ret:
        #     if self.item.model:
        #         index = self.item.model.index(
        #             self.item.get_row_nr(), self.field.column_nr)
        #         self.item.model.dataChanged.emit(index, index)
        return ret

    def icon(self):
        return self.hydrovak.get('icon')

    def parent(self):
        return self.parent_item

    def row(self):
        if self.parent_item:
            return self.parent_item.childs.index(self)
        return 0

    def up(self, end=None):

        up_list = []
        node = self
        while node != end and node is not None and node.hydrovak is not None:
            up_list.append(node)
            if node.row() != 0:
                node = node.parent().child(node.row() - 1)
            else:
                node = node.parent()

        if node is not None:
            up_list.append(node)
        return up_list

    def younger(self):
        nodes = []
        if self.row() < self.parent().childCount() - 1:
            nodes.append(self.parent().child(self.row() + 1))
        if self.childCount() > 0:
            nodes.append(self.childs[0])
        return nodes

    def older(self):
        if self.row() == 0:
            return self.parent()
        else:
            return self.parent().child(self.row() - 1)


class LeggerTreeModel(QtCore.QAbstractItemModel):
    """
    a model to display a few names, ordered by sex
    """

    def __init__(self, parent=None, root_item=None):
        super(LeggerTreeModel, self).__init__(parent)

        if root_item:
            self.rootItem = root_item
        else:
            self.rootItem = TreeItem(None, None)
        self.parents = {0: self.rootItem}
        self.tree_widget = None

        # shortcuts to items (only one active at a time
        self.ep = None
        self.sp = None
        self.hover = None
        self.selected = None

    def setTreeWidget(self, widget):
        """
        set reference to tree widget, to make it possible to check visual state
        widget (QTreeWidget): Treewidget
        :return:
        """
        self.tree_widget = widget

    def columnCount(self, parent=None):
        if parent and parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return len(HORIZONTAL_HEADERS)

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            if HORIZONTAL_HEADERS[index.column()].get('field_type') != CHECKBOX_FIELD:
                return item.data(index.column())
        elif role == Qt.BackgroundRole:
            if item.hydrovak.get('selected'):
                return QBrush(QColor(*settings.SELECT_COLOR))
            elif item.hydrovak.get('hover'):
                return QBrush(QColor(*settings.HOVER_COLOR))
            else:
                return QBrush(Qt.transparent)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter
        elif role == Qt.CheckStateRole:
            if HORIZONTAL_HEADERS[index.column()].get('field_type') == CHECKBOX_FIELD:
                return item.data(index.column(), qvalue=True)
            else:
                return None
        elif role == QtCore.Qt.DecorationRole and index.column() == 0:
            return item.icon()
        elif role == QtCore.Qt.DecorationRole and HORIZONTAL_HEADERS[index.column()]['field'] == 'add':
            return QIcon(':/plugins/legger/media/plus.png')
        elif role == QtCore.Qt.UserRole:
            if item:
                return item
        return None

    def setData(self, index, value, role=Qt.DisplayRole, signal=True):
        """
        required Qt function for setting data, including sending of signals
        :param index: QtModelIndex instance
        :param value: new value for ItemField
        :param role: Qt role (DisplayRole, CheckStateRole)
        :return: was setting value successful
        """
        if not index.isValid():
            return None

        item = index.internalPointer()

        # dataChanged.emit is done within the ItemField, triggered by setting
        # the value
        changed = item.setData(index.column(), value, role)
        if changed:
            # todo: check if this can be done more efficient with a single emit
            if HORIZONTAL_HEADERS[index.column()].get('single_selection') and value in [True, Qt.Checked]:
                self.set_column_value(index.column(), False, skip=index)
            self.data_change_post_process(index, index)

            if signal:
                self.dataChanged.emit(index, index)
        return changed

    def get_column_nr(self, key):
        header = HEADER_DICT.get(key)
        column_nr = HORIZONTAL_HEADERS.index(header)
        return column_nr

    def setDataItemKey(self, item, key, value, role=Qt.DisplayRole, signal=True):
        column_nr = self.get_column_nr(key)
        index = self.createIndex(item.row(), column_nr, item)
        self.setData(index, value, role, signal)

    def set_column_value(self, column, value, skip=None):
        """
        set all values in column to this value
        column (int or string): column number or field_name
        value: new value for column
        skip (QModelIndex): index of item which will be skipped in setting value
        return: if there are fields changed
        """

        if type(column) != int:
            column = HORIZONTAL_HEADERS.index(HEADER_DICT.get(column))

        def loop_nodes(node):
            """
            a function called recursively, looking at all nodes beneath node
            """
            changed = False
            for child in node.childs:
                index = self.createIndex(child.row(), column, child)
                if index != skip:
                    changed = self.setData(index, value)

                if child.childCount() > 0:
                    changed_child = loop_nodes(child)
                    changed = changed or changed_child
            return changed

        changed = loop_nodes(self.parents[0])
        return changed

    def setNewTree(self, root_children):
        self.clear()
        self.beginInsertRows(QtCore.QModelIndex(), 0, len(root_children))
        for child in root_children:
            self.rootItem.appendChild(child)
        self.endInsertRows()

    def flags(self, index):

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if HORIZONTAL_HEADERS[index.column()].get('field_type') == CHECKBOX_FIELD:
            flags |= Qt.ItemIsUserCheckable | Qt.ItemIsEditable

        return flags

    def clear(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, self.rootItem.childCount())
        self.rootItem.clearChilds()
        self.endRemoveRows()

    def headerData(self, column, orientation, role):
        if (orientation == QtCore.Qt.Horizontal and
                role == QtCore.Qt.DisplayRole):
            try:
                return HORIZONTAL_HEADERS[column].get('header', HORIZONTAL_HEADERS[column]['field'])
            except IndexError:
                pass
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        if not childItem:
            return QtCore.QModelIndex()

        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            p_item = self.rootItem
        else:
            p_item = parent.internalPointer()
        return p_item.childCount()

    def setupModelData(self):
        for hydrovak in self.hydrovakken:
            new_item = TreeItem(hydrovak, self.rootItem)
            self.rootItem.appendChild(new_item)

    def searchModel(self, hydrovak):
        """
        get the modelIndex for a given appointment
        """

        def searchNode(node):
            """
            a function called recursively, looking at all nodes beneath node
            """
            for child in node.childs:
                if hydrovak == child.hydrovak:
                    index = self.createIndex(child.row(), 0, child)
                    return index

                if child.childCount() > 0:
                    result = searchNode(child)
                    if result:
                        return result

        retarg = searchNode(self.parents[0])
        return retarg

    def find_younger(self, start_index, key, value):

        def search(node):
            """
            recursive function checking siblings
            :param index:
            :return:
            """
            if node.row() < node.parent().childCount() - 1:
                young = node.parent().child(node.row() + 1)
                if young.hydrovak.get(key) == value:
                    index = self.createIndex(young.row(), 0, young)
                    return index
                result = search(young)
                if result:
                    return result

            if node.childCount() > 0:
                child = node.child(0)
                if child.hydrovak.get(key) == value:
                    index = self.createIndex(child.row(), 0, child)
                    return index
                result = search(child)
                if result:
                    return result

        start_item = start_index.internalPointer()

        result = search(start_item)
        return result

    def find_older(self, start_index, key, value):

        def search(node):
            """
            recursive function checking parents
            :param index:
            :return:
            """
            if node is None or node.hydrovak is None:
                return None

            if node.hydrovak.get(key) == value:
                index = self.createIndex(node.row(), 0, node)
                return index

            if node.row() > 0:
                result = search(node.parent().child(node.row() - 1))
            else:
                result = search(node.parent())
            if result:
                return result

        start_item = start_index.internalPointer()
        result = search(start_item)
        return result

    def get_open_endleaf(self, tree_widget=None):
        """

        tree_widget (QTreeWidget):up[-1].hydrovak.get('distance') optional. Overwrites the widget set with the function .setTreeWidget
        :return:
        """
        if tree_widget is None:
            tree_widget = self.tree_widget

        def loop(node):
            index = self.createIndex(node.row(), 0, node)
            if tree_widget and tree_widget.isExpanded(index):  # node.childCount() > 0 and :
                result = loop(node.child(0))
            elif node.parent().childCount() - 1 == node.row():
                return node
            else:
                result = loop(node.parent().child(node.row() + 1))

            if result:
                return result

        result = loop(self.rootItem.child(0))
        return result

    def column(self, column_nr):
        return HORIZONTAL_HEADERS[column_nr]

    @property
    def columns(self):
        return HORIZONTAL_HEADERS

    def set_column_sizes_on_view(self, tree_view):
        """Helper function for applying the column sizes on a view.

        :table_view: table view instance that uses this model
        """

        for i, col in enumerate(HORIZONTAL_HEADERS):
            width = col.get('column_width')
            if width:
                tree_view.setColumnWidth(i, width)
            if not col.get('show', True):
                tree_view.setColumnHidden(i, True)

    def data_change_post_process(self, index, to_index):

        col = self.column(index.column())

        if col['field'] == 'hover':
            value = self.data(index, role=Qt.CheckStateRole)
            if value:
                self.hover = index.internalPointer()
            elif index.internalPointer() == self.hover:
                self.hover = None

            for colnr in range(0, len(HORIZONTAL_HEADERS)):
                self.tree_widget.update(self.index(index.row(), colnr, index.parent()))

        elif col['field'] == 'selected':
            value = self.data(index, role=Qt.CheckStateRole)
            if value:
                self.selected = index.internalPointer()
                self.tree_widget.update(index)

            elif index.internalPointer() == self.selected:
                self.selected = None

            for colnr in range(0, len(HORIZONTAL_HEADERS)):
                self.tree_widget.update(self.index(index.row(), colnr, index.parent()))

        elif col['field'] == 'sp':
            value = self.data(index, role=Qt.CheckStateRole)
            if value:
                index_ep = self.find_younger(start_index=index, key='ep', value=True)
                if index_ep is None:
                    leaf_endpoint = self.get_open_endleaf()
                    self.setDataItemKey(
                        leaf_endpoint, 'ep', True, role=Qt.CheckStateRole)
                else:
                    self.ep = index_ep.internalPointer()
                    self.sp = index.internalPointer()
            else:
                self.ep = None

        elif col['field'] == 'ep':
            value = self.data(index, role=Qt.CheckStateRole)
            if value:
                index_sp = self.find_older(start_index=index, key='sp', value=True)
                if index_sp is None:
                    self.setDataItemKey(
                        self.rootItem.child(0), 'sp', True, role=Qt.CheckStateRole)
                else:
                    self.ep = index.internalPointer()
                    self.sp = index_sp.internalPointer()
            else:
                self.ep = None
