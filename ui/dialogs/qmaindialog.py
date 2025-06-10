from ..abstract import qabcmeta
from ... import fnqt
from ...decorators.classproperty import classproperty
from ...vendor.Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QMainDialog(QtWidgets.QDialog, metaclass=qabcmeta.QABCMeta):
    """
    Overload of `QDialog` that extends upon base functionality.
    """

    # region Dunderscores
    __qt__ = fnqt.FnQt()
    __icon__ = QtGui.QIcon()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.pop('parent', QtWidgets.QApplication.activeWindow())
        f = kwargs.pop('f', QtCore.Qt.WindowFlags() | QtCore.Qt.Dialog)

        super(QMainDialog, self).__init__(parent=parent, f=f)

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        # Setup user interface
        #
        self.__setup_ui__(*args, **kwargs)
        self.__setstate__(kwargs)

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Initialize main dialog
        #
        self.setObjectName(self.className)
        self.setModal(kwargs.get('modal', True))
        self.setSizeGripEnabled(kwargs.get('sizeGripEnabled', True))

        # Override default dialog icon
        #
        if not self.customIcon.isNull():

            self.setWindowIcon(self.customIcon)

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

    @classproperty
    def qt(cls):
        """
        Getter method that returns the QT interface.

        :rtype: fnqt.FnQt
        """

        return cls.__qt__

    @classproperty
    def customIcon(cls):
        """
        Getter method that returns the custom icon for this class.

        :rtype: QtGui.QIcon
        """

        return cls.__icon__

    @customIcon.setter
    def customIcon(cls, customIcon):
        """
        Setter method that updates the custom icon for this class.

        :type customIcon: QtGui.QIcon
        :rtype: None
        """

        cls.__icon__ = customIcon
    # endregion

    # region Methods
    def centerToParent(self):
        """
        Centers this dialog to its current parent.

        :rtype: None
        """

        window = self.window()
        offset = window.geometry().center() - self.geometry().center()

        self.move(offset)
    # endregion
