from ..fbx.libs import FbxFileVersion
from ..abstract import afnfbx

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnFbx(afnfbx.AFnFbx):
    """
    Overload of `AFnFbx` that implements the FBX interface for Blender.
    """

    __slots__ = ()

    def setMeshExportParams(self, **kwargs):
        """
        Adopts the export settings from the supplied kwargs.

        :rtype: None
        """

        pass

    def setAnimExportParams(self, **kwargs):
        """
        Adopts the animation settings from the supplied kwargs.

        :rtype: None
        """

        pass

    def exportSelection(self, filePath):
        """
        Exports the active selection to the specified file path.

        :type filePath: str
        :rtype: bool
        """

        return False
