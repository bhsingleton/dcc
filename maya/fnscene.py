import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.abstract import afnscene
from dcc.maya.libs import dagutils

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

    def isBatchMode(self):
        """
        Evaluates if the scene is running in batch mode.

        :rtype: bool
        """

        return mc.about(query=True, batch=True)

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

        properties = mc.fileInfo(query=True)
        numProperties = len(properties)

        for i in range(0, numProperties, 2):

            yield properties[i], properties[i + 1].encode('ascii').decode('unicode-escape')

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

        :type selection: list
        :type replace: bool
        :rtype: None
        """

        # Check if selection should be replaced
        #
        if not replace:

            selection.extend(self.getActiveSelection())

        # Update selection global
        #
        om.MGlobal.setActiveSelectionList(selection)

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

