try:

    import qtmax  # max_version >= 2021

except ImportError:

    import MaxPlus as qtmax  # max_version < 2021

from ..abstract import afnqt

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnQt(afnqt.AFnQt):
    """
    Overload of AFnQt that interfaces with Qt objects in 3DS Max.
    """

    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: PySide2.QtWidgets.QMainWindow
        """

        return qtmax.GetQMaxMainWindow()
