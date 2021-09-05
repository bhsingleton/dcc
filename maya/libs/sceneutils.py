import maya.cmds as mc
import os

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isNewScene():
    """
    Method used to check if this is an untitled scene file.

    :rtype: bool
    """

    return len(mc.file(query=True, sceneName=True)) == 0


def isSaveRequired():
    """
    Method used to check if the open scene file has changes that need to be saved.

    :rtype: bool
    """

    return mc.file(query=True, modified=True)


def currentFilePath():
    """
    Convenience method used to retrieve the path of the open scene file.

    :rtype: str
    """

    if not isNewScene():

        return os.path.normpath(mc.file(query=True, sceneName=True))

    else:

        return ''


def currentFilename():
    """
    Convenience method used to retrieve the name of the open scene file.

    :rtype: str
    """

    return os.path.split(currentFilePath())[1]


def currentDirectory():
    """
    Convenience method used to retrieve the directory of the open scene file.

    :rtype: str
    """

    return os.path.split(currentFilePath())[0]


def removeUserAttributes():
    """
    Convenience method used to removed any user attributes that have carried over using fbx.

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


def unloadTurtlePlugin():
    """
    Convenience method used to unload the turtle plugin from the open scene file.

    :rtype: None
    """

    # Check if turtle is loaded
    #
    isLoaded = mc.pluginInfo('Turtle', query=True, loaded=True)

    if not isLoaded:

        log.info('Could not locate "Turtle" in the open scene file.')
        return

    # Remove all node types associated with turtle
    #
    nodeTypes = mc.pluginInfo('Turtle', query=True, dependNode=True)

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
    #
    mc.flushUndo()

    # Remove shelf from tab bar
    #
    if mc.shelfLayout('TURTLE', query=True, exists=True):

        log.info('Removing "TURTLE" from the shelf tab!')
        mc.deleteUI('TURTLE', layout=True)

    # Unlock plugin
    #
    mc.unloadPlugin('Turtle')


def resetWindowPositions():
    """
    Method used to move all of the active maya windows to the top left corner.

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
    Method used to fix the startup cameras when they're thrown out of wack.

    :rtype: None
    """

    mc.viewSet('top', home=True)
    mc.viewSet('front', home=True)
    mc.viewSet('side', home=True)
