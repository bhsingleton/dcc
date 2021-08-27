from PySide2 import QtWidgets

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QSeparator(QtWidgets.QAction):
    """
    Overload of QAction used to conveniently create a separator with name.
    """

    def __init__(self, name, parent):
        """
        Private method called after a new instance is created.

        :type name: str
        :type parent: QtWidgets.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QSeparator, self).__init__(name, parent=parent)

        # Enable separator
        #
        self.setSeparator(True)
