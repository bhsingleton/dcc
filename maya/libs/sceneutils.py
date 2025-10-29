import os
import sys
import shlex

from maya import cmds as mc, mel as mel
from maya.api import OpenMaya as om
from collections import namedtuple
from itertools import chain
from . import dagutils
from ..decorators import undo
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


Reference = namedtuple('Reference', ('name', 'namespace', 'filePath', 'loaded'))
Requirement = namedtuple('Requirement', ('plugin', 'version', 'nodeType', 'dataType'))
Units = namedtuple('Units', ('linear', 'angle', 'time'))
FileHeader = namedtuple(
    'FileHeader',
    (
        'name',
        'version',
        'lastModified',
        'codeset',
        'references',
        'requirements',
        'units',
        'information'
    )
)


def getFileType(filePath):
    """
    Returns the Maya file type from the supplied path.

    :type filePath: str
    :rtype: str
    """

    return 'mayaAscii' if filePath.endswith('.ma') else 'mayaBinary' if filePath.endswith('.mb') else ''


def isNewScene():
    """
    Evaluates whether this is an untitled scene file.

    :rtype: bool
    """

    return len(mc.file(query=True, sceneName=True)) == 0


def newScene():
    """
    Creates a new scene file.

    :rtype: None
    """

    mc.file(newFile=True, force=True)


def isSaveRequired():
    """
    Evaluates whether the open scene file has changes that need to be saved.

    :rtype: bool
    """

    return mc.file(query=True, modified=True)


def saveScene():
    """
    Saves any changes made to the open scene file.

    :rtype: None
    """

    # Check if this is an open scene file
    #
    if isNewScene():

        return

    # Get current file type
    # Otherwise, Maya will assume binary for all files!
    #
    filename = currentFilename()
    fileType = getFileType(filename)

    # Save changes to scene file
    #
    mc.file(save=True, prompt=False, type=fileType)


def renameScene(filePath):
    """
    Changes the file path on the open scene file.

    :rtype: None
    """

    mc.file(rename=filePath)


def saveSceneAs(filePath):
    """
    Saves the open scene file in a difference location.

    :type filePath: str
    :rtype: None
    """

    renameScene(filePath)
    saveScene()


def isBatchMode():
    """
    Evaluates if the scene is running in batch mode.

    :rtype: bool
    """

    isBatching = mc.about(query=True, batch=True)
    isStandalone = sys.executable.lower().endswith('mayapy.exe')

    return isBatching or isStandalone


def currentFilePath():
    """
    Returns the path of the open scene file.

    :rtype: str
    """

    if not isNewScene():

        return os.path.normpath(mc.file(query=True, sceneName=True))

    else:

        return ''


def currentFilename(includeName=True, includeExtension=True):
    """
    Returns the name of the open scene file.

    :type includeName: bool
    :type includeExtension: bool
    :rtype: str
    """

    # Check which part should be returned
    #
    directory, fileName = os.path.split(currentFilePath())
    name, extension = os.path.splitext(fileName)

    if includeName and includeExtension:

        return fileName

    elif includeName:

        return name

    elif includeExtension:

        return extension.lstrip('.')

    else:

        return ''


def currentExtension():
    """
    Returns the extension of the open scene file.

    :rtype: str
    """

    directory, fileName = os.path.split(currentFilePath())
    return os.path.splitext(fileName)[1].lstrip('.')


def currentDirectory():
    """
    Convenience method used to retrieve the directory of the open scene file.

    :rtype: str
    """

    return os.path.split(currentFilePath())[0]


def openScene(filePath):
    """
    Opens the supplied scene file.

    :rtype: bool
    """

    try:

        mc.file(filePath, open=True, prompt=False, force=True)
        return True

    except RuntimeError as exception:

        log.error(exception)
        return False


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


def currentNamespace():
    """
    Returns the current namespace.
    Unlike the `namespaceInfo` command, this method will return an empty string for the root namespace!

    :rtype: str
    """

    namespace = mc.namespaceInfo(currentNamespace=True)

    if namespace == ':':

        return ''

    else:

        return namespace


def iterFileProperties():
    """
    Returns a generator that yields file properties as key-value pairs.

    :rtype: iter
    """

    properties = mc.fileInfo(query=True)
    numProperties = len(properties)

    for i in range(0, numProperties, 2):

        yield properties[i], properties[i + 1].encode('ascii').decode('unicode-escape')


def isDirty():
    """
    Evaluates if the scene is dirty.

    :rtype: bool
    """

    return mc.file(query=True, modified=True)


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


def getAnimationRange(selected=False):
    """
    Returns the current start and end time.

    :type selected: bool
    :rtype: Tuple[int, int]
    """

    # Check if selection is required
    #
    if not selected:

        return getStartTime(), getEndTime()

    # Evaluate active selection
    # By default, `timeControl` will return the current time if nothing is selected!
    #
    timeSlider = mel.eval('$tmpVar=$gPlayBackSlider')
    startTime, endTime = mc.timeControl(timeSlider, query=True, rangeArray=True)

    difference = endTime - startTime

    if difference != 1.0:

        return startTime, endTime

    else:

        return getStartTime(), getEndTime()


def setAnimationRange(startTime, endTime):
    """
    Updates the current start and end time.

    :type startTime: int
    :type endTime: int
    :rtype: None
    """

    setStartTime(startTime)
    setEndTime(endTime)


def getTime():
    """
    Returns the current time.

    :rtype: int
    """

    return int(mc.currentTime(query=True))


@undo.Undo(state=False)
def setTime(time):
    """
    Updates the current time.

    :type time: int
    :rtype: None
    """

    mc.currentTime(time, edit=True)


def autoKey():
    """
    Returns the auto-key state.

    :rtype: bool
    """

    return mc.autoKeyframe(query=True, state=True)


@undo.Undo(state=False)
def setAutoKey(state):
    """
    Updates the auto-key state.

    :type state: bool
    :rtype: None
    """

    mc.autoKeyframe(state=state)


def enableAutoKey():
    """
    Enables the auto key mode.

    :rtype: None
    """

    setAutoKey(True)


def disableAutoKey():
    """
    Disables the auto key mode.

    :rtype: None
    """

    setAutoKey(False)


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


def refreshTextures():
    """
    Refreshes any texture changes in the active scene.

    :rtype: None
    """

    mc.ogs(reloadTextures=True)


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


def getCurrentCamera():
    """
    Returns the current camera with focus.

    :rtype: str
    """

    currentPanel = mc.getPanel(withFocus=True)
    camera = mc.modelPanel(currentPanel, query=True, camera=True)

    return camera


def resetStartupCameras():
    """
    Fixes the startup cameras when they're thrown out of wack.

    :rtype: None
    """

    mc.viewSet('top', home=True)
    mc.viewSet('front', home=True)
    mc.viewSet('side', home=True)


def frameVisible(all=False):
    """
    Frames the camera around the current scene contents.

    :type all: bool
    :rtype: None
    """

    cameras = mc.ls(type='camera') if all else [getCurrentCamera()]
    nodes = [dagutils.getMDagPath(shape).fullPathName() for shape in chain(*[list(dagutils.iterShapes(node, apiType=om.MFn.kGeometric)) for node in dagutils.iterVisibleNodes()])]

    for camera in cameras:

        mc.viewFit(camera, *nodes)


def getMayaVersion():
    """
    Returns the current Maya version.

    :rtype: int
    """

    return mc.about(version=True)


def decomposeFlags(args):
    """
    Returns an organized collection of flags.

    :type args: List[str]
    :rtype: dict[str, str]
    """

    # Evaluate flag positions
    #
    occurrences = [i for (i, arg) in enumerate(args) if arg.startswith('-')]
    numOccurrences = len(occurrences)

    flags = {}

    if numOccurrences == 0:

        return flags

    # Group flags together
    #
    occurrences.append(len(args))

    for (startIndex, endIndex) in zip(occurrences[:-1], occurrences[1:]):

        flag = args[startIndex]
        numArgs = (endIndex - startIndex) - 1

        if numArgs == 0:

            flags[flag] = True

        elif numArgs == 1:

            flags[flag] = args[startIndex + 1]

        else:

            flags[flag] = args[(startIndex + 1):endIndex]

    return flags


def getFileHeader(filePath):
    """
    Returns the file header from the supplied Maya ascii file.

    :type filePath: str
    :rtype: Union[FileHeader, None]
    """

    # Evaluate file type
    #
    fullFilePath = os.path.expandvars(filePath)

    isFile = os.path.isfile(fullFilePath)
    isMayaAscii = fullFilePath.endswith('.ma')

    if not (isFile and isMayaAscii):

        log.warning(f'Unable to read file header from: {fullFilePath}')
        return None

    # Perform a shallow read of the Maya file
    #
    name, version, lastModified, codeset = '', '', '', ''
    references = []
    requirements = []
    units = None
    information = {}

    with open(fullFilePath, 'r') as asciiFile:

        line = ''
        commandline = ''

        while True:

            # Check for empty string
            #
            line = asciiFile.readline().strip(stringutils.__escape_chars__)
            numChars = len(line)

            if numChars == 0:

                break

            # Check if this is a comment
            #
            if line.startswith('//'):

                comment = line.lstrip('//')

                if comment.startswith('Maya'):

                    version = comment

                elif comment.startswith('Name:'):

                    name = comment.replace('Name: ', '')

                elif comment.startswith('Last modified:'):

                    lastModified = comment.replace('Last modified: ', '')

                elif comment.startswith('Codeset:'):

                    codeset = comment.replace('Codeset: ', '')

                else:

                    pass

                continue

            # Concatenate command-line
            #
            commandline = line

            while not commandline.endswith(';'):

                line = asciiFile.readline().strip(stringutils.__escape_chars__)
                commandline += f' {line}'

            # Evaluate command
            #
            command, *args = shlex.split(commandline.rstrip(';'))

            if command == 'file':

                *args, filePath = args
                flags = decomposeFlags(args)
                containsPreferences = flags.get('-rdi', False)

                if not containsPreferences:

                    continue

                reference = Reference(flags['-rfn'], flags['-ns'], filePath, not flags.get('-dr', False))
                references.append(reference)

            elif command == 'requires':

                *args, pluginName, pluginVersion = args
                flags = decomposeFlags(args)

                requirement = Requirement(pluginName, pluginVersion, flags.get('-nodeType', None), flags.get('-dataType', None))
                requirements.append(requirement)

            elif command == 'currentUnit':

                flags = decomposeFlags(args)
                units = Units(flags.get('-l', None), flags.get('-a', None), flags.get('-t', None))

            elif command == 'fileInfo':

                information[args[0]] = args[1]

            else:

                break

    return FileHeader(name, version, lastModified, codeset, references, requirements, units, information)


def getFileReferences(filePath):
    """
    Returns the references from the supplied file path.
    This method only works on ascii based Maya files!

    :type filePath: str
    :rtype: dict[str, bool]
    """

    header = getFileHeader(filePath)
    references = {}

    for reference in header.references:

        references[reference.name] = reference.loaded

    return references
