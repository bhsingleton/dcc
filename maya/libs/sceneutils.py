import maya.cmds as mc
import os

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isNewScene():
    """
    Evaluates whether this is an untitled scene file.

    :rtype: bool
    """

    return len(mc.file(query=True, sceneName=True)) == 0


def isSaveRequired():
    """
    Evaluates whether the open scene file has changes that need to be saved.

    :rtype: bool
    """

    return mc.file(query=True, modified=True)


def isBatchMode():
    """
    Evaluates if the scene is running in batch mode.

    :rtype: bool
    """

    return mc.about(query=True, batch=True)


def currentFilePath():
    """
    Returns the path of the open scene file.

    :rtype: str
    """

    if not isNewScene():

        return os.path.normpath(mc.file(query=True, sceneName=True))

    else:

        return ''


def currentFilename():
    """
    Returns the name of the open scene file.

    :rtype: str
    """

    return os.path.split(currentFilePath())[-1]


def currentDirectory():
    """
    Convenience method used to retrieve the directory of the open scene file.

    :rtype: str
    """

    return os.path.split(currentFilePath())[0]


def currentProjectDirectory():
    """
    Returns the current project directory.

    :rtype: str
    """

    return os.path.normpath(mc.workspace(query=True, directory=True))


def currentUpAxis():
    """
    Returns the up-axis that the scene is set to.

    :rtype: str
    """

    return mc.upAxis(query=True, axis=True)


def currentUnits():
    """
    Returns the current scene units.

    :rtype: Dict[str, str]
    """

    return {
        'linear': mc.currentUnit(query=True, linear=True),
        'angle': mc.currentUnit(query=True, angle=True),
        'time': mc.currentUnit(query=True, time=True)
    }


def iterFileProperties():
    """
    Returns a generator that yields file properties as key-value pairs.

    :rtype: iter
    """

    properties = mc.fileInfo(query=True)
    numProperties = len(properties)

    for i in range(0, numProperties, 2):

        yield properties[i], properties[i + 1].encode('ascii').decode('unicode-escape')


def markDirty():
    """
    Marks the scene as dirty which will prompt the user for a save upon close.

    :rtype: None
    """

    mc.file(modified=True)


def markClean():
    """
    Marks the scene as clean which will not prompt the user for a save upon close.

    :rtype: None
    """

    mc.file(modified=False)


def getStartTime():
    """
    Returns the current start time.

    :rtype: int
    """

    return int(mc.playbackOptions(query=True, min=True))


def setStartTime(startTime):
    """
    Updates the start time.

    :type startTime: int
    :rtype: None
    """

    mc.playbackOptions(edit=True, min=startTime)


def getEndTime():
    """
    Returns the current end time.

    :rtype: int
    """

    return int(mc.playbackOptions(query=True, max=True))


def setEndTime(endTime):
    """
    Updates the end time.

    :type endTime: int
    :rtype: None
    """

    mc.playbackOptions(edit=True, max=endTime)


def getAnimationRange():
    """
    Returns the current start and end time.

    :rtype: Tuple[int, int]
    """

    return getStartTime(), getEndTime()


def getTime():
    """
    Returns the current time.

    :rtype: int
    """

    return int(mc.currentTime(query=True))


def setTime(time):
    """
    Updates the current time.

    :type time: int
    :rtype: None
    """

    mc.currentTime(time, edit=True)


def enableAutoKey():
    """
    Enables the auto key mode.

    :rtype: None
    """

    mc.autoKeyframe(state=True)


def disableAutoKey():
    """
    Disables the auto key mode.

    :rtype: None
    """

    mc.autoKeyframe(state=False)


def suspendViewport():
    """
    Pauses the current viewport from executing any redraws.

    :rtype: None
    """

    if not mc.ogs(query=True, pause=True):

        mc.ogs(pause=True)


def resumeViewport():
    """
    Un-pauses the current viewport to resume redraws.

    :rtype: None
    """

    if mc.ogs(query=True, pause=True):

        mc.ogs(pause=True)


def removeUserAttributes():
    """
    Removes all user attributes from the selected nodes.
    Useful for any garbage created by the FBX importer.

    :rtype: None
    """

    # Iterate through selection
    #
    nodeNames = mc.ls(sl=True)

    for nodeName in nodeNames:

        # Check if node has any user attributes
        #
        attrNames = mc.listAttr(nodeName, userDefined=True)

        if attrNames is None:

            continue

        for attrName in attrNames:

            log.info('Removing "%s.%s" attribute.' % (nodeName, attrName))
            mc.deleteAttr('%s.%s' % (nodeName, attrName))


def removeUnknownNodes():
    """
    Removes any unknown nodes from the scene file.

    :rtype: None
    """

    nodeNames = mc.ls(type='unknown')

    if nodeNames is not None:

        log.info('Deleting unknown nodes: %s' % nodeNames)
        mc.delete(nodeNames)


def unloadPlugin(pluginName):
    """
    Unloads the specified plugin and removes any associated nodes.

    :type pluginName: str
    :rtype: None
    """

    # Check if turtle is loaded
    #
    isLoaded = mc.pluginInfo(pluginName, query=True, loaded=True)

    if not isLoaded:

        log.info('Could not locate "%s" plugin.')
        return

    # Remove all node types associated with plugin
    #
    nodeTypes = mc.pluginInfo(pluginName, query=True, dependNode=True)

    for nodeType in nodeTypes:

        # List all nodes by type
        #
        nodeNames = mc.ls(type=nodeType)
        numNodeNames = len(nodeNames)

        if numNodeNames == 0:

            continue

        # Unlock and remove nodes
        #
        mc.lockNode(nodeNames, lock=False)
        mc.delete(nodeNames)

    # Flush undo queue
    # Otherwise this will prevent the plugin from unloading!
    #
    mc.flushUndo()

    # Unlock plugin
    #
    mc.unloadPlugin(pluginName)


def unloadTurtlePlugin():
    """
    Unloads the turtle plugin from the open scene file.

    :rtype: None
    """

    # Unload turtle plugin
    #
    unloadPlugin('Turtle')

    # Remove shelf from tab bar
    #
    if mc.shelfLayout('TURTLE', query=True, exists=True):

        log.info('Removing "TURTLE" from the shelf tab!')
        mc.deleteUI('TURTLE', layout=True)


def unloadMentalRayPlugin():
    """
    Unloads the mental-ray plugin from the open scene file.
    If the plugin no longer exists then unknown nodes are removed.

    :rtype: None
    """

    # Check if mental-ray is loaded
    #
    pluginName = 'mayatomr'
    isLoaded = mc.pluginInfo(pluginName, query=True, loaded=True)

    if isLoaded:

        unloadPlugin(pluginName)

    else:

        removeUnknownNodes()


def resetWindowPositions():
    """
    Resets all child windows to the top left corner.

    :rtype: None
    """

    # Collect all windows
    #
    windowNames = mc.lsUI(windows=True)

    for windowName in windowNames:

        log.info('Resetting "%s" window...' % windowName)
        mc.window(windowName, edit=True, topLeftCorner=[0, 0])


def resetStartupCameras():
    """
    Fixes the startup cameras when they're thrown out of wack.

    :rtype: None
    """

    mc.viewSet('top', home=True)
    mc.viewSet('front', home=True)
    mc.viewSet('side', home=True)
