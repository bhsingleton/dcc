from maya import cmds as mc
from maya import mel as mel
from maya import OpenMayaUI as omui
from functools import partial
from ..abstract import afnqt
from ..vendor.Qt import QtWidgets, QtCompat

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnQt(afnqt.AFnQt):
    """
    Overload of AFnQt that interfaces with Qt objects in Maya.
    """

    __slots__ = ()

    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: PySide2.QtWidgets.QMainWindow
        """

        return QtCompat.wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QMainWindow)

    def partial(self, command):
        """
        Returns a partial object for executing commands in a DCC embedded language.

        :type command: str
        :rtype: partial
        """

        return partial(mel.eval, command)
