import os

from abc import ABCMeta, abstractmethod
from six import with_metaclass, string_types
from six.moves import collections_abc
from dcc.abstract import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnScene(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase to outline function set behaviour for DCC scenes.
    """

    __slots__ = ()

    @abstractmethod
    def isNewScene(self):
        """
        Evaluates whether this is an untitled scene file.

        :rtype: bool
        """

        pass

    @abstractmethod
    def isSaveRequired(self):
        """
        Evaluates whether the open scene file has changes that need to be saved.

        :rtype: bool
        """

        pass

    @abstractmethod
    def currentFilename(self):
        """
        Returns the name of the open scene file.

        :rtype: str
        """

        pass

    @abstractmethod
    def currentFilePath(self):
        """
        Returns the path of the open scene file.

        :rtype: str
        """

        pass

    @abstractmethod
    def currentDirectory(self):
        """
        Returns the directory of the open scene file.

        :rtype: str
        """

        pass

    @abstractmethod
    def currentProjectDirectory(self):
        """
        Returns the current project directory.

        :rtype: str
        """

        pass

    @abstractmethod
    def getStartTime(self):
        """
        Returns the current start time.

        :rtype: int
        """

        pass

    @abstractmethod
    def setStartTime(self, startTime):
        """
        Updates the start time.

        :type startTime: int
        :rtype: None
        """

        pass

    @abstractmethod
    def getEndTime(self):
        """
        Returns the current end time.

        :rtype: int
        """

        pass

    @abstractmethod
    def setEndTime(self, endTime):
        """
        Updates the end time.

        :type endTime: int
        :rtype: None
        """

        pass

    @abstractmethod
    def getTime(self):
        """
        Returns the current time.

        :rtype: int
        """

        pass

    @abstractmethod
    def setTime(self, time):
        """
        Updates the current time.

        :type time: int
        :rtype: None
        """

        pass

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

    def expandFilePath(self, filePath):
        """
        Expands any file path that may contain an environment variable or relative syntax.

        :type filePath: str
        :rtype: str
        """

        # Check for empty strings
        #
        if self.isNullOrEmpty(filePath):

            return filePath

        # Evaluate any environment variables
        #
        filePath = os.path.expandvars(filePath)

        if os.path.isabs(filePath):

            return os.path.normpath(filePath)

        else:

            return os.path.normpath(os.path.join(self.currentProjectDirectory(), filePath))

    @abstractmethod
    def iterTextures(self):
        """
        Returns a generator that yields all texture paths inside the scene.
        All textures must be yielded as fully qualified file paths!

        :rtype: iter
        """

        pass

    def textures(self):
        """
        Returns a list of texture paths from the scene.

        :rtype: list[str]
        """

        return list(self.iterTextures())

    def iterMissingTextures(self):
        """
        Returns a generator that yields all missing texture paths from the scene.

        :rtype: iter
        """

        for texturePath in self.iterTextures():

            if not os.path.exists(texturePath):

                yield texturePath

            else:

                continue

    def missingTextures(self):
        """
        Returns a list of missing texture paths from the scene.

        :rtype: list[str]
        """

        return list(self.iterMissingTextures())

    @abstractmethod
    def iterFileProperties(self):
        """
        Returns a generator that yields file properties as key-value pairs.

        :rtype: iter
        """

        pass

    def fileProperties(self):
        """
        Returns a dictionary of file properties.

        :rtype: dict
        """

        return dict(self.iterFileProperties())

    @abstractmethod
    def getFileProperty(self, key, default=None):
        """
        Returns a file property value.
        An optional default value can be provided if no key is found.

        :type key: str
        :type default: Any
        :rtype: Any
        """

        pass

    @abstractmethod
    def setFileProperty(self, key, value):
        """
        Updates a file property value.
        If the item does not exist it will be automatically added.

        :type key: str
        :type value: str
        :rtype: None
        """

        pass

    def updateFileProperties(self, properties):
        """
        Updates the file properties using a dictionary.
        This method will not erase any pre-existing items but overwrite any duplicate keys.

        :type properties: dict
        :rtype: None
        """

        for (key, value) in properties.items():

            self.setFileProperty(key, value)

    @abstractmethod
    def getUpAxis(self):
        """
        Returns the up-axis that the scene is set to.

        :rtype: str
        """

        pass

    @abstractmethod
    def markDirty(self):
        """
        Marks the scene as dirty which will prompt the user for a save upon close.

        :rtype: None
        """

        pass

    @abstractmethod
    def markClean(self):
        """
        Marks the scene as clean which will not prompt the user for a save upon close.

        :rtype: None
        """

        pass
