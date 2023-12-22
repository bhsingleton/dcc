import os

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from dcc.abstract import afnnode

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
        variablePath = self.scene.makePathVariable(filePath, '$P4ROOT')

        if filePath != variablePath:

            self.setFilePath(variablePath)

    @abstractmethod
    def reload(self):
        """
        Reloads the displayed texture inside the viewport.

        :rtype: None
        """

        pass
