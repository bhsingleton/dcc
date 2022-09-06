import json

from Qt import QtCore, QtWidgets, QtGui, QtCompat
from enum import IntEnum
from six import string_types, integer_types
from six.moves import collections_abc
from dcc import fnqt
from dcc.python import stringutils
from . import qpsonpath

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ViewDetails(IntEnum):

    Name = 0
    Type = 1
    Value = 2


class QPSONItemModel(QtCore.QAbstractItemModel):
    """
    Overload of QAbstractItemModel used to represent python objects and their data properties.
    This class uses pathing collections to navigate through the data structure.
    """

    # region Dunderscores
    __builtins__ = (bool, int, float, str, collections_abc.Sequence, collections_abc.Mapping)

    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtCore.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QPSONItemModel, self).__init__(parent=parent)

        # Declare private variables
        #
        self._qt = fnqt.FnQt()
        self._invisibleRootItem = None
        self._invisibleRootProperty = ''
        self._viewDetails = [ViewDetails.Name, ViewDetails.Value]
        self._headerLabels = [stringutils.pascalize(x.name, separator=' ') for x in self._viewDetails]
        self._internalIds = {}
    # endregion

    # region Properties
    @property
    def qt(self):
        """
        Getter method that returns the qt function set.

        :rtype: fnqt.FnQt
        """

        return self._qt

    @property
    def invisibleRootItem(self):
        """
        Getter method that returns the invisible root item.

        :rtype: object
        """

        return self._invisibleRootItem

    @invisibleRootItem.setter
    def invisibleRootItem(self, invisibleRootItem):
        """
        Setter method that updates the invisible root item.

        :type invisibleRootItem: object
        :rtype: None
        """

        self.beginResetModel()
        self._invisibleRootItem = invisibleRootItem
        self._internalIds.clear()
        self.endResetModel()

    @property
    def invisibleRootProperty(self):
        """
        Getter method that returns the invisible root property.

        :rtype: str
        """

        return self._invisibleRootProperty

    @invisibleRootProperty.setter
    def invisibleRootProperty(self, invisibleRootProperty):
        """
        Setter method that updates the invisible root property.

        :type invisibleRootProperty: str
        :rtype: None
        """

        self.beginResetModel()
        self._invisibleRootProperty = invisibleRootProperty
        self._internalIds.clear()
        self.endResetModel()

    @property
    def viewDetails(self):
        """
        Getter method that returns the view details for this model.

        :rtype: List[ViewDetails]
        """

        return self._viewDetails

    @viewDetails.setter
    def viewDetails(self, viewDetails):
        """
        Setter method that updates the view details for this model.

        :type viewDetails: List[ViewDetails]
        :rtype: None
        """

        # Signal reset in progress
        #
        self.beginResetModel()

        # Update view details
        #
        self._viewDetails = viewDetails
        self._headerLabels = [stringutils.pascalize(x.name, separator=' ') for x in self._viewDetails]

        # Signal reset complete
        #
        self.endResetModel()

    @property
    def dataProperties(self):
        """
        Getter method that returns the data properties.

        :rtype: List[str]
        """

        return self._dataProperties

    @dataProperties.setter
    def dataProperties(self, dataProperties):
        """
        Setter method that updates the data properties.

        :type dataProperties: List[str]
        :rtype: None
        """

        # Signal reset in progress
        #
        self.beginResetModel()

        # Update data properties
        #
        self._dataProperties = dataProperties
        self._headerLabels = [stringutils.pascalize(x, separator=' ') for x in self._dataProperties]

        # Signal reset complete
        #
        self.endResetModel()

    @property
    def hierarchicalDataProperty(self):
        """
        Getter method that returns the hierarchical data properties.

        :rtype: List[str]
        """

        return self._hierarchicalDataProperty

    @hierarchicalDataProperty.setter
    def hierarchicalDataProperty(self, hierarchicalDataProperty):
        """
        Setter method that updates the hierarchical data property.

        :type hierarchicalDataProperty: str
        :rtype: None
        """

        self.beginResetModel()
        self._hierarchicalDataProperty = hierarchicalDataProperty
        self.endResetModel()

    @property
    def headerLabels(self):
        """
        Getter method that returns the header labels.

        :rtype: List[str]
        """

        return self._headerLabels
    # endregion

    # region Methods
    def getTextSizeHint(self, text):
        """
        Returns a size hint for the supplied text.

        :type text: str
        :rtype: QtCore.QSize
        """

        # Check if model has a parent
        #
        parent = super(QtCore.QAbstractItemModel, self).parent()

        if parent is None:

            parent = self.qt.getApplication()

        # Evaluate contents size from font metrics
        #
        options = QtWidgets.QStyleOptionViewItem()
        options.initFrom(parent)

        contentSize = options.fontMetrics.size(QtCore.Qt.TextSingleLine, text)

        # Evaluate item size
        #
        style = parent.style()

        if QtCompat.isValid(style):  # QStyle pointers get deleted easily!

            return style.sizeFromContents(QtWidgets.QStyle.CT_ItemViewItem, options, contentSize, parent)

        else:

            return contentSize

    def encodeInternalId(self, *indices):
        """
        Returns an internal ID for the supplied item path.

        :rtype: int
        """

        path = qpsonpath.QPSONPath(indices, model=self)
        internalId = hash(path)

        self._internalIds[internalId] = path

        return internalId

    def decodeInternalId(self, internalId):
        """
        Returns an item path from the supplied internal ID.

        :type internalId: int
        :rtype: qpsonpath.QPSONPath
        """

        return self._internalIds.get(internalId, qpsonpath.QPSONPath(self.invisibleRootProperty, model=self))

    def itemFromIndex(self, index):
        """
        Returns the path associated with the given index.

        :type index: QtCore.QModelIndex
        :rtype: object
        """

        internalId = index.internalId()
        path = self.decodeInternalId(internalId)

        return path.value()

    def topLevelIndex(self, index):
        """
        Returns the top-level index from the supplied index.

        :type index: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        while index.parent().isValid():

            index = index.parent()

        return index

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of rows under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        # Evaluate parent item
        #
        parentId = self.decodeInternalId(parent.internalId())
        parentItem = parentId.value()

        if isinstance(parentItem, (collections_abc.Sequence, collections_abc.Mapping)):

            return len(parentItem)

        else:

            return 0

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of columns under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        return len(self.headerLabels)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        """
        Returns the index of the item in the model specified by the given row, column and parent index.

        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        # Evaluate parent type
        #
        parentId = self.decodeInternalId(parent.internalId())
        parentItem = parentId.value()

        if isinstance(parentItem, collections_abc.Sequence):

            # Evaluate sequence size
            #
            numItems = len(parentItem)

            if 0 <= row < numItems:

                childId = self.encodeInternalId(parentId, row)
                return self.createIndex(row, column, id=childId)

            else:

                return QtCore.QModelIndex()

        elif isinstance(parentItem, collections_abc.Mapping):

            # Evaluate child array size
            #
            keys = list(parentItem.keys())
            numKeys = len(keys)

            if 0 <= row < numKeys:

                childId = self.encodeInternalId(parentId, keys[row])
                return self.createIndex(row, column, id=childId)

            else:

                return QtCore.QModelIndex()

        else:

            return QtCore.QModelIndex()

    def parent(self, *args):
        """
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid QModelIndex is returned.

        :type index: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        # Inspect number of arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            return super(QtCore.QAbstractItemModel, self).parent()

        # Evaluate internal id
        #
        index = args[0]
        internalId = self.decodeInternalId(index.internalId())

        if internalId.isRoot():

            return QtCore.QModelIndex()

        # Evaluate last index alongside parent type
        #
        item = internalId.value()
        lastIndex = internalId[-1]

        parentId = internalId[:-1]
        parentItem = parentId.value()

        if isinstance(lastIndex, integer_types) and isinstance(parentItem, collections_abc.Sequence):

            row = parentItem.index(item)
            return self.createIndex(row, 0, id=self.encodeInternalId(*parentId))

        elif isinstance(lastIndex, string_types) and isinstance(parentItem, collections_abc.Mapping):

            row = list(parentItem.keys()).index(lastIndex)
            return self.createIndex(row, 0, id=self.encodeInternalId(*parentId))

        else:

            return QtCore.QModelIndex()

    def flags(self, index):
        """
        Returns the item flags for the given index.

        :type index: QtCore.QModelIndex
        :rtype: int
        """

        # Evaluate if index is draggable
        #
        internalId = self.decodeInternalId(index.internalId())
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        isArray = internalId.isArray()
        isElement = internalId.isElement()

        if isArray and isElement:

            flags |= QtCore.Qt.ItemIsDragEnabled

        # Evaluate if index is droppable
        #
        if isArray and not isElement:

            flags |= QtCore.Qt.ItemIsDropEnabled

        # Evaluate if index has children
        #
        isMapping = internalId.isMapping()

        if not isArray and not isMapping:

            flags |= QtCore.Qt.ItemNeverHasChildren

        # Evaluate if index is editable
        #
        column = index.column()
        isValueColumn = self.viewDetails.index(ViewDetails.Value) == column

        if internalId.isEditable() and isValueColumn:

            flags |= QtCore.Qt.ItemIsEditable

        # Evaluate if item is checkable
        #
        if internalId.acceptsType(bool) and isValueColumn:

            flags |= QtCore.Qt.ItemIsUserCheckable

        return flags

    def insertRow(self, row, item, parent=QtCore.QModelIndex()):
        """
        Inserts a single row before the given row in the child items of the parent specified.

        :type row: int
        :type item: object
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return self.insertRows(row, [item], parent=parent)

    def insertRows(self, row, items, parent=QtCore.QModelIndex()):
        """
        Inserts multiple rows before the given row in the child items of the parent specified.

        :type row: int
        :type items: List[object]
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        # Signal start of insertion
        #
        count = len(items)
        firstRow = row if row > 0 else self.rowCount(parent)
        lastRow = (firstRow + count) - 1

        self.beginInsertRows(parent, firstRow, lastRow)

        # Verify parent is a mutable sequence
        #
        parentItem = self.itemFromIndex(parent)
        success = False

        if isinstance(parentItem, collections_abc.MutableSequence):

            # Insert items into list
            #
            for (index, item) in zip(range(firstRow, lastRow + 1), items):

                parentItem.insert(index, item)

            success = True

        # Signal end of insertion
        #
        self.endInsertRows()
        return success

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        """
        Removes number of rows starting with the given row under parent from the model.
        Returns true if the rows were successfully removed; otherwise returns false.

        :type row: int
        :type count: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        # Signal start of insertion
        #
        lastRow = (row + count) - 1
        self.beginRemoveRows(parent, row, lastRow)

        # Verify parent is mutable
        #
        parentItem = self.itemFromIndex(parent)
        success = False

        if isinstance(parentItem, collections_abc.MutableSequence):

            del parentItem[row:(lastRow + 1)]
            success = True

        # Signal end of insertion
        #
        self.endRemoveRows()
        return success

    def appendRow(self, item, parent=QtCore.QModelIndex()):
        """
        Appends a single row at the end of child items for the parent specified.

        :type item: object
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return self.insertRow(self.rowCount(parent), item, parent=parent)

    def extendRow(self, items, parent=QtCore.QModelIndex()):
        """
        Appends a single row at the end of child items for the parent specified.

        :type items: List[object]
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return self.insertRows(self.rowCount(parent), items, parent=parent)

    def moveRow(self, sourceParent, sourceRow, destinationParent, destinationRow):
        """
        Moves the sourceRow, from the sourceParent, to the destinationRow, under destinationParent.
        Returns true if the rows were successfully moved; otherwise returns false.

        :type sourceParent: QtCore.QModelIndex
        :type sourceRow: int
        :type destinationParent: QtCore.QModelIndex
        :type destinationRow: int
        :rtype: bool
        """

        return self.moveRows(sourceParent, sourceRow, 1, destinationParent, destinationRow)

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationRow):
        """
        Moves the sourceRow count, from the sourceParent, to the destinationRow, under destinationParent.
        Returns true if the rows were successfully moved; otherwise returns false.

        :type sourceParent: QtCore.QModelIndex
        :type sourceRow: int
        :type count: int
        :type destinationParent: QtCore.QModelIndex
        :type destinationRow: int
        :rtype: bool
        """

        # Signal start of move
        #
        lastSourceRow = (sourceRow + count) - 1
        lastDestinationRow = (destinationRow + count) - 1

        self.beginMoveRows(sourceParent, sourceRow, lastSourceRow, destinationParent, destinationRow)

        # Check if indices are valid
        #
        if not sourceParent.isValid() or not destinationParent.isValid():

            self.endMoveRows()
            return False

        # Get parent items
        #
        sourceItems = self.itemFromIndex(sourceParent)
        destinationItems = self.itemFromIndex(destinationParent)

        if not isinstance(sourceItems, collections_abc.MutableSequence) or not isinstance(destinationItems, collections_abc.MutableSequence):

            self.endMoveRows()
            return False

        # Insert source items under destination parent
        #
        items = sourceItems[sourceRow:(lastSourceRow + 1)]
        del sourceItems[sourceRow:(lastSourceRow + 1)]

        for (i, item) in zip(range(destinationRow, lastDestinationRow + 1), items):

            destinationItems.insert(i, item)

        # Signal end of move
        #
        self.endMoveRows()
        return True

    def resizeRow(self, size, T, parent=QtCore.QModelIndex()):
        """
        Resizes the property array by the specified amount.

        :type size: int
        :type T: type
        :type parent: QtCore.QModelIndex
        :rtype: None
        """

        # Resize parent row
        #
        numRows = self.rowCount(parent)

        if size < numRows:

            self.removeRows(numRows - size, size, parent=parent)

        elif size > numRows:

            items = [T() for x in range(numRows, size, 1)]
            self.extendRow(items, parent=parent)

        else:

            pass

    def supportedDragActions(self):
        """
        Returns the drag actions supported by this model.

        :rtype: int
        """

        return QtCore.Qt.MoveAction

    def supportedDropActions(self):
        """
        Returns the drop actions supported by this model.

        :rtype: int
        """

        return QtCore.Qt.MoveAction

    def mimeTypes(self):
        """
        Returns a list of supported mime types.

        :rtype: List[str]
        """

        return ['text/plain']

    def mimeData(self, indexes):
        """
        Returns an object that contains serialized items of data corresponding to the list of indexes specified.

        :type indexes: List[QtCore.QModelIndex]
        :rtype: QtCore.QMimeData
        """

        mimeData = QtCore.QMimeData()
        mimeData.setText(json.dumps([{'row': x.row(), 'column': x.column(), 'id': x.internalId()} for x in indexes if x.column() == 0]))

        return mimeData

    def canDropMimeData(self, data, action, row, column, parent):
        """
        Evaluates if mime data can be dropped on the requested row.

        :type data: QtCore.QMimeData
        :type action: int
        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        internalId = self.decodeInternalId(parent.internalId())
        return internalId.isArray() and not internalId.isElement()

    def dropMimeData(self, data, action, row, column, parent):
        """
        Handles the data supplied by a drag and drop operation that ended with the given action.
        Returns true if the data and action were handled by the model; otherwise returns false.

        :type data: QtCore.QMimeData
        :type action: int
        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        indexes = [self.createIndex(x['row'], x['column'], id=x['id']) for x in json.loads(data.text())]
        numIndexes = len(indexes)

        if numIndexes > 0 and action == QtCore.Qt.MoveAction:

            index = indexes[0]
            self.moveRow(index.parent(), index.row(), parent, row)

        return False  # Must return false for move actions or else the model will remove rows?

    def details(self, index):
        """
        Evaluates the details for the given index.
        This method is intended to be used with indices derived from the details view mode.

        :type index: QtCore.QModelIndex
        :rtype: Any
        """

        path = self.decodeInternalId(index.internalId())
        column = index.column()
        viewDetail = self.viewDetails[column]

        if viewDetail == ViewDetails.Name:

            return path.toString()

        elif viewDetail == ViewDetails.Type:

            T = path.type()
            return getattr(T, '__name__', str(T))

        elif viewDetail == ViewDetails.Value:

            return path.value()

        else:

            return None

    def data(self, index, role=None):
        """
        Returns the data stored under the given role for the item referred to by the index.

        :type index: QtCore.QModelIndex
        :type role: int
        :rtype: Any
        """

        # Evaluate data role
        #
        column = index.column()

        if role == QtCore.Qt.DisplayRole:

            return str(self.details(index))

        elif role == QtCore.Qt.EditRole:

            path = self.decodeInternalId(index.internalId())
            return path.value()

        elif role == QtCore.Qt.DecorationRole and column == 0:

            path = self.decodeInternalId(index.internalId())
            return path.icon()

        else:

            return None

    def setData(self, index, value, role=None):
        """
        Sets the role data for the item at index to value.
        Returns true if successful; otherwise returns false.

        :type index: QtCore.QModelIndex
        :type value: Any
        :type role: int
        :rtype: bool
        """

        # Evaluate view mode
        #
        internalId = self.decodeInternalId(index.internalId())

        if role == QtCore.Qt.EditRole:

            # Evaluate path type
            #
            if internalId.isArray() and not internalId.isElement():

                return False

            else:

                internalId = self.decodeInternalId(index.internalId())
                internalId.setValue(value)

                return True

        else:

            return False

    def headerData(self, section, orientation, role=None):
        """
        Returns the data for the given role and section in the header with the specified orientation.

        :type section: int
        :type orientation: int
        :type role: int
        :rtype: Any
        """

        # Evaluate orientation type
        #
        if orientation == QtCore.Qt.Horizontal:

            # Evaluate data role
            #
            if role == QtCore.Qt.DisplayRole:

                return self.headerLabels[section]

            else:

                return super(QPSONItemModel, self).headerData(section, orientation, role=role)

        elif orientation == QtCore.Qt.Vertical:

            # Evaluate data role
            #
            if role == QtCore.Qt.DisplayRole:

                return str(section)

            else:

                return super(QPSONItemModel, self).headerData(section, orientation, role=role)

        else:

            return super(QPSONItemModel, self).headerData(section, orientation, role=role)
    # endregion
