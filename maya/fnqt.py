import maya.OpenMayaUI as omui

from ..abstract import afnqt
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnQt(afnqt.AFnQt):
    """
    Overload of AFnQt that interfaces with Qt objects in Maya.
    """

    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: PySide2.QtWidgets.QMainWindow
        """

        return wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QMainWindow)
