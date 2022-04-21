from . import qproxywindow, quicmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicWindow(quicmixin.QUicMixin, qproxywindow.QProxyWindow):
    """
    Overload of QUicMixin and QProxyWindow that dynamically creates windows at runtime.
    """

    # region Dunderscores
    def __build__(self, *args, **kwargs):
        """
        Private method used to build the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QUicWindow, self).__build__(*args, **kwargs)

        # Load user interface
        #
        self.preLoad()
        self.__load__(*args, **kwargs)
        self.postLoad()
        self.connectSlots()
    # endregion
