from PySide2 import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QDivider(QtWidgets.QFrame):
    """
    Overload of QFrame used to conveniently create a divider.
    """

    def __init__(self, orientation, parent=None, f=QtCore.Qt.WindowFlags()):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :type f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QDivider, self).__init__(parent=parent)

        # Edit class properties
        #
        self.setFrameShape(QtWidgets.QFrame.VLine if orientation == QtCore.Qt.Vertical else QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
