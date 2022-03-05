import os

from PySide2 import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Path(object):
    """
    Overload of object used to represent a file path.
    Instances use a singleton pattern so that QFileItemModel can perform reverse lookups via hash ids.
    """

    # region Dunderscores
    __slots__ = ('_path', '_name', '_basename', '_extension', '_icon', '_stat', '_parent', '_children')
    __instances__ = {}
    __icons__ = QtWidgets.QFileIconProvider()

    def __new__(cls, path):
        """
        Private method called before a new instance is created.

        :type path: str
        :rtype: None
        """

        path = os.path.normpath(os.path.expandvars(path))
        handle = abs(hash(path.lower()))

        instance = cls.__instances__.get(handle, None)

        if instance is None:

            instance = super(Path, cls).__new__(cls)
            cls.__instances__[handle] = instance

        return instance

    def __init__(self, path):
        """
        Private method called after a new instance has been created.

        :type path: str
        :rtype: None
        """

        # Check if instance has already been initialized
        #
        if self.isInitialized():

            return

        # Call parent method
        #
        super(Path, self).__init__()

        # Declare private variables
        #
        self._path = os.path.normpath(os.path.expandvars(path))
        self._name = os.path.basename(self._path)
        self._basename, self._extension = os.path.splitext(self._name)
        self._icon = None
        self._stat = os.stat(self._path)
        self._parent = None
        self._children = None

    def __hash__(self):
        """
        Private method that returns a hashable value for this instance.

        :rtype: int
        """

        return abs(hash(self._path.lower()))

    def __len__(self):
        """
        Private method that evaluates the number of files derived from this directory.

        :rtype: int
        """

        return len(self.children)

    def __iter__(self):
        """
        Private method that returns a generator that yields child paths.

        :rtype: iter
        """

        return iter(self.children)

    def __getitem__(self, index):
        """
        Private method that returns an indexed child path.

        :type index: int
        :rtype: Path
        """

        return self.children[index]

    def __eq__(self, other):
        """
        Private method that evaluates if this and the other object are equivalent.

        :type other: Any
        :rtype: bool
        """

        return str(self) == str(other)

    def __ne__(self, other):
        """
        Private method that evaluates if this and the other object are not equivalent.

        :type other: Any
        :rtype: bool
        """

        return str(self) != str(other)

    def __str__(self):
        """
        Private method that converts this instance to a string.

        :rtype: str
        """

        return self.toString()

    def __repr__(self):
        """
        Private method that returns the string representation of this instance.

        :rtype: str
        """

        return '<%s at %s>' % (self.toString(), hex(id(self)))
    # endregion

    # region Properties
    @property
    def stat(self):
        """
        Getter method that returns the internal file stats.

        :rtype: os.stat_result
        """

        return self._stat

    @property
    def name(self):
        """
        Getter method that returns the base name of this path.

        :rtype: str
        """

        return self._name

    @property
    def parent(self):
        """
        Getter method that returns the parent of this path.

        :rtype: Path
        """

        # Check if parent has been initialized
        #
        if (self._parent is None or not self.isUpToDate()) and not self.isDrive():

            self.update()

        return self._parent

    @property
    def children(self):
        """
        Getter method that returns the children of this path.

        :rtype: List[Path]
        """

        # Check if children have been initialized
        #
        if self._children is None or not self.isUpToDate():

            self.update()

        return self._children
    # endregion

    # region Methods
    def isDir(self):
        """
        Evaluates if this path represents a directory.

        :rtype: bool
        """

        return os.path.isdir(self._path)

    def isDrive(self):
        """
        Evaluates if this path represents a drive letter.

        :rtype: bool
        """

        return self._path == os.path.dirname(self._path)

    def isFile(self):
        """
        Evaluates if this path represents a file.

        :rtype: bool
        """

        return os.path.isfile(self._path)

    def isLink(self):
        """
        Evaluates if this path represents a file.

        :rtype: bool
        """

        return os.path.islink(self._path)

    def icon(self):
        """
        Returns the icon associated with this path.

        :rtype: QtGui.QIcon
        """

        # Check if icon has been initialized
        #
        if self._icon is not None:

            return self._icon

        # Check if this is a directory
        #
        if self.isDrive():

            self._icon = self.__icons__.icon(QtWidgets.QFileIconProvider.Drive)

        elif self.isDir():

            self._icon = self.__icons__.icon(QtWidgets.QFileIconProvider.Folder)

        else:

            # Check if icon exists for mime type
            #
            icon = self.__icons__.icon(QtCore.QFileInfo(self.toString()))

            if not icon.isNull():

                self._icon = icon

            else:

                self._icon = self.__icons__.icon(QtWidgets.QFileIconProvider.File)

        return self._icon

    def isInitialized(self):
        """
        Evaluates if this instance's slots have been initialized.

        :rtype: bool
        """

        return all([hasattr(self, x) for x in self.__class__.__slots__])

    def isUpToDate(self):
        """
        Evaluates if this instance's stats are up to date.

        :rtype: bool
        """

        return os.stat(self._path).st_mtime == self.stat.st_mtime

    def update(self):
        """
        Forces this instance to update it's internal properties.

        :rtype: None
        """

        self._stat = os.stat(self._path)
        self._parent = Path(os.path.dirname(self._path))
        self._children = [Path(os.path.join(self._path, x)) for x in os.listdir(self._path)] if self.isDir() else []

    def toString(self):
        """
        Returns a string representation of this instance.

        :rtype: str
        """

        return self._path
    # endregion


class QFileItemModel(QtCore.QAbstractItemModel):
    """
    Overload of QAbstractItemModel used to represent a directory structure.
    """

    # region Dunderscores
    def __init__(self, cwd, parent=None):
        """
        Private method called after a new instance has been created.

        :type cwd: Union[str, Path]
        :type parent: QtCore.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QFileItemModel, self).__init__(parent=parent)

        # Declare private variables
        #
        self._cwd = None
        self._uniformSize = 24

        # Set current working directory
        #
        self.setCwd(cwd)
    # endregion

    # region Methods
    def cwd(self):
        """
        Returns the current working directory.

        :rtype: Path
        """

        return self._cwd

    def setCwd(self, cwd):
        """
        Updates the current working directory.

        :type cwd: Union[str, Path]
        :rtype: None
        """

        self.beginResetModel()
        self._cwd = Path(cwd)
        self.endResetModel()

    def uniformSize(self):
        """
        Returns the uniform size for all derived items.

        :rtype: QtCore.QSize
        """

        return self._uniformSize

    def setUniformSize(self, size):
        """
        Updates the uniform size for all derived items.

        :type size: QtCore.Size
        :rtype: None
        """

        self._uniformSize = size

    def pathFromIndex(self, index):
        """
        Returns the path associated with the given index.

        :type index: QtCore.QModelIndex
        :rtype: Path
        """

        return Path.__instances__.get(index.internalId(), None)

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
        if path is self.cwd():

            return QtCore.QModelIndex()

        # Check if parent path is also a root drive
        #
        parentPath = path.parent

        if not parentPath.isDrive():

            row = parentPath.parent.children.index(parentPath)
            return self.createIndex(row, 0, id=hash(parentPath))

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
        parentPath = self.cwd()

        if parent.isValid():

            parentPath = self.pathFromIndex(parent)

        # Get directory at row
        #
        numChildren = len(parentPath.children)

        if row < numChildren:

            directory = parentPath.children[row]
            return self.createIndex(row, column, id=hash(directory))

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
        parentPath = self.cwd()

        if parent.isValid():

            parentPath = self.pathFromIndex(parent)

        # Evaluate number of directories
        #
        return len(parentPath.children)

    def columnCount(self, parent=None):
        """
        Returns the number of columns under the given parent.

        :type parent: QtCore.QModelIndex
        :rtype: int
        """

        return 1

    def data(self, index, role=None):
        """
        Returns the data stored under the given role for the item referred to by the index.

        :type index: QtCore.QModelIndex
        :type role: int
        :rtype: Any
        """

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):

            return self.pathFromIndex(index).name

        elif role == QtCore.Qt.DecorationRole:

            return self.pathFromIndex(index).icon()

        elif role == QtCore.Qt.SizeHintRole:

            return QtCore.QSize(self._uniformSize, self._uniformSize)

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

        if section == 0 and orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:

            return 'Name'

        else:

            return super(QFileItemModel, self).headerData(section, orientation, role=role)
    # endregion
