import pymxs
import os

from ..abstract import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnScene(afnbase.AFnBase):
    """
    Overload of AFnBase used to interface with 3DS Max scenes.
    """

    __slots__ = ()

    def isNewScene(self):
        """
        Evaluates whether this is an untitled scene file.

        :rtype: bool
        """

        return len(pymxs.runtime.maxFileName) == 0

    def isSaveRequired(self):
        """
        Evaluates whether the open scene file has changes that need to be saved.

        :rtype: bool
        """

        return pymxs.runtime.getSaveRequired()

    def currentFilename(self):
        """
        Returns the name of the open scene file.

        :rtype: str
        """

        if not self.isNewScene():

            return os.path.normpath(pymxs.runtime.maxFileName)

        else:

            return ''

    def currentFilePath(self):
        """
        Returns the path of the open scene file.

        :rtype: str
        """

        return os.path.join(self.currentDirectory(), self.currentFilename())

    def currentDirectory(self):
        """
        Returns the directory of the open scene file.

        :rtype: str
        """

        if not self.isNewScene():

            return os.path.normpath(pymxs.runtime.maxFilePath)

        else:

            return ''

    def currentProjectDirectory(self):
        """
        Returns the current project directory.

        :rtype: str
        """

        return os.path.normpath(pymxs.runtime.pathConfig.getCurrentProjectFolder())

    def getStartTime(self):
        """
        Method used to retrieve the current start time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        return pymxs.runtime.animationRange.start

    def setStartTime(self, startTime):
        """
        Method used to update the start time.

        :type startTime: int
        :rtype: None
        """

        pymxs.runtime.animationRange.start = startTime

    def getEndTime(self):
        """
        Method used to retrieve the current end time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        return pymxs.runtime.animationRange.end

    def setEndTime(self, endTime):
        """
        Method used to update the end time.

        :type endTime: int
        :rtype: None
        """

        pymxs.runtime.animationRange.end = endTime

    def getTime(self):
        """
        Method used to get the current time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        return pymxs.runtime.sliderTime

    def setTime(self, time):
        """
        Method used to set the current time.
        Be sure to compensate for number of ticks per frame!

        :type time: int
        :rtype: int
        """

        pymxs.runtime.sliderTime = time

    def iterFileProperties(self):
        """
        Generator method used to iterate through the file properties.
        For the love of christ don't forget...max arrays start at 1...

        :rtype: iter
        """

        pass

    def getFileProperties(self):
        """
        Method used to retrieve the file properties as key-value pairs.

        :rtype: dict
        """

        pass

    def getFileProperty(self, key, default=None):
        """
        Returns a file property value.
        An optional default value can be provided if no key is found.

        :type key: str
        :type default: object
        :rtype: Union[str, int, float, bool]
        """

        pass

    def setFileProperty(self, key, value):
        """
        Updates a file property value.
        If the item does not exist it will be automatically added.

        :type key: str
        :type value: str
        :rtype: None
        """

        pass

    def setFileProperties(self, properties):
        """
        Updates the file properties using a dictionary.
        This method will not erase any pre-existing items but overwrite any duplicate keys.

        :type properties: dict
        :rtype: None
        """

        pass

    def getUpAxis(self):
        """
        Returns the up-axis that the scene is set to.

        :rtype: str
        """

        return 'z'

    def markDirty(self):
        """
        Marks the scene as dirty which will prompt the user for a save upon close.

        :rtype: None
        """

        pymxs.runtime.setSaveRequired(True)

    def markClean(self):
        """
        Marks the scene as clean which will not prompt the user for a save upon close.

        :rtype: None
        """

        pymxs.runtime.setSaveRequired(False)
