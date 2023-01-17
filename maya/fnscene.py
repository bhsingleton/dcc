import os

from enum import IntEnum
from maya import cmds as mc
from maya.api import OpenMaya as om
from .libs import dagutils, sceneutils
from ..abstract import afnscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FileExtensions(IntEnum):
    """
    Overload of IntEnum that contains the file extensions for Maya.
    """

    mb = 0
    ma = 1


class FnScene(afnscene.AFnScene):
    """
    Overload of AFnBase used to interface with Maya scenes.
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

        mc.file(newFile=True, force=True)

    def save(self):
        """
        Saves any changes to the current scene file.

        :rtype: None
        """

        # Check if this is an open scene file
        #
        if self.isNewScene():

            return

        # Get current file type
        # Otherwise, Maya will assume binary for all files!
        #
        extension = self.currentFileExtension()
        fileType = 'mayaAscii' if extension == FileExtensions.ma else 'mayaBinary'

        # Save changes to scene file
        #
        mc.file(save=True, prompt=False, type=fileType)

    def saveAs(self, filePath):
        """
        Saves the current scene to the specified path.

        :type filePath: str
        :rtype: None
        """

        mc.file(rename=filePath)
        self.save()

    def open(self, filePath):
        """
        Opens the supplied scene file.

        :type filePath: str
        :rtype: bool
        """

        try:

            mc.file(filePath, open=True, prompt=False, force=True)
            return True

        except RuntimeError as exception:

            log.error(exception)
            return False

    def extensions(self):
        """
        Returns a list of scene file extensions.

        :rtype: Tuple[FileExtensions]
        """

        return FileExtensions.mb, FileExtensions.ma

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

        return sceneutils.currentProjectDirectory()

    def getStartTime(self):
        """
        Returns the current start time.

        :rtype: int
        """

        return sceneutils.getStartTime()

    def setStartTime(self, startTime):
        """
        Updates the start time.

        :type startTime: int
        :rtype: None
        """

        sceneutils.setStartTime(startTime)

    def getEndTime(self):
        """
        Returns the current end time.

        :rtype: int
        """

        return sceneutils.getEndTime()

    def setEndTime(self, endTime):
        """
        Updates the end time.

        :type endTime: int
        :rtype: None
        """

        sceneutils.setEndTime(endTime)

    def getTime(self):
        """
        Returns the current time.

        :rtype: int
        """

        return sceneutils.getTime()

    def setTime(self, time):
        """
        Updates the current time.

        :type time: int
        :rtype: None
        """

        sceneutils.setTime(time)

    def enableAutoKey(self):
        """
        Enables the auto key mode.

        :rtype: None
        """

        sceneutils.enableAutoKey()

    def disableAutoKey(self):
        """
        Disables the auto key mode.

        :rtype: None
        """

        sceneutils.disableAutoKey()

    def suspendViewport(self):
        """
        Pauses the current viewport from executing any redraws.

        :rtype: None
        """

        sceneutils.suspendViewport()

    def resumeViewport(self):
        """
        Un-pauses the current viewport to resume redraws.

        :rtype: None
        """

        sceneutils.resumeViewport()

    def playblast(self, filePath=None, startFrame=None, endFrame=None):
        """
        Creates a playblast using the supplied path.
        If no path is supplied then the default project path should be used instead!

        :type filePath: str
        :type startFrame: int
        :type endFrame: int
        :rtype: None
        """

        pass

    def iterFileProperties(self):
        """
        Returns a generator that yields file properties as key-value pairs.

        :rtype: iter
        """

        return sceneutils.iterFileProperties()

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

        return sceneutils.currentUpAxis()

    def markDirty(self):
        """
        Marks the scene as dirty which will prompt the user for a save upon close.

        :rtype: None
        """

        sceneutils.markDirty()

    def markClean(self):
        """
        Marks the scene as clean which will not prompt the user for a save upon close.

        :rtype: None
        """

        sceneutils.markClean()

    def execute(self, string, asPython=True):
        """
        Executes the supplied string.
        Be sure to specify if the string is in python or the native embedded language.

        :type string: str
        :type asPython: bool
        :rtype: None
        """

        if asPython:

            exec(string)

        else:

            mc.eval(string)

    def iterNodes(self):
        """
        Returns a generator that yields all nodes from the scene.

        :rtype: iter
        """

        return dagutils.iterNodes(apiType=om.MFn.kDagNode)

    def getActiveSelection(self):
        """
        Returns the active selection.

        :rtype: List[om.MObject]
        """

        selection = om.MGlobal.getActiveSelectionList()  # type: om.MSelectionList
        selectionCount = selection.length()

        return [selection.getDependNode(i) for i in range(selectionCount)]

    def setActiveSelection(self, selection, replace=True):
        """
        Updates the active selection.

        :type selection: List[om.MObject]
        :type replace: bool
        :rtype: None
        """

        # Check if selection should be replaced
        #
        if not replace:

            selection.extend(self.getActiveSelection())

        # Update selection global
        #
        selectionList = dagutils.createSelectionList(selection)
        om.MGlobal.setActiveSelectionList(selectionList)

    def clearActiveSelection(self):
        """
        Clears the active selection.

        :rtype: None
        """

        om.MGlobal.clearSelectionList()

    def iterActiveComponentSelection(self):
        """
        Returns a generator that yields all selected components

        :rtype: iter
        """

        # Access the Maya global selection list
        #
        selection = om.MGlobal.getActiveSelectionList()
        numSelected = selection.length()

        if numSelected == 0:

            return

        # Iterate through selection
        #
        iterSelection = om.MItSelectionList(selection, om.MFn.kComponent)

        while not iterSelection.isDone():

            # Check if items are valid
            #
            dagPath, component = iterSelection.getComponent()

            if dagPath.isValid() and not component.isNull():

                yield dagPath, component

            # Go to next selection
            #
            iterSelection.next()

