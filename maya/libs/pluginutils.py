import os
import urllib

from maya import cmds as mc, mel
from . import shelfutils
from ...python import stringutils, pathutils

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


def iterPluginPaths():
    """
    Returns a generator that yields absolute plugin paths.

    :rtype: Iterator[str]
    """

    # Iterate through path substrings
    #
    paths = os.getenv('MAYA_PLUG_IN_PATH').split(';')

    for path in paths:

        # Check if path is valid
        #
        if stringutils.isNullOrEmpty(path):

            continue

        # Get absolute path and check if path exists
        #
        absPath = os.path.abspath(path)

        if os.path.isdir(absPath):

            yield absPath

        else:

            continue


def pathToPlugin(plugin):
    """
    Returns the absolute path to the specified plugin.

    :type plugin: str
    :rtype: Union[str, None]
    """

    # Check if plugin contains file extension
    #
    extension = getPluginExtension()

    if not plugin.endswith(extension):

        plugin += f'.{extension}'

    # Redundancy check
    #
    isFileLike = pathutils.isFileLike(plugin)

    if isFileLike:

        return plugin

    else:

        # Iterate through plugin paths
        #
        for path in iterPluginPaths():

            filePath = os.path.join(path, plugin)

            if os.path.isfile(filePath):

                return filePath

            else:

                continue

        return None


def doesPluginExist(plugin):
    """
    Evaluates if the supplied plugin exists.

    :type plugin: str
    :rtype: bool
    """

    filePath = pathToPlugin(plugin)

    if not stringutils.isNullOrEmpty(filePath):

        return os.path.isfile(filePath)

    else:

        return False


def ensurePluginPath(path):
    """
    Ensures the supplied path exists within the Maya plug-in paths.

    :type path: str
    :rtype: bool
    """

    # Check if supplied path is valid
    #
    directories = list(iterPluginPaths())
    absPath = os.path.abspath(path)

    isDirectory = os.path.isdir(absPath)

    if not isDirectory:

        return False

    # Check if path is missing
    #
    isMissing = absPath not in directories

    if isMissing:

        path = os.getenv('MAYA_PLUG_IN_PATH')
        altPath = absPath.replace(os.sep, os.altsep)

        if path.endswith(';'):

            os.environ['MAYA_PLUG_IN_PATH'] = f'{path}{altPath}'

        else:

            os.environ['MAYA_PLUG_IN_PATH'] = f'{path};{altPath}'

    return True


def downloadPlugin(url, filePath):
    """
    Downloads a plugin to the specified location.

    :type url: str
    :type filePath: str
    :rtype: bool
    """

    # Ensure directory exists
    #
    pathutils.ensureDirectory(filePath)

    # Try and download plugin
    #
    log.info(f'Downloading plugin from: {url}')
    downloadPath, headers = urllib.request.urlretrieve(url, filePath)

    success = os.path.isfile(downloadPath)

    if success:

        log.info(f'Plug-in downloaded to: {downloadPath}')
        return True

    else:

        log.warning(f'Unable to download plug-in to: {downloadPath}')
        return False


def tryLoadPlugin(plugin):
    """
    Tries to load a plugin with the specified name.

    :type plugin: str
    :rtype: bool
    """

    # Derive filename from plugin
    #
    extension = getPluginExtension()
    filename = str(plugin)

    if not filename.endswith(extension):

        filename = '{plugin}.{extension}'.format(plugin=plugin, extension=extension)

    # Check if plugin has already been loaded
    #
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

        # Check if node still exists
        #
        exists = mc.objExists(nodeName)

        if not exists:

            continue

        # Check if node is associated with requested plugin
        #
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

    # Try and remove shelf from tab bar
    #
    success = shelfutils.deleteShelfTab('TURTLE', silent=True)

    if not success:

        return

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
    success = shelfutils.deleteShelfTab('XGen', silent=True)

    if not success:

        return

    # Unload plugin
    #
    unloadPlugin('xgenToolkit')
    unloadPlugin('xgSplineDataToXpd')


def unloadMASHPlugin():
    """
    Unloads the MASH plugin from the open scene file.

    :rtype: None
    """

    # Remove mash from tab bar
    #
    success = shelfutils.deleteShelfTab('MASH', silent=True)

    if success:

        unloadPlugin('MASH')

    # Remove motion graphics from tab bar
    #
    success = shelfutils.deleteShelfTab('MotionGraphics', silent=True)

    if success:

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


def unloadArnoldPlugin():
    """
    Unloads the arnold plugin from the open scene file.
    If the plugin no longer exists then unknown nodes are removed.

    :rtype: None
    """

    # Check if arnold is loaded
    #
    pluginName = 'mtoa'
    isRegistered = mc.pluginInfo(pluginName, query=True, registered=True)

    if isRegistered:

        unloadPlugin(pluginName)

    else:

        removeUnknownNodes(pluginName)
