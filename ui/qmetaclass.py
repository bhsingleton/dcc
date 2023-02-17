from Qt import QtCore

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


ShibokenObject = type(QtCore.QObject)


class QMetaclass(ShibokenObject):
    """
    Extension of shiboken's metaclass to support post initialization.
    """

    def __call__(cls, *args, **kwargs):
        """
        Private method that's called whenever this class is evoked.

        :rtype: QMetaclass
        """

        obj = super(QMetaclass, cls).__call__(*args, **kwargs)
        obj.__post_init__(*args, **kwargs)

        return obj
