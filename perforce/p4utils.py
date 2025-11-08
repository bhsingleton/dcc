import os
import re
import stat
import json
import subprocess

from . import createAdapter, cmds, clientutils, searchutils
from .decorators import relogin
from .. import fnscene, fntexture
from ..python import importutils

P4 = importutils.tryImport('P4', __locals__=locals(), __globals__=globals())

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__file_regex__ = re.compile(r'(?:[\/]){2}(?:[a-zA-Z0-9_\-]+[\\\/])*([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)')


def isInstalled():
    """
    Evaluates if `p4python` is installed.

    :rtype: bool
    """

    return P4 is not None


def isNullOrEmpty(value):
    """
    Evaluates if the supplied value is null or empty.

    :type value: Any
    :rtype: bool
    """

    if hasattr(value, '__len__'):

        return len(value) == 0

    elif value is None:

        return True

    else:

        return False


def isDepotPath(string):
    """
    Evaluates if the supplied string represents a depot path.
    No validation is done to test whether the file exists or not!

    :rtype: bool
    """

    return __file_regex__.match(string) is not None


def isUpToDate(path):
    """
    Evaluates if the requested file is up to date.

    :type path: str
    :rtype: bool
    """

    # Get depot path to file
    #
    depotPath = guessDepotPath(path)

    if isNullOrEmpty(depotPath):

        return False

    # Check if file exists
    #
    exists = doesFileExist(depotPath)

    if not exists:

        return False

    # Compare have revision to head revision
    #
    fileStat = cmds.fstat(depotPath)[0]
    haveRev = int(fileStat['haveRev'])
    headRev = int(fileStat['headRev'])

    return haveRev == headRev


def acceptsCheckout(path):
    """
    Evaluates if the file can be checked out from P4.
    This function accepts either an absolute path or a depot path!

    :type path: str
    :rtype: bool
    """

    # Check if path is valid
    #
    if isNullOrEmpty(path):

        return False

    # Check if this is a depot path
    #
    if isDepotPath(path):

        return doesFileExist(path)

    else:

        # Check if path is in client view
        #
        client = clientutils.getCurrentClient()

        if client.hasAbsoluteFile(path):

            depotPath = client.mapToDepot(path)
            return doesFileExist(depotPath)

        else:

            return False


def tryFlush(filePath):
    """
    Attempts to sync to the latest revision without overwriting any local changes.

    :type filePath: str
    :rtype: bool
    """

    # Check if file can be checked out
    #
    accepted = acceptsCheckout(filePath)

    if not accepted:

        return False

    # Check if file requires syncing
    #
    stats = cmds.fstat(filePath)[0]

    haveRev = stats.get('haveRev', 0)
    headRev = stats['headRev']

    if haveRev != headRev:

        log.debug(f'File is out-of-date: {filePath}')
        cmds.sync(filePath, flush=True)

    else:

        log.debug(f'File is already up-to-date: {filePath}')

    return True


def tryCheckout(filePath):
    """
    Attempts to checkout the supplied file from perforce.

    :type filePath: str
    :rtype: bool
    """

    # Check if file can be checked out
    #
    accepted = acceptsCheckout(filePath)

    if accepted:

        tryFlush(filePath)
        cmds.edit(filePath)

        return True

    else:

        return False


def doesFileExist(path):
    """
    Evaluates if the supplied file exists on the server.
    This function accepts either an absolute path or a depot path!

    :type path: str
    :rtype: bool
    """

    # Check if path is valid
    #
    if isNullOrEmpty(path):

        return False

    # Check if this is a depot path
    #
    if isDepotPath(path):

        specs = cmds.files(path, quiet=True)
        exists = len(specs) == 1

        return exists

    else:

        # Check if path is in client view
        #
        depotPath = guessDepotPath(path)

        if not isNullOrEmpty(depotPath):

            return doesFileExist(depotPath)

        else:

            return False


def acceptsAdd(path):
    """
    Evaluates if the file can be added to P4.
    This function accepts either an absolute path or a depot path!

    :type path: str
    :rtype: bool
    """

    # Check if path is valid
    #
    if isNullOrEmpty(path):

        return False

    # Check if this is a depot path
    #
    if isDepotPath(path):

        return not doesFileExist(path)

    else:

        # Check if path is in client view
        #
        client = clientutils.getCurrentClient()

        if client.hasAbsoluteFile(path):

            depotPath = client.mapToDepot(path)
            return acceptsAdd(depotPath)

        else:

            return False


def tryAdd(filePath):
    """
    Attempts to add the supplied file to perforce.

    :type filePath: str
    :rtype: bool
    """

    # Check if file can be added
    #
    accepted = acceptsAdd(filePath)

    if accepted:

        cmds.add(filePath)
        return True

    else:

        return False


def smartCheckout(filePath):
    """
    Automatically detects whether the supplied file needs to be added or checked out.

    :type filePath: str
    :rtype: bool
    """

    if acceptsAdd(filePath):

        return tryAdd(filePath)

    elif acceptsCheckout(filePath):

        return tryCheckout(filePath)

    else:

        return False


def trySync(path):
    """
    Attempts to sync the supplied file from perforce.

    :type path: str
    :rtype: bool
    """

    exists = doesFileExist(path)

    if exists:

        cmds.sync(path)
        return True

    else:

        return False


@relogin.Relogin()
def checkoutScene():
    """
    Checks out the open scene file from perforce.

    :rtype: bool
    """

    # Check if scene exists
    #
    scene = fnscene.FnScene()
    filePath = scene.currentFilePath()

    if os.path.isfile(filePath):

        return tryCheckout(filePath)

    else:

        log.warning('Unable to checkout untitled scene file!')
        return False


@relogin.Relogin()
def addScene():
    """
    Adds the open scene file to perforce.

    :rtype: None
    """

    # Check if scene exists
    #
    scene = fnscene.FnScene()
    filePath = scene.currentFilePath()

    if os.path.isfile(filePath):

        return tryAdd(filePath)

    else:

        log.warning('Unable to checkout untitled scene file!')


@relogin.Relogin()
def revertScene():
    """
    Reverts the open scene from perforce.

    :rtype: bool
    """

    # Check if scene exists
    #
    fnScene = fnscene.FnScene()
    filePath = fnScene.currentFilePath()

    if os.path.isfile(filePath):

        return cmds.revert([filePath])

    else:

        log.warning('Unable to revert untitled scene file!')
        return False


def showInExplorer():
    """
    Opens an explorer window to where the open scene file is located.

    :rtype: None
    """

    # Check if scene exists
    #
    fnScene = fnscene.FnScene()
    filePath = fnScene.currentFilePath()

    if os.path.isfile(filePath):

        subprocess.Popen(r'explorer /select, "{filePath}"'.format(filePath=filePath))

    else:

        log.warning('Unable to show untitled scene file in explorer!')


def makeSceneWritable():
    """
    Removes the `readOnly` flag from the scene file.

    :rtype: None
    """

    # Check if scene exists
    #
    fnScene = fnscene.FnScene()
    filePath = fnScene.currentFilePath()

    if os.path.exists(filePath):

        os.chmod(filePath, stat.S_IWRITE)

    else:

        log.warning('Unable to make scene file writable!')


def makeSceneReadOnly():
    """
    Adds the `readOnly` flag to the scene file.

    :rtype: None
    """

    # Check if scene exists
    #
    fnScene = fnscene.FnScene()
    filePath = fnScene.currentFilePath()

    if os.path.exists(filePath):

        os.chmod(filePath, stat.S_IREAD|stat.S_IRGRP|stat.S_IROTH)

    else:

        log.warning('Unable to make scene file writable!')


def moveDirectory(fromDir, toDir, search='', replace='', changelist='default'):
    """
    Moves the files from the specified directory to the new location.

    :type fromDir: str
    :type toDir: str
    :type search: str
    :type replace: str
    :type changelist: Union[str, int]
    :rtype: None
    """

    # Collect files in directory to move
    #
    filenames = [filename for filename in os.listdir(fromDir) if os.path.isfile(os.path.join(fromDir, filename))]

    fromFiles = [os.path.join(fromDir, filename) for filename in filenames]
    toFiles = [os.path.join(toDir, filename.replace(search, replace)) for filename in filenames]

    # Iterate through files
    #
    clientSpec = clientutils.getCurrentClient()

    for (fromFile, toFile) in zip(fromFiles, toFiles):

        # Remap local paths
        #
        fromDepotFile = clientSpec.mapToDepot(fromFile)
        toDepotFile = clientSpec.mapToDepot(toFile)

        # Move depot file
        #
        log.info(f'Moving file: {fromDepotFile} > {toDepotFile}')
        cmds.move(fromDepotFile, toDepotFile, changelist=changelist)


def moveFile(fromFile, toDir, search='', replace='', changelist='default'):
    """
    Moves the supplied file to the new location.

    :type fromFile: str
    :type toDir: str
    :type search: str
    :type replace: str
    :type changelist: Union[str, int]
    :rtype: None
    """

    # Remap local paths
    #
    filename = os.path.basename(fromFile)
    toFile = os.path.join(toDir, filename.replace(search, replace))

    clientSpec = clientutils.getCurrentClient()
    fromDepotFile = clientSpec.mapToDepot(fromFile)
    toDepotFile = clientSpec.mapToDepot(toFile)

    # Move depot file
    #
    log.info(f'Moving file: {fromDepotFile} > {toDepotFile}')
    cmds.move(fromDepotFile, toDepotFile, changelist=changelist)


def saveChangelist(changelist, filePath, **kwargs):
    """
    Outputs the specified changelist to the designated file path.
    Each file data object consists of the following: ['rev', 'time', 'action', 'type', 'depotFile', 'change']
    Optional keywords can be supplied to override the p4 adapter.

    :type changelist: int
    :type filePath: str
    :rtype: bool
    """

    # Try and connect to server
    #
    try:

        # Write changelist to file
        #
        p4 = createAdapter(**kwargs)

        with open(filePath, 'w') as jsonFile:

            files = p4.run('files', '@={changelist}'.format(changelist=changelist))
            json.dump(files, jsonFile, indent=4)

        # Disconnect from server
        #
        p4.disconnect()
        return True

    except P4.P4Exception as exception:

        log.error(exception.message)
        return False


def getFilesFromChangelist(changelist, editsOnly=False, **kwargs):
    """
    Returns a list of depot files from the supplied changelist.

    :type changelist: int
    :type editsOnly: bool
    :rtype: List[str]
    """

    p4 = createAdapter()
    specs = []

    try:

        p4.connect()
        specs = p4.run('files', f'@={changelist}')

    except P4.P4Exception:

        cmds.logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()

        if editsOnly:

            return [spec['depotFile'] for spec in specs if spec['action'] == 'edit']

        else:

            return [spec['depotFile'] for spec in specs]


def guessDepotPath(path):
    """
    Returns a potential depot path for the supplied path from perforce.
    No error checking is performed to test if the depot path exists!

    :type path: str
    :rtype: str
    """

    # Redundancy check
    #
    if isDepotPath(path):

        return path

    # Check if path is relative to client
    #
    client = clientutils.getCurrentClient()

    if client.hasAbsoluteFile(path):

        return client.mapToDepot(path)

    else:

        return ''


@relogin.Relogin()
def findDepotPath(filePath, client=None):
    """
    Returns the depot path for the supplied path from perforce.

    :type filePath: str
    :type client: Union[ClientSpec, None]
    :rtype: str
    """

    # Check if path is valid
    #
    if isNullOrEmpty(filePath):

        return ''

    # Check if a client was supplied
    #
    if client is None:

        client = clientutils.getCurrentClient()

    # Search for file in client view
    #
    found = searchutils.findFile(filePath, client=client)
    numFound = len(found)

    if numFound == 0:

        return ''

    elif numFound == 1:

        return found[0]['depotFile']

    else:

        log.warning(f'Multiple depot files found for: {filePath}')
        return ''


@relogin.Relogin()
def fixBrokenTextures():
    """
    Fixes any broken textures using perforce.

    :rtype: bool
    """

    # Iterate through texture nodes
    #
    scene = fnscene.FnScene()

    texture = fntexture.FnTexture()
    texture.setQueue(texture.instances())

    while not texture.isDone():

        # Find associated depot file
        #
        filePath = texture.filePath()
        depotPath = findDepotPath(filePath)

        if isNullOrEmpty(depotPath):

            log.warning(f'Unable to fix file path: {filePath}')
            texture.next()

            continue

        # Get file stats
        #
        stats = cmds.fstat(depotPath)
        numStats = len(stats)

        if numStats == 0:

            log.warning(f'Unable to locate file stats: {filePath}')
            texture.next()

            continue

        # Check if file needs syncing
        #
        fileStat = stats[0]
        haveRev = fileStat.get('haveRev', 0)  # P4 omits `haveRev` if the file has not been synced!

        if haveRev != fileStat['headRev']:

            cmds.sync(depotPath)

        # Convert to local path
        #
        client = clientutils.getCurrentClient()

        localPath = client.mapToView(depotPath)
        absolutePath = scene.makePathAbsolute(filePath)  # This will resolve once the file has been synced

        if localPath != absolutePath:

            log.info(f'Fixing {filePath} to {localPath}')
            texture.setFilePath(localPath)

        # Go to next item
        #
        texture.next()

    # Refresh viewport
    #
    scene.refreshTextures()


@relogin.Relogin()
def syncMissingTextures():
    """
    Syncs any missing textures from perforce.

    :rtype: None
    """

    # Iterate through texture nodes
    #
    texture = fntexture.FnTexture()
    texture.setQueue(texture.instances())

    while not texture.isDone():

        # Check if file exists in client view
        #
        fullFilePath = texture.fullFilePath()
        client = clientutils.getCurrentClient()

        if not client.hasAbsoluteFile(fullFilePath):

            log.warning(f'Unable to locate: {fullFilePath}, from perforce!')
            texture.next()

            continue

        # Check if file needs syncing
        #
        depotPath = client.mapToDepot(fullFilePath)

        stats = cmds.fstat(depotPath)
        numStats = len(stats)

        if numStats == 0:

            log.warning(f'Unable to locate file stats: {depotPath}, from perforce!')
            texture.next()

            continue

        # Check if file is up-to-date
        #
        fileStat = stats[0]
        haveRev = fileStat.get('haveRev', 0)  # P4 omits `haveRev` if the file has not been synced!

        if haveRev != fileStat['headRev']:

            cmds.sync(depotPath)

        else:

            log.info(f'File is already up to date: {depotPath}')

        # Go to next item
        #
        texture.next()
