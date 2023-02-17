from Qt import QtWidgets
from . import quicmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicWidget(quicmixin.QUicMixin, QtWidgets.QWidget):
    """
    Overload of `QUicMixin` and `QWidget` that dynamically creates widgets at runtime.
    """

    pass
