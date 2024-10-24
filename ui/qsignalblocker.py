from Qt import QtCompat
from collections import deque

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QSignalBlocker(object):
    """
    Base class for Qt signal block contexts.
    """

    __slots__ = ('__widgets__',)

    def __init__(self, *widgets):
        """
        Private method called after a new instance has been created.

        :type widgets: Union[QtWidgets.QWidget, List[QtWidgets.QWidget]]
        :rtype: None
        """

        # Call parent method
        #
        super(QSignalBlocker, self).__init__()

        # Declare private variables
        #
        self.__widgets__ = deque(widgets)

    def __enter__(self):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        for widget in self.__widgets__:

            if QtCompat.isValid(widget):

                widget.blockSignals(True)

            else:

                continue

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        while len(self.__widgets__) > 0:

            widget = self.__widgets__.pop()

            if QtCompat.isValid(widget):

                widget.blockSignals(False)

            else:

                continue
