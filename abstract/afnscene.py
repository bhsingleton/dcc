import os

from abc import ABCMeta, abstractmethod
from six import with_metaclass

from dcc.abstract import afnbase
from dcc.perforce import cmds, clientutils, searchutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnScene(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase to outline function set behaviour for DCC scenes.
    """

    __slots__ = ()

    @abstractmethod
    def isNewScene(self):
        """
        Evaluates whether this is an untitled scene file.

        :rtype: bool
        """

        pass

    @abstractmethod
    def isSaveRequired(self):
        """
        Evaluates whether the open scene file has changes that need to be saved.

        :rtype: bool
        """

        pass

    @abstractmethod
    def isBatchMode(self):
        """
        Evaluates if the the scene is running in batch mode.

        :rtype: bool
        """

        pass

    @abstractmethod
    def currentFilename(self):
        """
        Returns the name of the open scene file.

        :rtype: str
        """

        pass

    @abstractmethod
    def currentFilePath(self):
        """
        Returns the path of the open scene file.

        :rtype: str
        """

        pass

    @abstractmethod
    def currentDirectory(self):
        """
        Returns the directory of the open scene file.

        :rtype: str
        """

        pass

    @abstractmethod
    def currentProjectDirectory(self):
        """
        Returns the current project directory.

        :rtype: str
        """

        pass

    @abstractmethod
    def getStartTime(self):
        """
        Returns the current start time.

        :rtype: int
        """

        pass

    @abstractmethod
    def setStartTime(self, startTime):
        """
        Updates the start time.

        :type startTime: int
        :rtype: None
        """

        pass

    @abstractmethod
    def getEndTime(self):
        """
        Returns the current end time.

        :rtype: int
        """

        pass

    @abstractmethod
    def setEndTime(self, endTime):
        """
        Updates the end time.

        :type endTime: int
        :rtype: None
        """

        pass

    @abstractmethod
    def getTime(self):
        """
        Returns the current time.

        :rtype: int
        """

        pass

    @abstractmethod
    def setTime(self, time):
        """
        Updates the current time.

        :type time: int
        :rtype: None
        """

        pass

    @abstractmethod
    def enableAutoKey(self):
        """
        Enables the auto key mode.

        :rtype: None
        """

        pass

    @abstractmethod
    def disableAutoKey(self):
        """
        Disables the auto key mode.

        :rtype: None
        """

        pass

    @staticmethod
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

    @staticmethod
    def isRelative(path, directory):
        """
        Evaluates if the supplied path is relative to the given directory.
        This method ignores casing!

        :type path: str
        :type directory: str
        :rtype: bool
        """

        path = os.path.normpath(os.path.expandvars(path))
        directory = os.path.normpath(os.path.expandvars(directory))

        return path.lower().startswith(directory.lower())

    def expandPath(self, filePath):
        """
        Expands any file path that may contain an environment variable or relative syntax.

        :type filePath: str
        :rtype: str
        """

        # Check for empty strings
        #
        if self.isNullOrEmpty(filePath):

            return filePath

        # Evaluate any environment variables
        #
        filePath = os.path.normpath(os.path.expandvars(filePath))

        if os.path.isabs(filePath):

            return filePath

        else:

            return os.path.join(self.currentProjectDirectory(), filePath)

    def makePathsRelative(self, filePaths, directory):
        """
        Converts all of the texture paths to relative.
        If a path is not relative then no changes are made to the original path.

        :type filePaths: list[str]
        :type directory: str
        :rtype: list[str]
        """

        # Iterate through file paths
        #
        directory = os.path.normpath(os.path.expandvars(directory))

        numFilePaths = len(filePaths)
        relativePaths = [None] * numFilePaths

        for (i, filePath) in enumerate(filePaths):

            # Check if path is relative to directory
            #
            filePath = os.path.normpath(filePath)
            fullFilePath = self.expandPath(filePath)

            if self.isRelative(fullFilePath, directory):

                relativePath = os.path.relpath(fullFilePath, directory)

                log.info('%s > %s' % (filePath, relativePath))
                relativePaths[i] = relativePath

            else:

                log.warning('Cannot make: %s, relative to: %s' % (filePath, directory))
                relativePaths[i] = filePath

        return relativePaths

    def makePathsAbsolute(self, filePaths):
        """
        Converts all of the texture paths to absolute.

        :type filePaths: list[str]
        :rtype: list[str]
        """

        numFilePaths = len(filePaths)
        absolutePaths = [None] * numFilePaths

        for (i, filePath) in enumerate(filePaths):

            filePath = os.path.normpath(filePath)
            fullFilePath = self.expandPath(filePath)

            log.info('%s > %s' % (filePath, fullFilePath))
            absolutePaths[i] = fullFilePath

        return absolutePaths

    def makePathsDynamic(self, filePaths, variable):
        """
        Converts all of the texture paths to dynamic.
        The supplied variable name must contain a dollar sign!

        :type filePaths: list[str]
        :type variable: str
        :rtype: list[str]
        """

        # Iterate through file paths
        #
        directory = os.path.normpath(os.path.expandvars(variable))

        numFilePaths = len(filePaths)
        dynamicPaths = [None] * numFilePaths

        for (i, filePath) in enumerate(filePaths):

            # Check if path is relative to variable
            #
            filePath = os.path.normpath(filePath)
            fullFilePath = self.expandPath(filePath)

            if self.isRelative(fullFilePath, directory):

                dynamicPath = os.path.join(variable, os.path.relpath(fullFilePath, directory))

                log.info('%s > %s' % (filePath, dynamicPath))
                dynamicPaths[i] = dynamicPath

            else:

                dynamicPaths[i] = filePath

        return dynamicPaths

    @abstractmethod
    def iterTextures(self, absolute=False):
        """
        Returns a generator that yields all texture paths inside the scene.
        An optional keyword argument can be used to convert paths to absolute.

        :type absolute: bool
        :rtype: iter
        """

        pass

    def textures(self, absolute=False):
        """
        Returns a list of texture paths from the scene.
        An optional keyword argument can be used to convert paths to absolute.

        :type absolute: bool
        :rtype: list[str]
        """

        return list(self.iterTextures(absolute=absolute))

    def iterMissingTextures(self):
        """
        Returns a generator that yields all missing texture paths from the scene.

        :rtype: iter
        """

        # Iterate through textures
        #
        for texturePath in self.iterTextures():

            # Check if texture exists
            #
            if not os.path.exists(texturePath):

                yield texturePath

            else:

                continue

    def missingTextures(self):
        """
        Returns a list of missing texture paths from the scene.

        :rtype: list[str]
        """

        return list(self.iterMissingTextures())

    def findMissingTextures(self):
        """
        Attempts to locate all missing textures from the scene using perforce.
        If a texture cannot be found from the server then it is ignored!

        :rtype: None
        """

        # Iterate through missing textures
        #
        client = clientutils.getCurrentClient()

        oldPaths = self.missingTextures()
        newPaths = [None] * len(oldPaths)

        for (i, oldPath) in enumerate(oldPaths):

            # Concatenate search request
            #
            directory, filename = os.path.split(oldPath)
            search = '//{client}/.../{filename}'.format(client=client.name, filename=filename)

            # Process search request
            #
            log.info('Searching for: %s' % search)

            fileSpecs = searchutils.findFile(search)
            numFileSpecs = len(fileSpecs)

            if numFileSpecs == 0:

                log.warning('No results found for: %s' % oldPath)
                newPaths[i] = oldPaths[i]

            elif numFileSpecs == 1:

                newPath = client.mapToView(fileSpecs[0]['depotFile'])
                log.info('Located texture file @ %s' % newPath)

                newPaths[i] = newPath

            else:

                log.warning('Multiple results found for: %s' % oldPath)
                newPaths[i] = oldPaths[i]

        # Update texture paths
        #
        self.updateTextures(dict(zip(oldPaths, newPaths)))

    def syncTextures(self):
        """
        Syncs all of the textures inside the scene.
        If the texture is not relative to the client it is ignored.

        :rtype: None
        """

        # Collect all client files
        #
        client = clientutils.getCurrentClient()

        filePaths = [x for x in self.iterTextures(absolute=True) if client.hasAbsoluteFile(x)]
        numFilePaths = len(filePaths)

        if numFilePaths > 0:

            cmds.sync(*filePaths)

        # Reload textures
        #
        self.reloadTextures()

    def makeTexturesRelative(self):
        """
        Converts all of the textures to relative paths.

        :rtype: None
        """

        oldPaths = self.textures(absolute=True)
        newPaths = self.makePathsRelative(oldPaths, self.currentProjectDirectory())

        self.updateTextures(dict(zip(oldPaths, newPaths)))

    def makeTexturesAbsolute(self):
        """
        Converts all of the textures to absolute paths.

        :rtype: None
        """

        oldPaths = self.textures(absolute=True)
        newPaths = self.makePathsAbsolute(oldPaths)

        self.updateTextures(dict(zip(oldPaths, newPaths)))

    def makeTexturesDynamic(self):
        """
        Converts all of the textures to dynamic paths.

        :rtype: None
        """

        oldPaths = self.textures(absolute=True)
        newPaths = self.makePathsDynamic(oldPaths, '$P4ROOT')

        self.updateTextures(dict(zip(oldPaths, newPaths)))

    @abstractmethod
    def updateTextures(self, updates):
        """
        Applies all of the texture path updates to the associated file nodes.
        Each key-value pair should consist of the old and new texture paths!

        :type updates: dict[str:str]
        :rtype: None
        """

        pass

    @abstractmethod
    def reloadTextures(self):
        """
        Forces all of the texture nodes to reload.

        :rtype: None
        """

        pass

    @abstractmethod
    def iterFileProperties(self):
        """
        Returns a generator that yields file properties as key-value pairs.

        :rtype: iter
        """

        pass

    def fileProperties(self):
        """
        Returns a dictionary of file properties.

        :rtype: dict
        """

        return dict(self.iterFileProperties())

    @abstractmethod
    def getFileProperty(self, key, default=None):
        """
        Returns a file property value.
        An optional default value can be provided if no key is found.

        :type key: str
        :type default: Any
        :rtype: Any
        """

        pass

    @abstractmethod
    def setFileProperty(self, key, value):
        """
        Updates a file property value.
        If the item does not exist it will be automatically added.

        :type key: str
        :type value: str
        :rtype: None
        """

        pass

    def updateFileProperties(self, properties):
        """
        Updates the file properties using a dictionary.
        This method will not erase any pre-existing items but overwrite any duplicate keys.

        :type properties: dict
        :rtype: None
        """

        for (key, value) in properties.items():

            self.setFileProperty(key, value)

    @abstractmethod
    def getUpAxis(self):
        """
        Returns the up-axis that the scene is set to.

        :rtype: str
        """

        pass

    @abstractmethod
    def markDirty(self):
        """
        Marks the scene as dirty which will prompt the user for a save upon close.

        :rtype: None
        """

        pass

    @abstractmethod
    def markClean(self):
        """
        Marks the scene as clean which will not prompt the user for a save upon close.

        :rtype: None
        """

        pass
