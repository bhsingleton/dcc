import maya.cmds as mc
import maya.mel as mel
import maya.OpenMayaUI as omui

from PySide2 import QtWidgets
from shiboken2 import wrapInstance
from functools import partial

from ..abstract import afnqt

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnQt(afnqt.AFnQt):
    """
    Overload of AFnQt that interfaces with Qt objects in Maya.
    """

    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: PySide2.QtWidgets.QMainWindow
        """

        return wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QMainWindow)

    def partial(self, command):
        """
        Returns a partial object for executing commands in a DCC embedded language.

        :type command: str
        :rtype: partial
        """

        return partial(mel.eval, command)
