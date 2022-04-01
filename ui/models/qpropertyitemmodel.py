import re
import json
import inspect
import shiboken2

from PySide2 import QtCore, QtWidgets, QtGui
from six import string_types, integer_types
from six.moves import collections_abc
from collections import namedtuple
from dcc.python import annotationutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


HierarchicalDataProperties = namedtuple('HierarchicalDataProperties', ['parent', 'children'])


class QPropertyItemModel(QtCore.QAbstractItemModel):
    """
    Overload of QAbstractItemModel used to represent python objects and their data properties.
    This model also supports hierarchical data properties for custom types!
    """

    # region Dunderscores
    __title__ = re.compile(r'([A-Z]?[a-z0-9_]+)')
    __builtins__ = (bool, int, float, str)

    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtCore.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QPropertyItemModel, self).__init__(parent=parent)

        # Declare private variables
        #
        self._invisibleRootItem = []
        self._headerLabels = ['key', 'value']
        self._internalIds = {}
    # endregion

    # region Methods
    def invisibleRootItem(self):
        """
        Returns the invisible root item.

        :rtype: object
        """

        return self._invisibleRootItem

    def setInvisibleRootItem(self, item):
        """
        Updates the invisible root item.

        :type item: object
        :rtype: None
        """

        self.beginResetModel()
        self._invisibleRootItem = item
        self._internalIds.clear()
        self.endResetModel()

    def encodeInternalId(self, *indices):
        """
        Returns an internal ID for the supplied item path.

        :rtype: int
        """

        internalId = abs(hash(indices))
        self._internalIds[internalId] = indices

        return internalId

    def decodeInternalId(self, internalId):
        """
        Returns an item path from the supplied internal ID.

        :type internalId: int
        :rtype: List[Union[str, int]]
        """

        return self._internalIds.get(internalId, [])

    @staticmethod
    def isNull(value):
        """
        Evaluates if the supplied value is not null.

        :type value: Any
        :rtype: bool
        """

        return value is None

    @staticmethod
    def isNullOrEmpty(value):
        """
        Evaluates if the supplied value is null or empty.

        :type value: Any
        :rtype: bool
        """

        if hasattr(value, '__len__'):

            return len(value) == 0

        elif value is None:

            return True

        else:

            raise TypeError('isNullOrEmpty() expects a sequence (%s given)!' % type(value).__name__)

    @classmethod
    def isPropertyResizable(cls, func):
        """
        Evaluates if the given property is resizable.

        :type func: function
        :rtype: bool
        """

        # Inspect return type
        #
        typeHints = annotationutils.getAnnotations(func)
        returnType = typeHints.get('return', None)

        if hasattr(returnType, '__args__'):

            # Inspect item type
            #
            numTypes = len(returnType.__args__)

            if numTypes == 1:

                return returnType.__args__[0] in cls.__builtins__

            else:

                return False

        else:

            return False

    @classmethod
    def isPropertyBuiltin(cls, func):
        """
        Evaluates if the given property returns a builtin type.

        :type func: function
        :rtype: bool
        """

        # Inspect return type
        #
        typeHints = annotationutils.getAnnotations(func)
        returnType = typeHints.get('return', None)

        if inspect.isclass(returnType):

            return issubclass(returnType, cls.__builtins__)

        else:

            return False
        
    def getPropertyTypeHint(self, func):
        """
        Returns the type hints for the given property accessor.

        :type func: function
        :rtype: type
        """

        typeHints = annotationutils.getAnnotations(func)
        return typeHints.get('return', None)

    def bindProperty(self, instance, func):
        """
        Returns a bound method from the supplied instance and function.

        :type instance: object
        :type func: function
        :rtype: function
        """

        # Check if function is valid
        #
        if inspect.isfunction(func) and hasattr(func, '__get__'):

            return func.__get__(instance, type(instance))

        else:

            return None

    def getPropertyAccessors(self, obj, name):
        """
        Returns the accessors from the supplied property.

        :type obj: object
        :type name: str
        :rtype: function, function
        """

        # Check if name is valid
        #
        if self.isNullOrEmpty(name):

            return None, None

        # Inspect object's base class
        #
        cls = type(obj)
        func = getattr(cls, name, None)

        if isinstance(func, property):

            return self.bindProperty(obj, func.fget), self.bindProperty(obj, func.fset)

        elif inspect.isfunction(func):

            otherName = 'set{name}'.format(name=self.titleize(func.__name__))
            otherFunc = getattr(cls, otherName, None)

            return self.bindProperty(obj, func), self.bindProperty(obj, otherFunc)

        else:

            return None, None

    def getPropertyValue(self, obj, name, default=None):
        """
        Returns the property value from the supplied item.

        :type obj: object
        :type name: str
        :type default: Any
        :rtype: Any
        """

        getter, setter = self.getPropertyAccessors(obj, name)

        if callable(getter):

            return getter()

        else:

            return default

    def setPropertyValue(self, obj, name, value):
        """
        Updates the property value for the supplied object.

        :type obj: object
        :type name: str
        :type value: Any
        :rtype: None
        """

        # Get if property is editable
        #
        getter, setter = self.getPropertyAccessors(obj, name)

        if callable(setter) and not self.isPropertyResizable(getter):

            setter(value)

    def getIcon(self, obj):
        """
        Returns the icon associated with the given item.

        :type obj: object
        :rtype: QtGui.QIcon
        """

        # Check if icon is resource path
        #
        icon = self.getPropertyValue(obj, 'icon')

        if isinstance(icon, string_types):

            icon = QtGui.QIcon(icon)

        return icon

    def itemFromIndex(self, index):
        """
        Returns the path associated with the given index.

        :type index: QtCore.QModelIndex
        :rtype: object
        """

        # Check if index is valid
        #
        if index.isValid():

            return self.itemFromInternalId(index.internalId())

        else:

            return None

    def itemFromInternalId(self, internalId):
        """
        Returns the item associated with the given internal id.

        :type internalId: Union[int, list]
        :rtype: object
        """

        # Inspect id type
        #
        if isinstance(internalId, integer_types):

            internalId = self.decodeInternalId(internalId)

        # Trace item path
        #
        current = self.invisibleRootItem()

        for index in internalId:

            # Inspect item type
            #
            if isinstance(index, integer_types) and isinstance(current, collections_abc.MutableSequence):

                current = current[index]

            elif isinstance(index, string_types) and isinstance(current, collections_abc.MutableMapping):

                current = current[index]

            else:

                raise TypeError('itemFromInternalId() expects a valid ID (%s given)!' % internalId)

        return current

    def propertyFromInternalId(self, internalId):
        """
        Returns the property accessors from the given internal id.

        :type internalId: List[Union[str, int]]
        :rtype: function, function
        """

        # Inspect id type
        #
        if isinstance(internalId, integer_types):

            internalId = self.decodeInternalId(internalId)

        # Get last string item
        #
        strings = [x for x in internalId if isinstance(x, string_types)]
        numStrings = len(strings)

        if numStrings == 0:

            return None, None

        # Evaluate path up to string
        #
        lastString = strings[-1]
        lastIndex = strings.index(lastString) + 1
        obj = self.itemFromInternalId(internalId[:lastIndex])

        return self.getPropertyAccessors(obj, lastString)

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

            # Call parent method
            #
            return super(QtCore.QAbstractItemModel, self).parent()

        elif numArgs == 1:

            # Evaluate internal id
            #
            index = args[0]
            internalId = self.decodeInternalId(index.internalId())

            if len(internalId) == 0:

                return QtCore.QModelIndex()

            # Inspect last index
            #
            item = self.itemFromInternalId(internalId)
            parentId = internalId[:-1]
            parentItem = self.itemFromInternalId(parentId)

            lastIndex = internalId[-1]

            if isinstance(lastIndex, integer_types):

                row = parentItem.index(item)
                return self.createIndex(row, 0, id=self.encodeInternalId(*parentId))

            elif isinstance(lastIndex, string_types):

                row = list(parentItem.keys()).index(lastIndex)
                return self.createIndex(row, 0, id=self.encodeInternalId(*parentId))

            else:

                return QtCore.QModelIndex()

        else:

            raise TypeError('parent() expects up to 1 argument (%s given)!' % numArgs)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        """
        Returns the index of the item in the model specified by the given row, column and parent index.

        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        # Check if parent is valid
        #
        parentItem = None
        parentId = []

        if parent.isValid():

            parentId = self.decodeInternalId(parent.internalId())
            parentItem = self.itemFromInternalId(parentId)

        else:

            parentItem = self.invisibleRootItem()

        # Evaluate parent type
        #
        if isinstance(parentItem, collections_abc.MutableSequence):

            # Evaluate sequence size
            #
            numItems = len(parentItem)

            if 0 <= row < numItems:

                childId = self.encodeInternalId(*parentId, row)
                return self.createIndex(row, column, id=childId)

            else:

                return QtCore.QModelIndex()

        elif isinstance(parentItem, collections_abc.MutableMapping):

            # Evaluate child array size
            #
            keys = list(parentItem.keys())
            numKeys = len(keys)

            if 0 <= row < numKeys:

                childId = self.encodeInternalId(*parentId, keys[row])
                return self.createIndex(row, column, id=childId)

            else:

                return QtCore.QModelIndex()

        else:

            return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of rows under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        # Get parent item
        #
        parentItem = None

        if parent.isValid():

            parentItem = self.itemFromIndex(parent)

        else:

            parentItem = self.invisibleRootItem()

        # Evaluate parent type
        #
        if isinstance(parentItem, (collections_abc.MutableSequence, collections_abc.MutableMapping)):

            return len(parentItem)

        else:

            return 0

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of columns under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        return len(self._headerLabels)

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

            parent = QtWidgets.QApplication.instance()

        # Evaluate contents size from font metrics
        #
        options = QtWidgets.QStyleOptionViewItem()
        options.initFrom(parent)

        contentSize = options.fontMetrics.size(QtCore.Qt.TextSingleLine, text)

        # Evaluate item size
        #
        style = parent.style()

        if shiboken2.isValid(style):  # QStyle pointers get deleted easily!

            return style.sizeFromContents(QtWidgets.QStyle.CT_ItemViewItem, options, contentSize, widget=parent)

        else:

            return contentSize

    @classmethod
    def titleize(cls, text):
        """
        Capitalizes the first letter of the supplied text.

        :type text: str
        :rtype: str
        """

        return ' '.join([x.title() for x in cls.__title__.findall(text)])

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
        lastRow = row + count

        self.beginInsertRows(parent, row, lastRow - 1)

        # Get parent item
        #
        parentItem = self.invisibleRootItem()

        if parent.isValid():

            parentItem = self.itemFromIndex(parent)

        # Verify parent is a mutable sequence
        #
        success = False

        if isinstance(parentItem, collections_abc.MutableSequence):

            # Insert items into list
            #
            for (index, item) in zip(range(row, lastRow), items):

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
        lastRow = row + count
        self.beginRemoveRows(parent, row, lastRow)

        # Get parent item
        #
        parentItem = self.invisibleRootItem()

        if parent.isValid():

            parentItem = self.itemFromIndex(parent)

        # Verify parent is mutable
        #
        success = False

        if isinstance(parentItem, collections_abc.MutableSequence):

            success = True
            del parentItem[row:lastRow]

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
        lastSourceRow = sourceRow + count
        lastDestinationRow = destinationRow + count

        self.beginMoveRows(sourceParent, sourceRow, lastSourceRow - 1, destinationParent, destinationRow)

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
        items = sourceItems[sourceRow:lastSourceRow]
        del items[sourceRow:lastSourceRow]

        for (index, item) in zip(range(destinationRow, lastDestinationRow), items):

            destinationItems.insert(index, item)

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
        mimeData.setText(json.dumps([{'row': x.row(), 'column': x.column(), 'id': x.internalId()} for x in indexes]))

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

        getter, setter = self.propertyFromInternalId(parent.internalId())
        return self.isPropertyResizable(getter)

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

        if numIndexes == 1 and action == QtCore.Qt.MoveAction:

            index = indexes[0]
            return self.moveRow(index.parent(), index.row(), parent, row)

        else:

            return False

    def flags(self, index):
        """
        Returns the item flags for the given index.

        :type index: QtCore.QModelIndex
        :rtype: int
        """

        # Check if index is valid
        #
        internalId = self.decodeInternalId(index.internalId())

        if len(internalId) == 0:

            return QtCore.Qt.NoItemFlags

        # Evaluate column with last index
        #
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        column = index.column()

        lastIndex = internalId[-1]

        if column == 0 and isinstance(lastIndex, integer_types):

            # Append draggable flags
            #
            flags |= QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

        elif column == 1 and (isinstance(lastIndex, string_types) or isinstance(lastIndex, integer_types)):

            # Check if item is editable
            #
            getter, setter = self.propertyFromInternalId(internalId)

            if callable(setter) and (self.isPropertyBuiltin(getter) or self.isPropertyResizable(getter)):

                flags |= QtCore.Qt.ItemIsEditable

        else:

            pass

        return flags

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

    def getDisplayKey(self, internalId):
        """
        Returns the display key for the given internal ID.

        :type internalId: List[Union[str, int]]
        :rtype: str
        """

        # Check if id is valid
        #
        length = len(internalId)

        if length == 0:

            return ''

        # Evaluate last index
        #
        item = self.itemFromInternalId(internalId)
        lastIndex = internalId[-1]

        if isinstance(lastIndex, integer_types):

            # Evaluate item type
            #
            if isinstance(item, collections_abc.MutableMapping):

                return type(item).__name__

            else:

                return '{name}[{index}]'.format(name=internalId[-2], index=lastIndex)

        elif isinstance(lastIndex, string_types):

            return lastIndex

        else:

            return ''

    def getDisplayValue(self, item):
        """
        Returns the display value for the given item.

        :type item: object
        :rtype: str
        """

        # Evaluate item type
        #
        if isinstance(item, collections_abc.MutableSequence):

            return '{count} item(s)'.format(count=len(item))

        elif isinstance(item, collections_abc.MutableMapping):

            return str(hex(id(item)))

        else:

            return str(item)

    def data(self, index, role=None):
        """
        Returns the data stored under the given role for the item referred to by the index.

        :type index: QtCore.QModelIndex
        :type role: int
        :rtype: Any
        """

        # Evaluate data role
        #
        internalId = self.decodeInternalId(index.internalId())
        item = self.itemFromInternalId(internalId)

        column = index.column()

        if role == QtCore.Qt.DisplayRole:

            return self.getDisplayKey(internalId) if column == 0 else self.getDisplayValue(item)

        elif role == QtCore.Qt.EditRole and column == 1:

            return item

        elif role == QtCore.Qt.SizeHintRole:

            text = self.data(index, role=QtCore.Qt.DisplayRole)
            return self.getTextSizeHint(text)

        elif role == QtCore.Qt.DecorationRole and column == 0:

            return self.getIcon(item)

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

        # Evaluate data role
        #
        internalId = self.decodeInternalId(index.internalId())
        lastIndex = internalId[-1]

        if role == QtCore.Qt.EditRole:

            # Evaluate parent item type
            #
            getter, setter = self.propertyFromInternalId(internalId)
            typeHint = self.getPropertyTypeHint(getter)

            if isinstance(lastIndex, string_types):

                # Check if property is resizable
                #
                if self.isPropertyResizable(getter):

                    self.resizeRow(value, typeHint.__args__[0], parent=index)
                    self.dataChanged.emit(index, index, [role])
                    return True

                elif self.isPropertyBuiltin(getter):

                    setter(value)
                    self.dataChanged.emit(index, index, [role])
                    return True

                else:

                    return False

            elif isinstance(lastIndex, integer_types):

                obj = getter()
                obj[lastIndex] = value
                self.dataChanged.emit(index, index, [role])
                return True

            else:

                return False

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

                return self.titleize(self._headerLabels[section])

            elif role == QtCore.Qt.SizeHintRole:

                text = self.headerData(section, orientation, role=QtCore.Qt.DisplayRole)
                return self.getTextSizeHint(text)

            else:

                return super(QPropertyItemModel, self).headerData(section, orientation, role=role)

        elif orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:

            # Evaluate data role
            #
            if role == QtCore.Qt.DisplayRole:

                return str(section)

            elif role == QtCore.Qt.SizeHintRole:

                text = self.headerData(section, orientation, role=QtCore.Qt.DisplayRole)
                return self.getTextSizeHint(text)

            else:

                return super(QPropertyItemModel, self).headerData(section, orientation, role=role)

        else:

            return super(QPropertyItemModel, self).headerData(section, orientation, role=role)
    # endregion
