import pymxs
import os
import sys

from dcc.abstract import afnscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnScene(afnscene.AFnScene):
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

    def isBatchMode(self):
        """
        Evaluates if the the scene is running in batch mode.

        :rtype: bool
        """

        return os.path.split(sys.executable)[-1] == '3dsmaxbatch.exe'

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
        Returns the current start time.

        :rtype: int
        """

        return pymxs.runtime.animationRange.start

    def setStartTime(self, startTime):
        """
        Updates the start time.

        :type startTime: int
        :rtype: None
        """

        pymxs.runtime.animationRange.start = startTime

    def getEndTime(self):
        """
        Returns the current end time.

        :rtype: int
        """

        return pymxs.runtime.animationRange.end

    def setEndTime(self, endTime):
        """
        Updates the end time.

        :type endTime: int
        :rtype: None
        """

        pymxs.runtime.animationRange.end = endTime

    def getTime(self):
        """
        Returns the current time.

        :rtype: int
        """

        return pymxs.runtime.sliderTime

    def setTime(self, time):
        """
        Updates the current time.

        :type time: int
        :rtype: int
        """

        pymxs.runtime.sliderTime = time

    def enableAutoKey(self):
        """
        Enables the auto key mode.

        :rtype: None
        """

        pymxs.runtime.animateMode = True

    def disableAutoKey(self):
        """
        Disables the auto key mode.

        :rtype: None
        """

        pymxs.runtime.animateMode = False

    def iterTextures(self, absolute=False):
        """
        Returns a generator that yields all texture paths inside the scene.
        An optional keyword argument can be used to convert paths to absolute.

        :type absolute: bool
        :rtype: iter
        """

        # Iterate through bitmaps
        #
        for bitmap in pymxs.runtime.getClassInstances(pymxs.runtime.BitmapTexture):

            # Check if path is valid
            #
            texturePath = bitmap.filename

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

        :type updates: Dict[str, str]
        :rtype: None
        """

        # Iterate through bitmaps
        #
        for bitmap in pymxs.runtime.getClassInstances(pymxs.runtime.BitmapTexture):

            # Check if path is valid
            #
            texturePath = bitmap.filename

            if self.isNullOrEmpty(texturePath):

                continue

            # Check if bitmap has an update
            #
            oldPath = os.path.normpath(texturePath)
            newPath = updates.get(oldPath)

            if newPath is not None:

                log.info('%s.filename = %s' % (bitmap.name, newPath))
                bitmap.filename = newPath

        # Reload textures
        #
        self.reloadTextures()

    def reloadTextures(self):
        """
        Forces all of the texture nodes to reload.

        :rtype: None
        """

        # Iterate through bitmaps
        #
        for bitmap in pymxs.runtime.getClassInstances(pymxs.runtime.BitmapTexture):

            bitmap.reload()

    def iterFileProperties(self):
        """
        Generator method used to iterate through the file properties.
        For the love of christ don't forget...max arrays start at 1...

        :rtype: iter
        """

        # Iterate through properties
        #
        category = pymxs.runtime.name('custom')
        numProperties = pymxs.runtime.fileProperties.getNumProperties(category)

        for i in range(numProperties):

            key = pymxs.runtime.fileProperties.getPropertyName(category, i + 1)
            value = pymxs.runtime.fileProperties.getPropertyValue(category, i + 1)

            yield key, value

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

        pymxs.runtime.fileProperties.addProperty(pymxs.runtime.name('custom'), key, value)

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
