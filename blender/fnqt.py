from ..abstract import afnqt
from ..vendor.Qt import QtWidgets

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnQt(afnqt.AFnQt):
    """
    Overload of `AFnQt` that implements the Qt interface for Blender.
    """

    __slots__ = ()

    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: PySide2.QtWidgets.QMainWindow
        """

        return QtWidgets.QApplication.instance().blender_widget  # This only works so long as the `bqt` addon is installed!

    def nativizeWindow(self, window):
        """
        Performs any DCC required operations to the supplied window.
        For instance, 3ds Max requires you disable accelerators in order to receive key press events.

        :type window: QtWidgets.QMainWindow
        :rtype: None
        """

        pass

    def partial(self, command):
        """
        Returns a partial object for executing commands in a DCC embedded language.

        :type command: str
        :rtype: partial
        """

        return
