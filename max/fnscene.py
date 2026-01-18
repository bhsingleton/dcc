import pymxs
import os

from enum import IntEnum
from .libs import sceneutils
from ..abstract import afnscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FileExtensions(IntEnum):
    """
    Enum class of all 3ds-Max file extensions.
    """

    max = 0


class FnScene(afnscene.AFnScene):
    """
    Overload of `AFnScene` that implements the scene interface for 3ds-Max.
    """

    __slots__ = ()
    __extensions__ = FileExtensions

    def isNewScene(self):
        """
        Evaluates whether this is an untitled scene file.

        :rtype: bool
        """

        return sceneutils.isNewScene()

    def isSaveRequired(self):
        """
        Evaluates whether the open scene file has changes that need to be saved.

        :rtype: bool
        """

        return sceneutils.isSaveRequired()

    def new(self):
        """
        Opens a new scene file.

        :rtype: None
        """

        sceneutils.newScene()

    def save(self):
        """
        Saves any changes to the current scene file.

        :rtype: None
        """

        self.saveAs(self.currentFilePath())

    def saveAs(self, filePath):
        """
        Saves the current scene to the specified path.

        :type filePath: str
        :rtype: None
        """

        sceneutils.saveSceneAs(filePath)

    def open(self, filePath):
        """
        Opens the supplied scene file.

        :type filePath: str
        :rtype: bool
        """

        return sceneutils.openScene(filePath)

    def extensions(self):
        """
        Returns a list of scene file extensions.

        :rtype: Tuple[FileExtensions]
        """

        return FileExtensions.max,

    def isBatchMode(self):
        """
        Evaluates if the scene is running in batch mode.

        :rtype: bool
        """

        return sceneutils.isBatchMode()

    def currentFilename(self):
        """
        Returns the name of the open scene file.

        :rtype: str
        """

        return sceneutils.currentFilename()

    def currentFilePath(self):
        """
        Returns the path of the open scene file.

        :rtype: str
        """

        return sceneutils.currentFilePath()

    def currentDirectory(self):
        """
        Returns the directory of the open scene file.

        :rtype: str
        """

        return sceneutils.currentDirectory()

    def currentProjectDirectory(self):
        """
        Returns the current project directory.

        :rtype: str
        """

        return sceneutils.projectPath()

    def paths(self):
        """
        Returns a list of content paths.

        :rtype: List[str]
        """

        # Call parent method
        #
        paths = super(FnScene, self).paths()

        # Append scene paths
        #
        paths.extend(list(sceneutils.iterBitmapPaths(expand=True)))
        paths.extend(list(sceneutils.iterXRefPaths(expand=True)))
        paths.extend(list(sceneutils.iterSessionPaths(maps=True, xrefs=True)))

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

        pymxs.runtime.animationRange = pymxs.runtime.Interval(startTime, pymxs.runtime.animationRange.end)

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

        pymxs.runtime.animationRange = pymxs.runtime.Interval(pymxs.runtime.animationRange.start, endTime)

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

    def suspendViewport(self):
        """
        Pauses the current viewport from executing any redraws.

        :rtype: None
        """

        pymxs.runtime.disableSceneRedraw()

    def resumeViewport(self):
        """
        Un-pauses the current viewport to resume redraws.

        :rtype: None
        """

        pymxs.runtime.enableSceneRedraw()

    def refreshTextures(self):
        """
        Refreshes any texture changes in the active scene.

        :rtype: None
        """

        bitmaps = pymxs.runtime.getClassInstances(pymxs.runtime.BitmapTexture)

        for bitmap in bitmaps:

            bitmap.reload()

    def playblast(self, filePath=None, startFrame=None, endFrame=None, autoplay=True):
        """
        Creates a playblast using the supplied path.
        If no path is supplied then the default project path should be used instead!

        :type filePath: str
        :type startFrame: int
        :type endFrame: int
        :type autoplay: bool
        :rtype: None
        """

        # Check if a file path was supplied
        #
        if filePath is None:

            projectPath = self.currentProjectDirectory()
            filePath = os.path.join(projectPath, 'previews', '_scene.avi')

        # Create playblast
        #
        startFrame = startFrame if (not self.isNullOrEmpty(startFrame)) else self.getStartTime()
        endFrame = endFrame if (not self.isNullOrEmpty(endFrame)) else self.getEndTime()

        pymxs.runtime.createPreview(
            filename=filePath,
            outputAVI=True,
            start=startFrame,
            end=endFrame
        )

        # Transcode playblast
        #
        filePath = self.transcodePlayblast(filePath, delete=True)

        # Check if autoplay was requested
        #
        if autoplay:

            os.startfile(filePath)

    def iterFileProperties(self):
        """
        Generator method used to iterate through the file properties.
        For the love of christ don't forget...max arrays start at 1...

        :rtype: iter
        """

        return sceneutils.iterFileProperties()

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

        :type key: str
        :type value: str
        :rtype: None
        """

        pymxs.runtime.fileProperties.addProperty(pymxs.runtime.name('custom'), key, value)

    def deleteFileProperty(self, key):
        """
        Removes a file property value.

        :type key: str
        :rtype: None
        """

        pymxs.runtime.fileProperties.deleteProperty(pymxs.runtime.name('custom'), key)

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

    def execute(self, string):
        """
        Executes the supplied string.

        :type string: str
        :rtype: bool
        """

        try:

            pymxs.runtime.execute(string)
            return True

        except Exception as exception:

            log.warning(exception)
            return False

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
