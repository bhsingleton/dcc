import os
import stat

from enum import IntEnum
from datetime import datetime
from Qt import QtCore, QtWidgets
from . import qfilepath

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FileHeaderLabels(IntEnum):

    Name = 0
    Type = 1
    Size = 2
    DateCreated = 3
    DateModified = 4


class QAbstractFileItemModel(QtCore.QAbstractItemModel):
    """
    Overload of QAbstractItemModel that outlines the base file item model logic.
    """

    # region Dunderscores
    __getters__ = {
        FileHeaderLabels.Name: lambda x: x.name,
        FileHeaderLabels.Type: lambda x: x.extension,
        FileHeaderLabels.Size: lambda x: x.stat.st_size,
        FileHeaderLabels.DateCreated: lambda x: datetime.fromtimestamp(x.stat.st_ctime),
        FileHeaderLabels.DateModified: lambda x: datetime.fromtimestamp(x.stat.st_mtime),
    }

    __setters__ = {}

    def __init__(self, *paths, cwd='', parent=None):
        """
        Private method called after a new instance has been created.

        :type paths: Union[str, Tuple[str]]
        :type cwd: Union[str, Path]
        :type parent: QtCore.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QAbstractFileItemModel, self).__init__(parent=parent)

        # Declare private variables
        #
        self._paths = []
        self._headerLabels = [FileHeaderLabels.Name]

        # Check if paths were supplied
        #
        numPaths = len(paths)

        if numPaths > 0:

            self.setPaths(paths)

        # Check if CWD was supplied
        #
        if os.path.exists(cwd):

            self.setCwd(cwd)
    # endregion

    # region Methods
    def paths(self):
        """
        Returns the top-level paths for this model.

        :rtype: List[Path]
        """

        return self._paths

    def setPaths(self, paths):
        """
        Updates the top-level paths for this model.

        :type paths: List[Path]
        :rtype: None
        """

        self.beginResetModel()
        self._paths = [qfilepath.QFilePath(path) for path in paths]
        self.endResetModel()

    def setCwd(self, cwd):
        """
        Updates the current working directory.

        :type cwd: Union[str, Path]
        :rtype: None
        """

        self.setPaths(qfilepath.QFilePath(cwd).children)

    def headerLabels(self):
        """
        Returns the horizontal header labels for this model.

        :rtype: List[FileHeaderLabels]
        """

        return self._headerLabels

    def setHeaderLabels(self, headerLabels):
        """
        Updates the horizontal header labels for this model.

        :type headerLabels: List[FileHeaderLabels]
        :rtype: None
        """

        self._headerLabels = headerLabels

    def flags(self, index):
        """
        Returns the item flags for the given index.

        :type index: QtCore.QModelIndex
        :rtype: int
        """

        # Check if index is valid
        #
        path = self.pathFromIndex(index)

        if path is None:

            return QtCore.Qt.ItemIsDropEnabled

        # Check if path is read-only
        #
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        if not path.isReadOnly():

            flags |= QtCore.Qt.ItemIsEditable

        # Evaluate if path is drag/drop enabled
        #
        if (path.isFile() or path.isDir()) and not path.isDrive():

            flags |= QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

        return flags

    def pathFromIndex(self, index):
        """
        Returns the path associated with the given index.

        :type index: QtCore.QModelIndex
        :rtype: Path
        """

        return qfilepath.QFilePath.__instances__.get(index.internalId(), None)

    def parent(self, index):
        """
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid QModelIndex is returned.

        :type index: QtCore.QModelIndex
        :rtype: QtCore.QModelIndex
        """

        # Check if path exists
        #
        path = self.pathFromIndex(index)

        if path is None:

            return QtCore.QModelIndex()

        # Check if path is a root drive
        # Otherwise the path will have no parent!
        #
        paths = self.paths()

        if path in paths:

            return QtCore.QModelIndex()

        # Check if parent path is also a root drive
        #
        parent = path.parent

        if not parent.isDrive():

            row = parent.parent.children.index(parent)
            return self.createIndex(row, 0, id=hash(parent))

        else:

            return QtCore.QModelIndex()

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

            # Check if child is in range
            #
            path = self.pathFromIndex(parent)
            numChildren = len(path.children)

            if 0 <= row < numChildren:

                child = path.children[row]
                return self.createIndex(row, column, id=hash(child))

            else:

                return QtCore.QModelIndex()

        else:

            # Check if path is in range
            #
            numPaths = len(self._paths)

            if 0 <= row < numPaths:

                path = self._paths[row]
                return self.createIndex(row, column, id=hash(path))

            else:

                return QtCore.QModelIndex()

    def rowCount(self, parent=None):
        """
        Returns the number of rows under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        # Check if parent is valid
        #
        if parent.isValid():

            path = self.pathFromIndex(parent)
            return len(path.children)

        else:

            return len(self._paths)

    def columnCount(self, parent=None):
        """
        Returns the number of columns under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        return len(self._headerLabels)

    def mimeTypes(self):
        """
        Returns a list of supported mime types.

        :rtype: List[str]
        """

        return ['text/uri-list']

    def mimeData(self, indexes):
        """
        Returns an object that contains serialized items of data corresponding to the list of indexes specified.

        :type indexes: List[QtCore.QModelIndex]
        :rtype: QtCore.QMimeData
        """

        paths = set([str(self.pathFromIndex(index)) for index in indexes])
        log.info('Creating mime-data for URLs: %s' % paths)

        mimeData = QtCore.QMimeData()
        mimeData.setUrls(list(map(QtCore.QUrl.fromLocalFile, paths)))

        return mimeData

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

    def data(self, index, role=None):
        """
        Returns the data stored under the given role for the item referred to by the index.

        :type index: QtCore.QModelIndex
        :type role: int
        :rtype: Any
        """

        # Evaluate data role
        #
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):

            # Check if column has accessor method
            #
            path = self.pathFromIndex(index)
            func = self.__getters__.get(self.headerLabels()[index.column()], None)

            if callable(func):

                return str(func(path))

            else:

                return None

        elif role == QtCore.Qt.DecorationRole:

            return self.pathFromIndex(index).icon()

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

        # Evaluate orientation
        #
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:

            return FileHeaderLabels(section).name

        else:

            return super(QAbstractFileItemModel, self).headerData(section, orientation, role=role)
    # endregion
