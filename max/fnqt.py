import pymxs

from functools import partial
from dcc.abstract import afnqt
from dcc.python import importutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


MaxPlus = importutils.tryImport('MaxPlus')
qtmax = importutils.tryImport('qtmax', default=MaxPlus)


class FnQt(afnqt.AFnQt):
    """
    Overload of AFnQt that interfaces with Qt objects in 3DS Max.
    """

    __slots__ = ()

    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: PySide2.QtWidgets.QMainWindow
        """

        return qtmax.GetQMaxMainWindow()

    def nativizeWindow(self, window):
        """
        Performs any DCC required operations to the supplied window.
        For instance, 3ds Max requires you disable accelerators in order to receive key press events.

        :type window: QtWidgets.QMainWindow
        :rtype: None
        """

        qtmax.DisableMaxAcceleratorsOnFocus(window, True)

    def partial(self, command):
        """
        Returns a partial object for executing commands in a DCC embedded language.

        :type command: str
        :rtype: partial
        """

        return partial(pymxs.runtime.execute, command)
