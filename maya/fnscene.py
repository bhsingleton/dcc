import os

from maya import cmds as mc
from dcc.abstract import afnscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnScene(afnscene.AFnScene):
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
        Returns the current start time.

        :rtype: int
        """

        return int(mc.playbackOptions(query=True, min=True))

    def setStartTime(self, startTime):
        """
        Updates the start time.

        :type startTime: int
        :rtype: None
        """

        mc.playbackOptions(edit=True, min=startTime)

    def getEndTime(self):
        """
        Returns the current end time.

        :rtype: int
        """

        return int(mc.playbackOptions(query=True, max=True))

    def setEndTime(self, endTime):
        """
        Updates the end time.

        :type endTime: int
        :rtype: None
        """

        mc.playbackOptions(edit=True, max=endTime)

    def getTime(self):
        """
        Returns the current time.

        :rtype: int
        """

        return int(mc.currentTime(query=True))

    def setTime(self, time):
        """
        Updates the current time.

        :type time: int
        :rtype: int
        """

        mc.currentTime(time, edit=True)

    def enableAutoKey(self):
        """
        Enables the auto key mode.

        :rtype: None
        """

        mc.autoKeyframe(state=True)

    def disableAutoKey(self):
        """
        Disables the auto key mode.

        :rtype: None
        """

        mc.autoKeyframe(state=False)

    def iterTextures(self, absolute=False):
        """
        Returns a generator that yields all texture paths inside the scene.
        An optional keyword argument can be used to convert paths to absolute.

        :type absolute: bool
        :rtype: iter
        """

        # Iterate through file nodes
        #
        for nodeName in mc.ls(type='file'):

            # Check if path is valid
            #
            texturePath = mc.getAttr('%s.fileTextureName' % nodeName)

            if self.isNullOrEmpty(texturePath):

                continue

            # Check if absolute path should be yielded
            #
            if absolute:

                yield self.expandPath(texturePath)

            else:

                yield os.path.normpath(texturePath)

    def updateTextures(self, updates):
        """
        Applies all of the texture path updates to the associated file nodes.
        Each key-value pair should consist of the original and updates texture paths!

        :type updates: dict[str:str]
        :rtype: None
        """

        # Iterate through file nodes
        #
        for nodeName in mc.ls(type='file'):

            # Check if path is valid
            #
            texturePath = mc.getAttr('%s.fileTextureName' % nodeName)

            if self.isNullOrEmpty(texturePath):

                continue

            # Check if file node has an update
            #
            oldPath = os.path.normpath(texturePath)
            newPath = updates.get(oldPath)

            if newPath is not None:

                mc.setAttr('%s.fileTextureName' % nodeName, newPath, type='string')

    def reloadTextures(self):
        """
        Forces all of the texture nodes to reload.

        :rtype: None
        """

        # Iterate through file nodes
        #
        for nodeName in mc.ls(type='file'):

            mc.dgdirty('%s.fileTextureName' % nodeName)

    def iterFileProperties(self):
        """
        Returns a generator that yields file properties as key-value pairs.

        :rtype: iter
        """

        properties = mc.fileInfo(query=True)
        numProperties = len(properties)

        for i in range(0, numProperties, 2):

            yield properties[i], properties[i + 1].encode('ascii').decode('unicode-escape')

    def getFileProperty(self, key, default=None):
        """
        Returns a file property value.
        An optional default value can be provided if no key is found.

        :type key: str
        :type default: object
        :rtype: Union[str, int, float, bool]
        """

        return self.fileProperties().get(key, default)

    def setFileProperty(self, key, value):
        """
        Updates a file property value.
        If the item does not exist it will be automatically added.

        :type key: str
        :type value: str
        :rtype: None
        """

        mc.fileInfo(key, value)

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
