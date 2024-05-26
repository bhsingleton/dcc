import os

from maya import cmds as mc
from six.moves import collections_abc
from dcc.maya.libs import sceneutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FileProperties(collections_abc.MutableMapping):
    """
    Overload of `MutableMapping` that interfaces with file properties.
    """

    # region Dunderscores
    __slots__ = ('__scene__', '__modified__', '__properties__')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FileProperties, self).__init__()

        # Declare private variables
        #
        self.__scene__ = sceneutils.currentFilePath()
        self.__modified__ = os.stat(self.__scene__).st_mtime if os.path.exists(self.__scene__) else 0
        self.__properties__ = {}

        # Reload scene properties
        #
        self.invalidate(force=True)

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[int, str]
        :rtype: Any
        """

        self.invalidate()
        return self.__properties__[key]

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[int, str]
        :type value: Any
        :rtype: None
        """

        mc.fileInfo(key, value)
        self.markDirty()
        self.invalidate(force=True)

    def __delitem__(self, key):
        """
        Private method that removes an indexed item.

        :type key: Union[int, str]
        :rtype: None
        """

        mc.fileInfo(remove=key)
        self.markDirty()
        self.invalidate(force=True)

    def __len__(self):
        """
        Private method that returns the number of properties.

        :rtype: int
        """

        self.invalidate()
        return len(self.__properties__)

    def __iter__(self):
        """
        Private method that returns a generator that yields property keys.

        :rtype: iter
        """

        self.invalidate()
        return iter(self.__properties__)
    # endregion

    # region Methods
    def keys(self):
        """
        Returns a generator that yields property keys.

        :rtype: iter
        """

        self.invalidate()
        return self.__properties__.keys()

    def values(self):
        """
        Returns a generator that yields property values.

        :rtype: iter
        """

        self.invalidate()
        return self.__properties__.values()

    def items(self):
        """
        Returns a generator that yields property key-value pairs.

        :rtype: iter
        """

        self.invalidate()
        return self.__properties__.items()

    def get(self, key, default=None):
        """
        Returns an indexed item.
        If no corresponding value exists then the default value is returned instead!

        :type key: str
        :type default: Any
        :rtype: Any
        """

        self.invalidate()
        return self.__properties__.get(key, default)

    def update(self, values):
        """
        Merges the supplied values with this instance.

        :type values: Union[List[Tuple[str, Any]], Dict[str, Any]]
        :rtype: FileProperties
        """

        iterable = None

        if isinstance(values, list):

            iterable = iter(values)

        elif isinstance(values, dict):

            iterable = values.items()

        else:

            raise TypeError(f'update() expects an array of key-value pairs ({type(values).__name__} given)!')

        for (key, value) in iterable:

            mc.fileInfo(key, value)

        self.markDirty()
        self.invalidate(force=True)

        return self

    def invalidate(self, force=False):
        """
        Updates the internal properties if the scene is dirty.

        :type force: bool
        :rtype: None
        """

        if self.isDirty() or force:

            self.__properties__ = dict(sceneutils.iterFileProperties())

    def isOutOfDate(self):
        """
        Evaluates if the scene file has been modified.

        :rtype: bool
        """

        return os.stat(self.__scene__).st_mtime != self.__modified__ if os.path.exists(self.__scene__) else False

    def isDirty(self):
        """
        Evaluates if this collection is dirty.

        :rtype: bool
        """

        fileChanged = sceneutils.currentFilePath() != self.__scene__
        fileDirty = sceneutils.isDirty()
        fileOutdated = self.isOutOfDate()

        return (fileChanged or fileDirty) or fileOutdated

    def markDirty(self):
        """
        Marks the scene as dirty requiring the user to save.

        :rtype: None
        """

        sceneutils.markDirty()
    # endregion
