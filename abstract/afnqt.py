from abc import ABCMeta, abstractmethod
from . import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnQt(afnbase.AFnBase, metaclass=ABCMeta):
    """
    Overload of AFnBase that outlines function set behaviour for DCC qt objects.
    """

    __slots__ = ()

    @abstractmethod
    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: PySide2.QtWidgets.QMainWindow
        """

        pass
