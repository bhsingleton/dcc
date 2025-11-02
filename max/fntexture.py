import pymxs

from . import fnnode
from ..abstract import afntexture

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnTexture(fnnode.FnNode, afntexture.AFnTexture):
    """
    Overload of `AFnTexture` that implements the texture interface for 3ds-Max.
    """

    __slots__ = ()

    def filePath(self):
        """
        Returns the file path for this texture.

        :rtype: str
        """

        return self.object().filename

    def setFilePath(self, filePath):
        """
        Updates the file path for this texture.

        :type filePath: str
        :rtype: None
        """

        self.object().filename = filePath

    def reload(self):
        """
        Reloads the displayed texture inside the viewport.

        :rtype: None
        """

        self.object().reload()

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields texture instances.

        :rtype: iter
        """

        return iter(pymxs.runtime.getClassInstances(pymxs.runtime.BitmapTexture))
