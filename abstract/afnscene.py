import os
import subprocess

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from six.moves import collections_abc
from dcc import fntexture
from dcc.python import pathutils, stringutils
from dcc.abstract import afnbase
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnScene(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase to outline function set behaviour for DCC scenes.
    """

    __slots__ = ()
    __extensions__ = None

    @classproperty
    def FileExtensions(cls):
        """
        Getter method that returns the file extension enumerators.

        :rtype: Type[IntEnum]
        """

        return cls.__extensions__

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
    def new(self):
        """
        Opens a new scene file.

        :rtype: None
        """

        pass

    @abstractmethod
    def save(self):
        """
        Saves any changes to the current scene file.

        :rtype: None
        """

        pass

    @abstractmethod
    def saveAs(self, filePath):
        """
        Saves the current scene to the specified path.

        :type filePath: str
        :rtype: None
        """

        pass

    @abstractmethod
    def open(self, filePath):
        """
        Opens the supplied scene file.

        :type filePath: str
        :rtype: bool
        """

        pass

    @abstractmethod
    def extensions(self):
        """
        Returns a list of scene file extensions.

        :rtype: Tuple[IntEnum]
        """

        pass

    def isValidExtension(self, path):
        """
        Evaluates if the supplied extension is supported.

        :type path: str
        :rtype: bool
        """

        # Get extension from path
        #
        extension = ''

        if os.path.isfile(path):

            directory, filename = os.path.split(path)
            name, extension = os.path.splitext(filename)

        else:

            extension = path

        # Compare extension with enumerators
        #
        extensions = [member.name.lower() for member in self.extensions()]
        extension = extension.lstrip('.').lower()

        return extension in extensions

    @abstractmethod
    def isBatchMode(self):
        """
        Evaluates if the scene is running in batch mode.

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

    def currentFileExtension(self):
        """
        Returns the extension of the open scene file.

        :rtype: FileExtensions
        """

        # Check if this is a new scene
        #
        if self.isNewScene():

            return None

        # Inspect file name
        #
        name, extension = os.path.splitext(self.currentFilename())
        return self.__extensions__[extension.lstrip('.')]

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

        return stringutils.isNullOrEmpty(value)

    @classmethod
    def getDriveLetters(cls):
        """
        Returns all the available drive letters.

        :rtype: List[str]
        """

        return pathutils.getDriveLetters()

    @classmethod
    def ensureDirectory(cls, path):
        """
        Ensures that the supplied directory exists.

        :type path: str
        :rtype: None
        """

        pathutils.ensureDirectory(path)

    @classmethod
    def isPathRelative(cls, path):
        """
        Evaluates if the supplied path is relative.

        :type path: str
        :rtype: bool
        """

        return pathutils.isPathRelative(path)

    @classmethod
    def isPathVariable(cls, path):
        """
        Evaluates if the supplied path contains an environment variable.

        :type path: str
        :rtype: bool
        """

        return pathutils.isPathVariable(path)

    @classmethod
    def isPathRelativeTo(cls, path, directory):
        """
        Evaluates if the supplied path is relative to the given directory.

        :type path: str
        :type directory: str
        :rtype: bool
        """

        return pathutils.isPathRelativeTo(path, directory)

    @classmethod
    def makePathRelativeTo(cls, path, directory):
        """
        Returns a path relative to the supplied directory.

        :type path: str
        :type directory: str
        :rtype: str
        """

        return pathutils.makePathRelativeTo(path, directory)

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
        :rtype: str
        """

        return pathutils.makePathAbsolute(path, paths=self.paths())

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
    def suspendViewport(self):
        """
        Pauses the current viewport from executing any redraws.

        :rtype: None
        """

        pass

    @abstractmethod
    def resumeViewport(self):
        """
        Un-pauses the current viewport to resume redraws.

        :rtype: None
        """

        pass

    @staticmethod
    def findFFmpeg():
        """
        Locates the FFmpeg installation from the user's machine.
        If FFmpeg cannot be found then an empty string is returned!
        If multiple installations are found then a TypeError will be raised!

        :rtype: str
        """

        paths = os.environ.get('PATH', '').split(';')

        found = [os.path.join(x, 'ffmpeg.exe') for x in paths if os.path.exists(os.path.join(x, 'ffmpeg.exe'))]
        numFound = len(found)

        if numFound == 0:

            return ''

        elif numFound == 1:

            return found[0]

        else:

            raise TypeError('findFFmpeg() multiple installations found: %s' % found)

    def hasFFmpeg(self):
        """
        Evaluates if the user has FFmpeg installed.

        :rtype: bool
        """

        return os.path.exists(self.findFFmpeg())

    @abstractmethod
    def playblast(self, filePath=None, startFrame=None, endFrame=None):
        """
        Creates a playblast using the supplied path.
        If no path is supplied then the default project path should be used instead!

        :type filePath: str
        :type startFrame: int
        :type endFrame: int
        :rtype: None
        """

        pass

    def transcodePlayblast(self, filePath):
        """
        Converts the supplied playblast to an MPEG w/H.264 encoding.

        :type filePath: str
        :rtype: None
        """

        # Check FFmpeg is installed
        #
        if not self.hasFFmpeg():

            log.warning('Unable to locate FFmpeg!')
            return

        # Concatenate save path
        #
        directory, filename = os.path.split(filePath)
        name, extension = os.path.splitext(filename)

        savePath = os.path.join(directory, '{name}.mp4'.format(name=name))

        # Execute shell command
        #
        command = '{ffmpeg} -y -i {input} -c:v libx264 -preset slow -crf 20 -c:a aac -b:a 160k -vf format=yuv420p -movflags +faststart {output}'.format(
            ffmpeg=self.findFFmpeg(),
            input=filePath,
            output=savePath
        )

        log.info('Transcoding playblast to: %s' % savePath)
        subprocess.call(command, shell=True)

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
    def execute(self, string, asPython=True):
        """
        Executes the supplied string.
        Be sure to specify if the string is in python or the native embedded language.

        :type string: str
        :type asPython: bool
        :rtype: None
        """

        pass

    def executeFile(self, filePath):
        """
        Executes the supplied script file.

        :rtype: None
        """

        # Check if file exists
        #
        if not os.path.exists(filePath):

            log.warning('Cannot locate file: %s' % filePath)
            return

        # Evaluate file extension
        #
        directory, filename = os.path.split(filePath)
        name, extension = os.path.splitext(filename)

        asPython = extension.endswith('py')

        # Execute file
        #
        with open(filePath, 'r') as file:

            self.execute(file.read(), asPython=asPython)

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
