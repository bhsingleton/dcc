from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui, QtCompat
from enum import IntEnum
from dcc import fnqt
from dcc.python import stringutils
from dcc.maya.libs import dagutils
from . import qplugpath

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ViewDetails(IntEnum):
    """
    Overload of `IntEnum` that contains all the displayable data.
    """

    Name = 0
    Type = 1
    Value = 2


class QPlugItemModel(QtCore.QAbstractItemModel):
    """
    Overload of `QAbstractItemModel` used to represent Maya node plugs.
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
        super(QPlugItemModel, self).__init__(parent=parent)

        # Declare private variables
        #
        self._qt = fnqt.FnQt()
        self._invisibleRootItem = om.MObjectHandle()
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

        :rtype: om.MObject
        """

        return self._invisibleRootItem.object()

    @invisibleRootItem.setter
    def invisibleRootItem(self, invisibleRootItem):
        """
        Setter method that updates the invisible root item.

        :type invisibleRootItem: om.MObject
        :rtype: None
        """

        # Signal model reset in progress
        #
        self.beginResetModel()

        # Evaluate invisible root item
        #
        if invisibleRootItem is not None:

            self._invisibleRootItem = dagutils.getMObjectHandle(invisibleRootItem)
            self._internalIds.clear()

        else:

            self._invisibleRootItem = om.MObjectHandle()
            self._internalIds.clear()

        # Signal end of model reset
        #
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

        path = qplugpath.QPlugPath(indices, model=self)
        internalId = hash(path)

        self._internalIds[internalId] = path

        return internalId

    def decodeInternalId(self, internalId):
        """
        Returns an item path from the supplied internal ID.

        :type internalId: int
        :rtype: qplugpath.QPlugPath
        """

        return self._internalIds.get(internalId, qplugpath.QPlugPath(model=self))

    def plugFromIndex(self, index):
        """
        Returns the plug associated with the given index.

        :type index: QtCore.QModelIndex
        :rtype: om.MPlug
        """

        internalId = index.internalId()
        path = self.decodeInternalId(internalId)

        return path.plug()

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Returns the number of rows under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        return self.decodeInternalId(parent.internalId()).childCount()

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
        childId = parentId.child(row)

        if childId is not None:

            encodedId = self.encodeInternalId(childId)
            return self.createIndex(row, column, id=encodedId)

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

        else:

            parentId = internalId.parent()
            encodedId = self.encodeInternalId(parentId)
            row = parentId.position()

            return self.createIndex(row, 0, id=encodedId)

    def flags(self, index):
        """
        Returns the item flags for the given index.

        :type index: QtCore.QModelIndex
        :rtype: int
        """

        # Evaluate if index has children
        #
        internalId = self.decodeInternalId(index.internalId())
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        isArray = internalId.isArray()
        isCompound = internalId.isCompound()

        if not (isArray or isCompound):

            flags |= QtCore.Qt.ItemNeverHasChildren

        # Evaluate if index is editable
        #
        column = index.column()

        isEditable = internalId.isEditable()
        isValueColumn = self.viewDetails.index(ViewDetails.Value) == column

        if isEditable and isValueColumn:

            flags |= QtCore.Qt.ItemIsEditable

        return flags

    def supportedDragActions(self):
        """
        Returns the drag actions supported by this model.

        :rtype: int
        """

        return QtCore.Qt.IgnoreAction

    def supportedDropActions(self):
        """
        Returns the drop actions supported by this model.

        :rtype: int
        """

        return QtCore.Qt.IgnoreAction

    def mimeTypes(self):
        """
        Returns a list of supported mime types.

        :rtype: List[str]
        """

        return ['text/plain']

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

        return False

    def details(self, index):
        """
        Returns the details for the given index.
        This method is intended to be used with indices derived from the details view mode.

        :type index: QtCore.QModelIndex
        :rtype: Any
        """

        path = self.decodeInternalId(index.internalId())
        column = index.column()
        viewDetail = self.viewDetails[column]

        if viewDetail == ViewDetails.Name:

            return path.name()

        elif viewDetail == ViewDetails.Type:

            return path.typeName()

        elif viewDetail == ViewDetails.Value:

            return path.value()

        else:

            return None

    def icon(self, index):
        """
        Returns the icon for the given index.

        :type index: QtCore.QModelIndex
        :rtype: Any
        """

        # Verify this is the name column
        #
        column = index.column()
        path = self.decodeInternalId(index.internalId())
        isNameColumn = self.viewDetails.index(ViewDetails.Name) == column

        if isNameColumn:

            return path.icon()

        else:

            return None

    def data(self, index, role=None):
        """
        Returns the data stored under the given role for the item referred to by the index.

        :type index: QtCore.QModelIndex
        :type role: QtCore.Qt.ItemDataRole
        :rtype: Any
        """

        # Evaluate data role
        #
        if role == QtCore.Qt.DisplayRole:

            return str(self.data(index, role=QtCore.Qt.EditRole))

        elif role == QtCore.Qt.EditRole:

            return self.details(index)

        elif role == QtCore.Qt.DecorationRole:

            return self.icon(index)

        else:

            return None

    def setData(self, index, value, role=None):
        """
        Sets the role data for the item at index to value.
        Returns true if successful; otherwise returns false.

        :type index: QtCore.QModelIndex
        :type value: Any
        :type role: QtCore.Qt.ItemDataRole
        :rtype: bool
        """

        # Evaluate view mode
        #
        if role == QtCore.Qt.EditRole:

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

                return super(QPlugItemModel, self).headerData(section, orientation, role=role)

        elif orientation == QtCore.Qt.Vertical:

            # Evaluate data role
            #
            if role == QtCore.Qt.DisplayRole:

                return str(section)

            else:

                return super(QPlugItemModel, self).headerData(section, orientation, role=role)

        else:

            return super(QPlugItemModel, self).headerData(section, orientation, role=role)
    # endregion
