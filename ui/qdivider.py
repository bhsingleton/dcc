from ..vendor.Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QDivider(QtWidgets.QFrame):
    """
    Overload of `QFrame` that draws vertical and horizontal dividers.
    """

    def __init__(self, orientation, **kwargs):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :type f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.get('parent', None)
        super(QDivider, self).__init__(parent=parent)

        # Initialize divider
        #
        frameShadow = kwargs.get('frameShadow', QtWidgets.QFrame.Sunken)

        if orientation == QtCore.Qt.Horizontal:

            self.setFrameShape(QtWidgets.QFrame.HLine)
            self.setFrameShadow(frameShadow)
            self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

        elif orientation == QtCore.Qt.Vertical:

            self.setFrameShape(QtWidgets.QFrame.VLine)
            self.setFrameShadow(frameShadow)
            self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding))

        else:

            raise TypeError(f'__init__() expects a valid orientation ({orientation} given)!')
