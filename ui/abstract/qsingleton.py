from Qt import QtCore, QtCompat

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


ShibokenObject = type(QtCore.QObject)


class QSingleton(ShibokenObject):
    """
    Shiboken abstract base class that supports singleton patterns.
    """

    # region Dunderscores
    __instances__ = {}

    def __call__(cls, *args, **kwargs):
        """
        Private method that's called whenever this class is called.

        :rtype: QSingleton
        """

        hasInstance = cls.hasInstance()

        if hasInstance:

            instance = cls.getInstance(*args, **kwargs)
            instance.setWindowState(QtCore.Qt.WindowActive)  # Reverts minimized state!

            return instance

        else:

            instance = super(QSingleton, cls).__call__(*args, **kwargs)
            instance.__post_init__(*args, **kwargs)

            cls.__instances__[cls.__name__] = instance

            return instance
    # endregion

    # region Methods
    def hasInstance(cls):
        """
        Evaluates if an instance of this class already exists.

        :rtype: bool
        """

        instance = cls.__instances__.get(cls.__name__, None)

        if instance is not None:

            return QtCompat.isValid(instance)

        else:

            return False

    def getInstance(cls, *args, **kwargs):
        """
        Returns an instance of this class.

        :key create: bool
        :rtype: QSingleton
        """

        hasInstance = cls.hasInstance()

        if hasInstance:

            return cls.__instances__[cls.__name__]

        else:

            return None
    # endregion
