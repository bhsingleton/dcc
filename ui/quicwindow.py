from . import qproxywindow, quicmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicWindow(quicmixin.QUicMixin, qproxywindow.QProxyWindow):
    """
    Overload of `QUicMixin` and `QProxyWindow` that dynamically creates windows at runtime.
    """

    pass
