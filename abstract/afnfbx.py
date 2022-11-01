from abc import ABCMeta, abstractmethod
from six import with_metaclass

from dcc.abstract import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnFbx(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC fbx operations.
    """

    __slots__ = ()

    @abstractmethod
    def setMeshExportParams(self, **kwargs):
        """
        Adopts the export settings from the supplied kwargs.

        :rtype: None
        """

        pass

    @abstractmethod
    def setAnimExportParams(self, **kwargs):
        """
        Adopts the animation settings from the supplied kwargs.

        :rtype: None
        """

        pass

    @abstractmethod
    def exportSelection(self, filePath):
        """
        Exports the active selection to the specified file path.

        :type filePath: str
        :rtype: bool
        """

        pass
