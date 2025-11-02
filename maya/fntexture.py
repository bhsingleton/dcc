from maya import cmds as mc
from maya.api import OpenMaya as om
from . import fnnode
from ..abstract import afntexture

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnTexture(fnnode.FnNode, afntexture.AFnTexture):
    """
    Overload of `AFnTexture` that implements the texture interface for Maya.
    """

    __slots__ = ()

    def filePath(self):
        """
        Returns the file path for this texture.

        :rtype: str
        """

        return self.getAttr('fileTextureName')

    def setFilePath(self, filePath):
        """
        Updates the file path for this texture.

        :type filePath: str
        :rtype: None
        """

        self.setAttr('fileTextureName', filePath)

    def reload(self):
        """
        Reloads the displayed texture inside the viewport.

        :rtype: None
        """

        mc.dgdirty('%s.fileTextureName' % self.absoluteName())

    @classmethod
    def iterInstances(cls, apiType=om.MFn.kFileTexture):
        """
        Returns a generator that yields texture instances.

        :rtype: iter
        """

        return super(FnTexture, cls).iterInstances(apiType=apiType)
