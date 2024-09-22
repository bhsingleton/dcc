from maya import cmds as mc
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getPluginExtension():
    """
    Returns the plugin file extension based on the user's operating system.

    :rtype: str
    """

    # Check system type
    #
    if mc.about(windows=True) or mc.about(win64=True):

        return 'mll'

    elif mc.about(macOS=True) or mc.about(macOSx86=True):

        return 'bundle'

    elif mc.about(linux=True) or mc.about(linxx64=True):

        return 'so'

    else:

        raise RuntimeError('Unable to determine operating system!')


def tryLoadPlugin(plugin):
    """
    Tries to load a plugin with the specified name.

    :type plugin: str
    :rtype: bool
    """

    # Check if plugin has been loaded
    #
    extension = getPluginExtension()
    filename = '{plugin}.{extension}'.format(plugin=plugin, extension=extension)

    if mc.pluginInfo(filename, query=True, loaded=True):

        log.info(f'"{filename}" plugin has already been loaded.')
        return True

    # Try and load plugin
    #
    success = True

    try:

        log.info(f'Loading "{filename}" plugin...')
        mc.loadPlugin(filename)

    except RuntimeError as exception:

        success = False
        log.error(exception)

    finally:

        return success


def removeUnknownNodes(pluginName):
    """
    Removes any unknown nodes from the associated plugin.

    :type pluginName: str
    :rtype: None
    """

    # Collect all unknown nodes
    #
    nodeNames = mc.ls(type='unknown')

    if stringutils.isNullOrEmpty(nodeNames):

        return

    # Iterate through unknown nodes
    #
    for nodeName in nodeNames:

        associatedPlugin = mc.unknownNode(nodeName, query=True, plugin=True)

        if associatedPlugin == pluginName:

            log.info(f'Deleting unknown node: {nodeName}')
            mc.lockNode(nodeName, lock=False)
            mc.delete(nodeName)

        else:

            continue


def unloadPlugin(pluginName):
    """
    Unloads the specified plugin and removes any associated nodes.

    :type pluginName: str
    :rtype: bool
    """

    # Check if plugin is loaded
    #
    isLoaded = mc.pluginInfo(pluginName, query=True, loaded=True)

    if not isLoaded:

        log.debug(f'"{pluginName}" plugin has already been unloaded!')
        return

    # Remove all node types associated with plugin
    # This is another one of those commands that'll return None instead of an empty list!
    #
    nodeTypes = mc.pluginInfo(pluginName, query=True, dependNode=True)

    if not stringutils.isNullOrEmpty(nodeTypes):

        # Iterate through node types
        #
        for nodeType in nodeTypes:

            # List all nodes by type
            #
            nodeNames = mc.ls(type=nodeType)

            if stringutils.isNullOrEmpty(nodeNames):

                continue

            # Iterate through plugin nodes
            #
            for nodeName in nodeNames:

                # Check if node is referenced
                #
                isReferenced = mc.referenceQuery(nodeName, isNodeReferenced=True)

                if isReferenced:

                    log.warning(f'Unable to remove "{pluginName}" plugin with referenced nodes!')
                    return

                # Unlock and remove nodes
                #
                mc.lockNode(nodeName, lock=False)
                mc.delete(nodeName)

    # Flush undo queue
    # Otherwise this will prevent the plugin from unloading!
    #
    mc.flushUndo()

    # Try and unload plugin
    #
    success = True

    try:

        mc.unloadPlugin(pluginName)
        mc.pluginInfo(pluginName, edit=True, autoload=False)

    except RuntimeError as exception:

        log.warning(f'Unable to unload "{pluginName}" plugin!')
        log.error(exception)

        success = False

    finally:

        return success


def unloadTurtlePlugin():
    """
    Unloads the turtle plugin from the open scene file.

    :rtype: None
    """

    # Remove shelf from tab bar
    #
    if mc.shelfLayout('TURTLE', query=True, exists=True):

        log.info('Removing "TURTLE" from the shelf tab!')
        mc.deleteUI('TURTLE', layout=True)

    # Unload plugin
    #
    unloadPlugin('Turtle')


def unloadXGenPlugin():
    """
    Unloads the x-gen plugin from the open scene file.

    :rtype: None
    """

    # Remove shelf from tab bar
    #
    if mc.shelfLayout('XGen', query=True, exists=True):

        log.info('Removing "XGen" from the shelf tab!')
        mc.deleteUI('XGen', layout=True)

    # Unload plugin
    #
    unloadPlugin('xgenToolkit')
    unloadPlugin('xgSplineDataToXpd')


def unloadMASHPlugin():
    """
    Unloads the MASH plugin from the open scene file.

    :rtype: None
    """

    # Remove shelf from tab bar
    #
    if mc.shelfLayout('MASH', query=True, exists=True):

        log.info('Removing "MASH" from the shelf tab!')
        mc.deleteUI('MASH', layout=True)

    if mc.shelfLayout('MotionGraphics', query=True, exists=True):

        log.info('Removing "Motion Graphics" from the shelf tab!')
        mc.deleteUI('MotionGraphics', layout=True)

    # Unload plugin
    #
    unloadPlugin('MASH')
    unloadPlugin('LookdevXMaya')
    unloadPlugin('lookdevKit')


def unloadMentalRayPlugin():
    """
    Unloads the mental-ray plugin from the open scene file.
    If the plugin no longer exists then unknown nodes are removed.

    :rtype: None
    """

    # Check if mental-ray is loaded
    #
    pluginName = 'mayatomr'
    isRegistered = mc.pluginInfo(pluginName, query=True, registered=True)

    if isRegistered:

        unloadPlugin(pluginName)

    else:

        removeUnknownNodes(pluginName)
