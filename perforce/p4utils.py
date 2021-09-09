import os
import subprocess

from PySide2 import QtWidgets

from . import cmds, clientutils, searchengine
from .. import fnscene, fnqt

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


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


def isNullOrEmpty(value):
    """
    Evaluates whether the supplied value is null of empty.

    :type value: Union[str, list]
    :rtype: bool
    """

    # Check value type
    #
    if hasattr(value, '__len__'):

        # Check number of characters
        #
        if len(value) == 0:

            return True

        else:

            return False

    elif value is None:

        return True

    else:

        raise TypeError('Unable to evaluate "%s" type!' % type(value).__name__)


def resolveAbsolutePath(filePath):
    """
    Convenience method used to resolve a file path against the user's current client view.

    :type filePath: str
    :rtype: str
    """

    # Split file into path and name
    #
    filePath = os.path.normpath(filePath)
    dirPath, filename = os.path.split(filePath)

    # List files under client view
    #
    client = os.environ['P4CLIENT']
    clientSpec = clientutils.getClientByName(client)

    fileSpecs = searchengine.findFile(
        '//{client}/.../{filename}'.format(
            client=client,
            filename=filename
        )
    )

    if isNullOrEmpty(fileSpecs):

        log.warning('Unable to locate: "%s", from "%s" client view!' % (filename, client))
        return filePath

    # Check if any files were found
    #
    numFound = len(fileSpecs)

    if numFound == 1:

        localPath = clientSpec.mapToView(fileSpecs[0]['depotFile'])
        return clientSpec.mapToRoot(localPath)

    else:

        # Prompt user
        #
        fnQt = fnqt.FnQt()
        parent = fnQt.getMainWindow()

        depotPath, response = QtWidgets.QInputDialog.getItem(
            parent,
            'Select Depot File',
            'Depot File:',
            [x['depotFile'] for x in fileSpecs],
            editable=False
        )

        if response:

            localPath = clientSpec.mapToView(depotPath)
            return clientSpec.mapToRoot(localPath)

        else:

            return filePath
