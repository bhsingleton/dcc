import os
import stat
import json
import shutil
import subprocess

from P4 import P4Exception
from dcc import fnscene
from dcc.perforce import createAdapter, cmds

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

        raise TypeError('isNullOrEmpty() expects a sequence (%s given)!' % type(value).__name__)


def checkoutScene():
    """
    Checks out the open scene file from perforce.

    :rtype: None
    """

    # Check if scene exists
    #
    fnScene = fnscene.FnScene()
    filePath = fnScene.currentFilePath()

    if os.path.exists(filePath):

        return cmds.edit(filePath)

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


def renameFile(oldPath, newPath, changelist='default'):
    """
    Renames the old path to the new path and adds it to the specified changelist.

    :type oldPath: str
    :type newPath: str
    :type changelist: Union[str, int]
    :rtype: None
    """

    shutil.copy(oldPath, newPath)
    cmds.delete(oldPath, changelist=changelist)
    cmds.add(newPath, changelist=changelist)


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
