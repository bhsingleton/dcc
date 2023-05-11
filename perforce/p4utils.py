import os
import stat
import json
import shutil
import subprocess

from P4 import P4Exception
from dcc import fnscene
from dcc.perforce import createAdapter, cmds, clientutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


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


def acceptsCheckout(filePath):
    """
    Evaluates if the file can be checked out from P4.

    :type filePath: str
    :rtype: bool
    """

    # Check if path is in client view
    #
    client = clientutils.getCurrentClient()

    if not client.hasAbsoluteFile(filePath):

        return False

    # Evaluate file specs
    #
    depotPath = client.mapToDepot(filePath)
    specs = cmds.files(depotPath)

    return len(specs) == 1


def tryCheckout(filePath):
    """
    Attempts to checkout the supplied file from perforce.

    :type filePath: str
    :rtype: bool
    """

    accepted = acceptsCheckout(filePath)

    if accepted:

        cmds.edit(filePath)
        return True

    else:

        return False


def acceptsAdd(filePath):
    """
    Evaluates if the file can be added to P4.

    :type filePath: str
    :rtype: bool
    """

    # Check if path is in client view
    #
    client = clientutils.getCurrentClient()

    if not client.hasAbsoluteFile(filePath):

        return False

    # Evaluate file specs
    #
    depotPath = client.mapToDepot(filePath)
    specs = cmds.files(depotPath)

    return len(specs) == 0


def tryAdd(filePath):
    """
    Attempts to add the supplied file to perforce.

    :type filePath: str
    :rtype: bool
    """

    accepted = acceptsAdd(filePath)

    if accepted:

        cmds.add(filePath)
        return True

    else:

        return False


def checkoutScene():
    """
    Checks out the open scene file from perforce.

    :rtype: None
    """

    # Check if scene exists
    #
    scene = fnscene.FnScene()
    filePath = scene.currentFilePath()

    if os.path.exists(filePath):

        return tryCheckout(filePath)

    else:

        log.warning('Unable to checkout untitled scene file!')


def addScene():
    """
    Adds the open scene file to perforce.

    :rtype: None
    """

    # Check if scene exists
    #
    scene = fnscene.FnScene()
    filePath = scene.currentFilePath()

    if os.path.exists(filePath):

        return tryAdd(filePath)

    else:

        log.warning('Unable to checkout untitled scene file!')


def revertScene():
    """
    Reverts the open scene from perforce.

    :rtype: None
    """

    # Check if scene exists
    #
    fnScene = fnscene.FnScene()
    filePath = fnScene.currentFilePath()

    if os.path.exists(filePath):

        return cmds.revert([filePath])

    else:

        log.warning('Unable to revert untitled scene file!')


def showInExplorer():
    """
    Opens an explorer window to where the open scene file is located.

    :rtype: None
    """

    # Check if scene exists
    #
    fnScene = fnscene.FnScene()
    filePath = fnScene.currentFilePath()

    if os.path.exists(filePath):

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
    for (fromFile, toFile) in zip(fromFiles, toFiles):

        cmds.move(fromFile, toFile, changelist=changelist)


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
    
    filename = os.path.basename(fromFile)
    toFile = os.path.join(toDir, filename.replace(search, replace))

    cmds.move(fromFile, toFile, changelist=changelist)


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

    except P4Exception as exception:

        log.error(exception.message)
        return False
