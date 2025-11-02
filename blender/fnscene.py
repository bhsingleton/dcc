from enum import IntEnum
from ..abstract import afnscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FileExtensions(IntEnum):
    """
    Enum class of all the Blender file extensions.
    """

    blend = 0


class FnScene(afnscene.AFnScene):
    """
    Overload of `AFnBase` that implements the scene interface for Blender.
    """

    __slots__ = ()
    __extensions__ = FileExtensions

    def isNewScene(self):
        """
        Evaluates whether this is an untitled scene file.

        :rtype: bool
        """

        return False

    def isSaveRequired(self):
        """
        Evaluates whether the open scene file has changes that need to be saved.

        :rtype: bool
        """

        return False

    def new(self):
        """
        Opens a new scene file.

        :rtype: None
        """

        pass

    def save(self):
        """
        Saves any changes to the current scene file.

        :rtype: None
        """

        pass

    def saveAs(self, filePath):
        """
        Saves the current scene to the specified path.

        :type filePath: str
        :rtype: None
        """

        pass

    def open(self, filePath):
        """
        Opens the supplied scene file.

        :type filePath: str
        :rtype: bool
        """

        return False

    def extensions(self):
        """
        Returns a list of scene file extensions.

        :rtype: Tuple[FileExtensions]
        """

        return FileExtensions.blend,

    def isBatchMode(self):
        """
        Evaluates if the scene is running in batch mode.

        :rtype: bool
        """

        return False

    def currentFilename(self):
        """
        Returns the name of the open scene file.

        :rtype: str
        """

        return ''

    def currentFilePath(self):
        """
        Returns the path of the open scene file.

        :rtype: str
        """

        return ''

    def currentDirectory(self):
        """
        Returns the directory of the open scene file.

        :rtype: str
        """

        return ''

    def currentProjectDirectory(self):
        """
        Returns the current project directory.

        :rtype: str
        """

        return ''

    def paths(self):
        """
        Returns a list of content paths.

        :rtype: List[str]
        """

        return []

    def getStartTime(self):
        """
        Returns the current start time.

        :rtype: int
        """

        return 0

    def setStartTime(self, startTime):
        """
        Updates the start time.

        :type startTime: int
        :rtype: None
        """

        pass

    def getEndTime(self):
        """
        Returns the current end time.

        :rtype: int
        """

        return 0

    def setEndTime(self, endTime):
        """
        Updates the end time.

        :type endTime: int
        :rtype: None
        """

        pass

    def getTime(self):
        """
        Returns the current time.

        :rtype: int
        """

        return 0

    def setTime(self, time):
        """
        Updates the current time.

        :type time: int
        :rtype: int
        """

        pass

    def enableAutoKey(self):
        """
        Enables the auto key mode.

        :rtype: None
        """

        pass

    def disableAutoKey(self):
        """
        Disables the auto key mode.

        :rtype: None
        """

        pass

    def suspendViewport(self):
        """
        Pauses the current viewport from executing any redraws.

        :rtype: None
        """

        pass

    def resumeViewport(self):
        """
        Un-pauses the current viewport to resume redraws.

        :rtype: None
        """

        pass

    def refreshTextures(self):
        """
        Refreshes any texture changes in the active scene.

        :rtype: None
        """

        pass

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

        pass

    def iterFileProperties(self):
        """
        Generator method used to iterate through the file properties.
        For the love of christ don't forget...max arrays start at 1...

        :rtype: iter
        """

        return iter([])

    def getFileProperty(self, key, default=None):
        """
        Returns a file property value.
        An optional default value can be provided if no key is found.

        :type key: str
        :type default: object
        :rtype: Union[str, int, float, bool]
        """

        return

    def setFileProperty(self, key, value):
        """
        Updates a file property value.
        If the item does not exist it will be automatically added.

        :type key: str
        :type value: str
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

        pass

    def markClean(self):
        """
        Marks the scene as clean which will not prompt the user for a save upon close.

        :rtype: None
        """

        pass

    def execute(self, string, asPython=True):
        """
        Executes the supplied string.
        Be sure to specify if the string is in python or the native embedded language.

        :type string: str
        :type asPython: bool
        :rtype: None
        """

        pass

    def iterNodes(self):
        """
        Returns a generator that yields all nodes from the scene.

        :rtype: iter
        """

        return iter([])

    def getActiveSelection(self):
        """
        Returns the active selection.

        :rtype: list[pymxs.MXSWrapperBase]
        """

        return []

    def setActiveSelection(self, selection, replace=True):
        """
        Updates the active selection.

        :type selection: list
        :type replace: bool
        :rtype: None
        """

        pass

    def clearActiveSelection(self):
        """
        Clears the active selection.

        :rtype: None
        """

        pass
