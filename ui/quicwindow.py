from dcc.ui import qproxywindow, quicinterface

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicWindow(quicinterface.QUicInterface, qproxywindow.QProxyWindow):
    """
    Overload of QUicInterface and QProxyWindow used to dynamically create windows at runtime.
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
    # endregion
