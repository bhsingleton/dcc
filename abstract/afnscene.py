import os
import win32api

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from fnmatch import fnmatch
from dcc import fntexture
from dcc.abstract import afnbase

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

    def paths(self):
        """
        Returns a list of content paths.

        :rtype: List[str]
        """

        return [self.currentProjectDirectory()]

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

    def getDriveLetters(self):
        """
        Returns all the available drive letters.

        :rtype: List[str]
        """

        return win32api.GetLogicalDriveStrings().split('\000')[:-1]

    @classmethod
    def isPathRelative(cls, path):
        """
        Evaluates if the supplied path is relative.

        :type path: str
        :rtype: bool
        """

        segments = os.path.normpath(path).split(os.path.sep)
        numSegments = len(segments)

        if numSegments == 0:

            return False

        else:

            return not fnmatch(segments[0], '?:')

    @classmethod
    def isPathVariable(cls, path):
        """
        Evaluates if the supplied path contains an environment variable.

        :type path: str
        :rtype: bool
        """

        return path.startswith(('%', '$'))

    @classmethod
    def isPathRelativeTo(cls, path, directory):
        """
        Evaluates if the supplied path is relative to the given directory.

        :type path: str
        :type directory: str
        :rtype: bool
        """

        # Check for empty strings
        #
        if cls.isNullOrEmpty(path) or cls.isNullOrEmpty(directory):

            return ''

        # Normalize and compare paths
        #
        path = os.path.normpath(os.path.expandvars(path))
        directory = os.path.normpath(os.path.expandvars(directory))

        return os.path.normcase(path).startswith(os.path.normcase(directory))

    @classmethod
    def makePathRelativeTo(cls, path, directory):
        """
        Returns a path relative to the supplied directory.

        :type path: str
        :type directory: str
        :rtype: str
        """

        # Check for empty strings
        #
        if cls.isNullOrEmpty(path) or cls.isNullOrEmpty(directory):

            return ''

        # Check if path is relative to directory
        #
        path = os.path.normpath(path)

        if cls.isPathRelativeTo(path, directory):

            relativePath = os.path.relpath(path, directory)
            log.info('%s > %s' % (path, relativePath))

            return relativePath

        else:

            log.warning('Cannot make: %s, relative to: %s' % (path, directory))
            return path

    def makePathRelative(self, path):
        """
        Returns a path relative to the current project directory.

        :type path: str
        :rtype: str
        """

        # Iterate through paths
        #
        for directory in self.paths():

            # Check if path is relative
            #
            if self.isPathRelativeTo(path, directory):

                return self.makePathRelativeTo(path, directory)

            else:

                continue

        # Notify user
        #
        log.warning('Unable to make path relative: %s' % path)
        return path

    def makePathAbsolute(self, path):
        """
        Converts all the texture paths to absolute.

        :type path: str
        :rtype: List[str]
        """

        # Check for empty strings
        #
        if self.isNullOrEmpty(path):

            return ''

        # Inspect path type
        #
        path = os.path.normpath(os.path.expandvars(path))

        if os.path.isabs(path):

            return path

        # Iterate through paths
        #
        for directory in self.paths():

            # Check if combined path is valid
            #
            absolutePath = os.path.join(directory, path)

            if os.path.exists(absolutePath):

                return absolutePath

            else:

                continue

        # Notify user
        #
        log.warning('Unable to make path absolute: %s' % path)
        return path

    def makePathVariable(self, path, variable):
        """
        Converts all the texture paths to variable.
        The supplied variable name must contain a dollar sign!

        :type path: str
        :type variable: str
        :rtype: str
        """

        # Check for empty strings
        #
        if self.isNullOrEmpty(path) or self.isNullOrEmpty(variable):

            return ''

        # Check if path is relative to variable
        #
        absolutePath = self.makePathAbsolute(path)
        directory = os.path.expandvars(variable)

        if self.isPathRelativeTo(absolutePath, directory):

            variablePath = os.path.join(variable, os.path.relpath(absolutePath, directory))
            log.debug('%s > %s' % (absolutePath, variablePath))

            return variablePath

        else:

            log.warning('Unable to make path variable: %s' % path)
            return path

    def makeTexturesRelative(self):
        """
        Converts all the texture paths to relative.

        :rtype: None
        """

        fnTexture = fntexture.FnTexture()
        fnTexture.setQueue(fnTexture.instances())

        while not fnTexture.isDone():

            fnTexture.next()
            fnTexture.makeRelative()

    def makeTexturesAbsolute(self):
        """
        Converts all the texture paths to absolute.

        :rtype: None
        """

        fnTexture = fntexture.FnTexture()
        fnTexture.setQueue(fnTexture.instances())

        while not fnTexture.isDone():

            fnTexture.next()
            fnTexture.makeAbsolute()

    def findMissingTextures(self):
        """
        Locates all the missing textures using perforce.

        :rtype: None
        """

        fnTexture = fntexture.FnTexture()
        fnTexture.setQueue(fnTexture.instances())

        while not fnTexture.isDone():

            fnTexture.next()
            fnTexture.fix()

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

    def getFileProperty(self, key, default=None):
        """
        Returns a file property value.
        An optional default value can be provided if no key is found.

        :type key: str
        :type default: Any
        :rtype: Any
        """

        return self.fileProperties().get(key, default)

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

    def setFileProperties(self, properties):
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

    @abstractmethod
    def iterNodes(self):
        """
        Returns a generator that yields all nodes from the scene.

        :rtype: iter
        """

        pass

    @abstractmethod
    def getActiveSelection(self):
        """
        Returns the active selection.

        :rtype: list
        """

        pass

    @abstractmethod
    def setActiveSelection(self, selection, replace=True):
        """
        Updates the active selection.

        :type selection: list
        :type replace: bool
        :rtype: None
        """

        pass

    @abstractmethod
    def clearActiveSelection(self):
        """
        Clears the active selection.

        :rtype: None
        """

        pass
