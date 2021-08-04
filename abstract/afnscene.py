from abc import ABCMeta, abstractmethod
from six import with_metaclass

from . import afnbase

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
        Method used to retrieve the current start time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        pass

    @abstractmethod
    def setStartTime(self, startTime):
        """
        Method used to update the start time.

        :type startTime: int
        :rtype: None
        """

        pass

    @abstractmethod
    def getEndTime(self):
        """
        Method used to retrieve the current end time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        pass

    @abstractmethod
    def setEndTime(self, endTime):
        """
        Method used to update the end time.

        :type endTime: int
        :rtype: None
        """

        pass

    @abstractmethod
    def getTime(self, ):
        """
        Method used to get the current time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        pass

    @abstractmethod
    def setTime(self, time):
        """
        Method used to set the current time.
        Be sure to compensate for number of ticks per frame!

        :type time: int
        :rtype: int
        """

        pass

    @abstractmethod
    def iterFileProperties(self):
        """
        Generator method used to iterate through the file properties.
        For the love of christ don't forget...max arrays start at 1...

        :rtype: iter
        """

        pass

    @abstractmethod
    def getFileProperties(self):
        """
        Method used to retrieve the file properties as key-value pairs.

        :rtype: dict
        """

        pass

    @abstractmethod
    def getFileProperty(self, key, default=None):
        """
        Returns a file property value.
        An optional default value can be provided if no key is found.

        :type key: str
        :type default: object
        :rtype: Union[str, int, float, bool]
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

    @abstractmethod
    def setFileProperties(self, properties):
        """
        Updates the file properties using a dictionary.
        This method will not erase any pre-existing items but overwrite any duplicate keys.

        :type properties: dict
        :rtype: None
        """

        pass

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
