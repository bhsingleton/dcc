import os

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from dcc.abstract import afnnode
from dcc.perforce import cmds, clientutils, searchutils
from dcc.perforce.decorators.relogin import relogin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnTexture(with_metaclass(ABCMeta, afnnode.AFnNode)):
    """
    Overload of AFnNode that outlines texture interfaces.
    """

    __slots__ = ()

    @abstractmethod
    def filePath(self):
        """
        Returns the file path for this texture.

        :rtype: str
        """

        pass

    @abstractmethod
    def setFilePath(self, filePath):
        """
        Updates the file path for this texture.

        :type filePath: str
        :rtype: None
        """

        pass

    def exists(self):
        """
        Evaluates if this texture exists.

        :rtype: bool
        """

        return os.path.exists(self.fullFilePath())

    def fullFilePath(self):
        """
        Returns the full file path for this texture.

        :rtype: str
        """

        return self.scene.makePathAbsolute(self.filePath())

    def isRelative(self):
        """
        Evaluates if this texture uses a relative path.

        :rtype: bool
        """

        return self.scene.isPathRelative(self.filePath())

    def isAbsolute(self):
        """
        Evaluates if this texture uses an absolute path.

        :rtype: bool
        """

        return os.path.isabs(self.filePath())

    def isVariable(self):
        """
        Evaluates if this texture uses environment variables.

        :rtype: bool
        """

        return self.scene.isPathVariable(self.filePath())

    def makeRelative(self):
        """
        Converts this texture path to relative.

        :rtype: None
        """

        filePath = self.filePath()
        relativePath = self.scene.makePathRelative(filePath)

        if filePath != relativePath:

            self.setFilePath(relativePath)

    def makeAbsolute(self):
        """
        Converts this texture path to absolute.

        :rtype: None
        """

        filePath = self.filePath()
        absolutePath = self.scene.makePathAbsolute(filePath)

        if filePath != absolutePath:

            self.setFilePath(absolutePath)

    def makeVariable(self):
        """
        Converts this texture path to variable.

        :rtype: None
        """

        filePath = self.filePath()
        variablePath = self.scene.makePathVariable(filePath, 'P4ROOT')

        if filePath != variablePath:

            self.setFilePath(variablePath)

    @relogin
    def findDepotPath(self):
        """
        Returns the depot path for this texture from perforce.

        :rtype: str
        """

        # Check for empty string
        #
        filePath = self.filePath()

        if self.scene.isNullOrEmpty(filePath):

            return ''

        # Search for file in client view
        #
        client = clientutils.getCurrentClient()

        found = searchutils.findFile(filePath, client=client)
        numFound = len(found)

        if numFound == 0:

            return ''

        elif numFound == 1:

            return found[0]['depotFile']

        else:

            log.warning('Multiple depot files found for: %s' % filePath)
            return ''

    def fix(self):
        """
        Fixes the texture path by searching perforce.

        :rtype: bool
        """

        # Find associated depot file
        #
        filePath = self.filePath()
        depotPath = self.findDepotPath()

        if self.scene.isNullOrEmpty(depotPath):

            log.warning('Unable to fix file path: %s' % filePath)
            return False

        # Get file stats
        #
        stats = cmds.fstat(depotPath)
        numStats = len(stats)

        if numStats == 0:

            log.warning('Unable to locate file stats: %s' % filePath)
            return False

        # Check if file needs syncing
        #
        stat = stats[0]
        haveRev = stat.get('haveRev', 0)  # P4 omits `haveRev` if the file has not been synced!

        if haveRev != stat['headRev']:

            cmds.sync(depotPath)

        # Convert to local path
        #
        client = clientutils.getCurrentClient()

        localPath = client.mapToView(depotPath)
        absolutePath = self.scene.makePathAbsolute(filePath)  # This will resolve once the file has been synced

        if localPath != absolutePath:

            log.info('Fixing %s, to %s' % (filePath, localPath))
            self.setFilePath(localPath)

        return True

    @relogin
    def getLatest(self):
        """
        Pulls the latest texture from perforce.

        :rtype: None
        """

        # Check if file exists in client view
        #
        fullFilePath = self.fullFilePath()
        client = clientutils.getCurrentClient()

        if not client.hasAbsoluteFile(fullFilePath):

            log.warning('Unable to locate: %s, from perforce!' % fullFilePath)
            return

        # Check if file needs syncing
        #
        depotPath = client.mapToDepot(fullFilePath)

        stats = cmds.fstat(depotPath)
        numStats = len(stats)

        if numStats == 0:

            log.warning('Unable to locate file stats: %s, from perforce!' % depotPath)
            return

        # Check if file is up to date
        #
        stat = stats[0]
        haveRev = stat.get('haveRev', 0)  # P4 omits `haveRev` if the file has not been synced!

        if haveRev != stat['headRev']:

            cmds.sync(depotPath)

        else:

            log.info('File is already up to date: %s' % depotPath)

    @abstractmethod
    def reload(self):
        """
        Reloads the displayed texture inside the viewport.

        :rtype: None
        """

        pass
