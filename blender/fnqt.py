from ..abstract import afnqt
from ..python import piputils
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

    def isEnabled(self):
        """
        Checks if the `bqt` addon exists.

        :rtype: bool
        """

        return piputils.hasPackage('bqt')

    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: Union[QtWidgets.QMainWindow, None]
        """

        if self.isEnabled():

            return QtWidgets.QApplication.instance().blender_widget

        else:

            return None

    def nativizeWindow(self, window):
        """
        Performs any DCC required operations to the supplied window.

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
