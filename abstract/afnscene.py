import os
import subprocess

from abc import ABCMeta, abstractmethod
from . import afnbase
from .. import fnnode, fntexture
from ..python import stringutils, pathutils, importutils, ffmpegutils
from ..decorators.classproperty import classproperty
from ..vendor.six import with_metaclass
from ..vendor.six.moves import collections_abc

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

    def isReadOnly(self):
        """
        Evaluates whether the open scene file is read-only.

        :rtype: bool
        """

        if not self.isNewScene():

            return pathutils.isReadOnly(self.currentFilePath())

        else:

            return False

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

    def currentName(self):
        """
        Returns the name of the open scene file without extension.

        :rtype: str
        """

        if not self.isNewScene():

            return os.path.splitext(self.currentFilename())[0]

        else:

            return ''

    @abstractmethod
    def currentFilename(self):
        """
        Returns the name of the open scene file with extension.

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
    def ensureWritable(cls, path):
        """
        Ensures that the supplied file is writable.

        :type path: str
        :rtype: None
        """

        pathutils.ensureWritable(path)

    @classmethod
    def isPathAbsolute(cls, path):
        """
        Evaluates if the supplied path is absolute.

        :type path: str
        :rtype: bool
        """

        return os.path.isabs(path)

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
    def makePathRelativeTo(cls, path, directory, force=False):
        """
        Returns a path relative to the supplied directory.

        :type path: str
        :type directory: str
        :type force: bool
        :rtype: str
        """

        return pathutils.makePathRelativeTo(path, directory, force=force)

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

            fnTexture.makeRelative()
            fnTexture.next()

    def makeTexturesAbsolute(self):
        """
        Converts all the texture paths to absolute.

        :rtype: None
        """

        texture = fntexture.FnTexture()
        texture.setQueue(texture.instances())

        while not texture.isDone():

            texture.makeAbsolute()
            texture.next()

    def makeTexturesVariable(self):
        """
        Converts all the texture paths to variable.

        :rtype: None
        """

        texture = fntexture.FnTexture()
        texture.setQueue(texture.instances())

        while not texture.isDone():

            texture.makeVariable()
            texture.next()

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

    @abstractmethod
    def refreshTextures(self):
        """
        Refreshes any texture changes in the active scene.

        :rtype: None
        """

        pass

    @staticmethod
    def findFFmpeg():
        """
        Locates the FFmpeg installation from the user's machine.
        If FFmpeg cannot be found then an empty string is returned!

        :rtype: str
        """

        return ffmpegutils.findFFmpeg()

    def hasFFmpeg(self):
        """
        Evaluates if the user has FFmpeg installed.

        :rtype: bool
        """

        return ffmpegutils.hasFFmpeg()

    @abstractmethod
    def playblast(self, filePath=None, startFrame=None, endFrame=None, autoplay=True):
        """
        Creates a playblast using the supplied path.
        If no path is supplied then the default project path should be used instead!

        :type filePath: str
        :type startFrame: int
        :type endFrame: int
        :type autoplay: bool
        :rtype: None
        """

        pass

    def transcodePlayblast(self, filePath, delete=True):
        """
        Converts the supplied playblast to an MPEG w/H.264 encoding.

        :type filePath: str
        :type delete: bool
        :rtype: str
        """

        # Check FFmpeg is installed
        #
        if not self.hasFFmpeg():

            log.warning('Unable to locate FFmpeg!')
            return filePath

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

        # Check if source file should be deleted
        #
        if delete:

            os.remove(filePath)

        return savePath

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

        :type key: str
        :type value: str
        :rtype: None
        """

        pass

    @abstractmethod
    def deleteFileProperty(self, key):
        """
        Removes a file property value.

        :type key: str
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
    def execute(self, string):
        """
        Executes the supplied string using the embedded language.

        :type string: str
        :rtype: bool
        """

        pass

    def executePython(self, string):
        """
        Executes the supplied string using python.

        :type string: str
        :rtype: bool
        """

        try:

            exec(string, globals())
            return True

        except Exception as exception:

            log.warning(exception)
            return False

    def executeFile(self, filePath):
        """
        Executes the supplied script file.

        :type filePath: str
        :rtype: bool
        """

        # Check if file exists
        #
        if not os.path.exists(filePath):

            log.warning('Cannot locate file: %s' % filePath)
            return False

        # Evaluate file extension
        #
        directory, filename = os.path.split(filePath)
        name, extension = os.path.splitext(filename)

        asPython = extension.endswith('py')

        # Execute file
        #
        if asPython:

            return importutils.executeFile(filePath)

        else:

            script = ''

            with open(filePath, 'r') as file:

                script = file.read()

            return self.execute(script)

    @abstractmethod
    def iterNodes(self):
        """
        Returns a generator that yields all nodes from the scene.

        :rtype: iter
        """

        pass

    def doesNodeExist(self, name):
        """
        Evaluates whether a node exists with the given name.

        :type name: str
        :rtype: bool
        """

        return fnnode.FnNode.doesNodeExist(name)

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
