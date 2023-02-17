from Qt import QtCore, QtWidgets, QtGui
from dcc.ui import quicmixin, resources  # Initializes dcc resources!
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicDialog(quicmixin.QUicMixin, QtWidgets.QDialog):
    """
    Overload of `QUicMixin` and `QDialog` that dynamically creates dialogs at runtime.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called before a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.pop('parent', QtWidgets.QApplication.activeWindow())
        f = kwargs.pop('f', QtCore.Qt.WindowFlags())

        super(QUicDialog, self).__init__(parent=parent, f=f)

    def __setstate__(self, state):
        """
        Private method that inherits the contents of the pickled object.

        :type state: dict
        :rtype: None
        """

        # Iterate through items
        #
        for (key, value) in state.items():

            # Check if class has property
            #
            func = getattr(self.__class__, key, None)

            if not isinstance(func, property):

                continue

            # Check if property is settable
            #
            if callable(func.fset):

                func.fset(self, value)
    # endregion

    # region Properties
    @classproperty
    def className(cls):
        """
        Getter method that returns the name of this class.

        :rtype: str
        """

        return cls.__name__
    # endregion

    # region Methods
    def preLoad(self, *args, **kwargs):
        """
        Called before the user interface has been loaded.

        :rtype: None
        """

        self.setObjectName(self.className)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Dialog)
        self.setModal(True)

    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        self.__setstate__(kwargs)
    # endregion
