from Qt import QtCompat

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QSignalBlocker(object):
    """
    Base class for Qt signal block contexts.
    """

    __slots__ = ('__widget__',)

    def __init__(self, widget):
        """
        Private method called after a new instance has been created.

        :type widget: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        super(QSignalBlocker, self).__init__()

        # Declare private variables
        #
        self.__widget__ = widget

    def __enter__(self):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        if QtCompat.isValid(self.__widget__):

            self.__widget__.blockSignals(True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        if QtCompat.isValid(self.__widget__):

            self.__widget__.blockSignals(False)
            self.__widget__ = None
