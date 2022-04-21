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

    def paths(self):
        """
        Returns a list of content paths.

        :rtype: List[str]
        """

        # Call parent method
        #
        paths = super(FnScene, self).paths()

        # Append map paths
        #
        numMapPaths = pymxs.runtime.MapPaths.count()
        paths.extend([os.path.normpath(pymxs.runtime.MapPaths.get(i)) for i in range(1, numMapPaths + 1, 1)])

        # Append xref paths
        #
        numXRefPaths = pymxs.runtime.XRefPaths.count()
        paths.extend([os.path.normpath(pymxs.runtime.XRefPaths.get(i)) for i in range(1, numXRefPaths + 1, 1)])

        # Append session paths
        #
        for sessionType in (pymxs.runtime.Name('map'), pymxs.runtime.Name('xref')):

            numPaths = pymxs.runtime.SessionPaths.count(sessionType)
            paths.extend([os.path.normpath(pymxs.runtime.SessionPaths.get(sessionType, i)) for i in range(1, numPaths + 1, 1)])

        return list(set(paths))

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

    def playblast(self, filePath=None, startFrame=None, endFrame=None):
        """
        Creates a playblast using the supplied path.
        If no path is supplied then the default project path should be used instead!

        :type filePath: str
        :type startFrame: int
        :type endFrame: int
        :rtype: None
        """

        # Check if a file path was supplied
        #
        if filePath is None:

            projectPath = self.currentProjectDirectory()
            filePath = os.path.join(projectPath, 'previews', 'playblast.avi')

        # Check if start and end frame was supplied
        #
        startFrame = startFrame if not self.isNullOrEmpty(startFrame) else self.getStartTime()
        endFrame = endFrame if not self.isNullOrEmpty(endFrame) else self.getEndTime()

        # Create playblast
        #
        pymxs.runtime.createPreview(
            filename=filePath,
            outputAVI=True,
            start=startFrame,
            end=endFrame
        )

        self.transcodePlayblast(filePath)

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

    def iterNodes(self):
        """
        Returns a generator that yields all nodes from the scene.

        :rtype: iter
        """

        return iter(pymxs.runtime.objects)

    def getActiveSelection(self):
        """
        Returns the active selection.

        :rtype: list[pymxs.MXSWrapperBase]
        """

        selection = pymxs.runtime.selection
        return [selection[x] for x in range(selection.count)]

    def setActiveSelection(self, selection, replace=True):
        """
        Updates the active selection.

        :type selection: list
        :type replace: bool
        :rtype: None
        """

        # Check if selection should be replaced
        #
        if replace:

            pymxs.runtime.select(selection)

        else:

            pymxs.runtime.selectMore(selection)

    def clearActiveSelection(self):
        """
        Clears the active selection.

        :rtype: None
        """

        pymxs.runtime.clearSelection()
