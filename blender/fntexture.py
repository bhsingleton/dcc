from . import fnnode
from ..abstract import afntexture

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnTexture(fnnode.FnNode, afntexture.AFnTexture):
    """
    Overload of `AFnTexture` that implements the texture interface for Blender.
    """

    __slots__ = ()

    def filePath(self):
        """
        Returns the file path for this texture.

        :rtype: str
        """

        return ''

    def setFilePath(self, filePath):
        """
        Updates the file path for this texture.

        :type filePath: str
        :rtype: None
        """

        pass

    def reload(self):
        """
        Reloads the displayed texture inside the viewport.

        :rtype: None
        """

        pass

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields texture instances.

        :rtype: iter
        """

        return iter([])
