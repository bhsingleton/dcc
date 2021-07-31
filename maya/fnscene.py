import maya.cmds as mc
import os

from ..abstract import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnScene(afnbase.AFnBase):
    """
    Overload of AFnBase used to interface with Maya scenes.
    """

    __slots__ = ()

    def isNewScene(self):
        """
        Evaluates whether this is an untitled scene file.

        :rtype: bool
        """

        return len(mc.file(query=True, sceneName=True)) == 0

    def isSaveRequired(self):
        """
        Evaluates whether the open scene file has changes that need to be saved.

        :rtype: bool
        """

        return mc.file(query=True, modified=True)

    def currentFilename(self):
        """
        Returns the name of the open scene file.

        :rtype: str
        """

        return os.path.split(self.currentFilePath())[-1]

    def currentFilePath(self):
        """
        Returns the path of the open scene file.

        :rtype: str
        """

        if not self.isNewScene():

            return os.path.normpath(mc.file(query=True, sceneName=True))

        else:

            return ''

    def currentDirectory(self):
        """
        Returns the directory of the open scene file.

        :rtype: str
        """

        return os.path.split(self.currentFilePath())[0]

    def currentProjectDirectory(self):
        """
        Returns the current project directory.

        :rtype: str
        """

        return os.path.normpath(mc.workspace(query=True, directory=True))

    def getStartTime(self):
        """
        Method used to retrieve the current start time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        return int(mc.playbackOptions(query=True, min=True))

    def setStartTime(self, startTime):
        """
        Method used to update the start time.

        :type startTime: int
        :rtype: None
        """

        mc.playbackOptions(edit=True, min=startTime)

    def getEndTime(self):
        """
        Method used to retrieve the current end time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        return int(mc.playbackOptions(query=True, max=True))

    def setEndTime(self, endTime):
        """
        Method used to update the end time.

        :type endTime: int
        :rtype: None
        """

        mc.playbackOptions(edit=True, max=endTime)

    def getTime(self):
        """
        Method used to get the current time.
        Be sure to compensate for number of ticks per frame!

        :rtype: int
        """

        return int(mc.currentTime(query=True))

    def setTime(self, time):
        """
        Method used to set the current time.
        Be sure to compensate for number of ticks per frame!

        :type time: int
        :rtype: int
        """

        mc.currentTime(time, edit=True)

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

        return mc.upAxis(query=True, axis=True)

    def markDirty(self):
        """
        Marks the scene as dirty which will prompt the user for a save upon close.

        :rtype: None
        """

        mc.file(modified=True)

    def markClean(self):
        """
        Marks the scene as clean which will not prompt the user for a save upon close.

        :rtype: None
        """

        mc.file(modified=False)
