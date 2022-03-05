import ctypes

from PySide2 import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPropertyItemModel(QtCore.QAbstractItemModel):
    """
    Overload of QAbstractItemModel used to represent python objects and their properties.
    """

    # region Dunderscores
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
        self._objects = []
        self._dataProperties = []
        self._parentProperty = 'parent'
        self._childrenProperty = 'children'
        self._rowHeight = 24
    # endregion

    # region Methods
    def objects(self):
        """
        Returns the list of objects to display.

        :rtype: list[object]
        """

        return self._objects

    def setObjects(self, objects):
        """
        Updates the list of objects to display.

        :type objects: list[object]
        :rtype: None
        """

        self.beginResetModel()
        self._objects = objects
        self.endResetModel()

    def dataProperties(self):
        """
        Returns the list of properties to derive data from.

        :rtype: List[str]
        """

        return self._dataProperties

    def setDataProperties(self, dataProperties):
        """
        Updates the list of properties to derive data from.

        :type dataProperties: List[str]
        :rtype: None
        """

        self.beginResetModel()
        self._dataProperties = dataProperties
        self.endResetModel()

    def parentProperty(self):
        """
        Returns the parent property name for hierarchical data.

        :rtype: str
        """

        return self._parentProperty

    def setParentProperty(self, parentProperty):
        """
        Updates the parent property name for hierarchical data.

        :type parentProperty: str
        :rtype: None
        """

        self._parentProperty = parentProperty

    def childrenProperty(self):
        """
        Returns the children property name for hierarchical data.

        :rtype: str
        """

        return self._childrenProperty

    def setChildrenProperty(self, childrenProperty):
        """
        Updates the children property name for hierarchical data.

        :type childrenProperty: str
        :rtype: None
        """

        self._childrenProperty = childrenProperty

    def rowHeight(self):
        """
        Returns the row height for all derived items.

        :rtype: int
        """

        return self._rowHeight

    def setRowHeight(self, size):
        """
        Updates the row height for all derived items.

        :type size: int
        :rtype: None
        """

        self._rowHeight = size

    def propertyFromObject(self, obj, name, default=None):
        """
        Returns the property value from the supplied object.

        :type obj: object
        :type name: str
        :type default: Any
        :rtype: Any
        """

        func = getattr(obj.__class__, name, None)

        if isinstance(func, property):

            return func.fget(obj)

        elif callable(func):

            return func(obj)

        else:

            return default

    def objectFromIndex(self, index):
        """
        Returns the path associated with the given index.

        :type index: QtCore.QModelIndex
        :rtype: object
        """

        if index.isValid():

            return ctypes.cast(index.internalId(), ctypes.py_object).value

        else:

            return None

    def indexFromObject(self, obj):
        """
        Returns an index from the supplied object.

        :type obj: object
        :rtype: QtCore.QModelIndex
        """

        # Check for none type
        #
        if obj is None:

            return QtCore.QModelIndex()

        # Get parent from object
        #
        parent = self.propertyFromObject(obj, self._parentProperty, default=None)

        if parent is not None:

            children = self.propertyFromObject(obj, self._childrenProperty, default=[])
            row = children.index(obj)

            return self.createIndex(row, 0, id=id(obj))

        else:

            row = self._objects.index(obj)
            return self.createIndex(row, 0, id=id(obj))

    def parent(self, index):
        """
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid QModelIndex is returned.

        :type index: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        obj = self.objectFromIndex(index)
        parent = self.propertyFromObject(obj, self._parentProperty, default=None)

        return self.indexFromObject(parent)

    def index(self, row, column, parent=None):
        """
        Returns the index of the item in the model specified by the given row, column and parent index.

        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        # Check if parent is valid
        #
        if parent.isValid():

            parent = self.objectFromIndex(parent)
            children = self.propertyFromObject(parent, self._childrenProperty, default=None)

            return self.createIndex(row, column, id=id(children[row]))

        else:

            obj = self._objects[row]
            return self.createIndex(row, column, id=id(obj))

    def rowCount(self, parent=None):
        """
        Returns the number of rows under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        # Check if parent is valid
        #
        if parent.isValid():

            obj = self.objectFromIndex(parent)
            children = self.propertyFromObject(obj, self._childrenProperty, default=[])

            return len(children)

        else:

            return len(self._objects)

    def columnCount(self, parent=None):
        """
        Returns the number of columns under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        return len(self._properties)

    def getTextSizeHint(self, text, padding=6):
        """
        Returns a size hint for the supplied text.

        :type text: str
        :type padding: int
        :rtype: QtCore.QSize
        """

        application = QtWidgets.QApplication.instance()
        font = application.font()

        fontMetric = QtGui.QFontMetrics(font)
        width = fontMetric.width(text) + padding

        return QtCore.QSize(width, self._rowHeight)

    def data(self, index, role=None):
        """
        Returns the data stored under the given role for the item referred to by the index.

        :type index: QtCore.QModelIndex
        :type role: int
        :rtype: Any
        """

        obj = self.objectFromIndex(index)

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):

            return self.propertyFromObject(obj, self._dataProperties[index.column()])

        elif role == QtCore.Qt.SizeHintRole:

            text = self.data(index, role=QtCore.Qt.DisplayRole)
            return self.getTextSizeHint(text)

        else:

            return None

    def headerData(self, section, orientation, role=None):
        """
        Returns the data for the given role and section in the header with the specified orientation.

        :type section: int
        :type orientation: int
        :type role: int
        :rtype: Any
        """

        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:

            return self._dataProperties[section]

        elif orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:

            return str(section)

        else:

            return super(QPropertyItemModel, self).headerData(section, orientation, role=role)
    # endregion
