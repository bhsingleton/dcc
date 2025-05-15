import os
import stat

from ...vendor.Qt import QtCore, QtWidgets

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFilePath(object):
    """
    Base class used to interface with files from a string path.
    Instances use a singleton pattern so external interfaces can perform reverse lookups via hash IDs.
    """

    # region Dunderscores
    __slots__ = ('_path', '_name', '_basename', '_extension', '_icon', '_stat', '_parent', '_children', '_siblings')
    __instances__ = {}
    __icons__ = QtWidgets.QFileIconProvider()

    def __new__(cls, path):
        """
        Private method called before a new instance is created.

        :type path: str
        :rtype: None
        """

        # Redundancy check
        #
        if isinstance(path, QFilePath):

            return path

        # Check if path is valid
        #
        absolutePath = os.path.normpath(os.path.expandvars(path))

        if not os.path.exists(absolutePath):

            return None

        # Check if instance already exists for path
        #
        handle = abs(hash(absolutePath.lower()))
        instance = cls.__instances__.get(handle, None)

        if instance is None:

            instance = super(QFilePath, cls).__new__(cls)
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
        super(QFilePath, self).__init__()

        # Declare private variables
        #
        self._path = os.path.normpath(os.path.expandvars(path))
        self._name = os.path.basename(self._path)
        self._basename, self._extension = '', ''
        self._stat = os.stat(self._path)
        self._parent = None
        self._children = None
        self._siblings = None
        self._icon = None

        if os.path.isfile(self._path):

            name, extension = os.path.splitext(self._name)
            self._basename, self._extension = name, extension.lstrip('.')

        else:

            self._basename, self._extension = self._name, ''

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

        return '<"%s" path at %s>' % (self.toString(), hex(id(self)))
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
    def basename(self):
        """
        Getter method that returns the base name of this path with no extensions.

        :rtype: str
        """

        return self._basename

    @property
    def name(self):
        """
        Getter method that returns the name from this path.

        :rtype: str
        """

        return self._name

    @property
    def extension(self):
        """
        Getter method that returns the file extension from this path.

        :rtype: str
        """

        return self._extension

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
        Getter method that returns the children from this path.

        :rtype: List[Path]
        """

        # Check if children have been initialized
        #
        if self._children is None or not self.isUpToDate():

            self.update()

        return self._children

    @property
    def siblings(self):
        """
        Getter method that returns the siblings from this path.

        :rtype: List[Path]
        """

        # Check if children have been initialized
        #
        if self._siblings is None or not self.isUpToDate():

            self.update()

        return self._siblings
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

    def isReadOnly(self):
        """
        Evaluates if this path represents a read-only file.

        :rtype: bool
        """

        return not bool(self.stat.st_mode & stat.S_IWRITE)

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
        Evaluates if this instance's stats are up-to-date.

        :rtype: bool
        """

        if os.path.exists(self._path):

            return os.stat(self._path).st_mtime == self.stat.st_mtime

        else:

            return True  # Safe to say we can no longer test for changes!

    def update(self):
        """
        Forces this instance to update its internal properties.

        :rtype: None
        """

        # Update internal stats
        #
        self._stat = os.stat(self._path)
        self._parent = QFilePath(os.path.dirname(self._path))

        # Re-populate child array
        #
        if self.isDir():

            children = tuple(map(lambda filename: os.path.join(self._path, filename), os.listdir(self._path)))
            filteredChildren = tuple(filter(lambda path: os.access(path, os.R_OK), children))

            directories = tuple(filter(lambda path: os.path.isdir(path), filteredChildren))
            filePaths = tuple(filter(lambda path: os.path.isfile(path), filteredChildren))
            sortedChildren = directories + filePaths

            self._children = list(map(QFilePath, sortedChildren))

        else:

            self._children = []

        # Re-populate siblings array
        #
        self._siblings = [path for path in self._parent.children if path is not self]

    def toString(self):
        """
        Returns a string representation of this instance.

        :rtype: str
        """

        return self._path
    # endregion
