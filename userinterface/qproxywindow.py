from PySide2 import QtCore, QtWidgets, QtGui
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from dcc import fnqt
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QProxyWindow(QtWidgets.QMainWindow):
    """
    Overload of QMainWindow used to track all derived Robot Entertainment windows.
    This provides us the ability to close all windows on restart.
    """

    __instances__ = defaultdict(list)
    __icon__ = QtGui.QIcon()
    __singleton__ = True

    def __new__(cls, *args, **kwargs):

        return cls.getInstance()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :keyword parent: QtWidgets.QWidget
        :keyword flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Check if instance has been initialized
        #
        if self.isInitialized():

            return

        # Call parent method
        #
        parent = kwargs.get('parent', fnqt.FnQt().getMainWindow())
        flags = kwargs.get('flags', QtCore.Qt.WindowFlags())

        super(QProxyWindow, self).__init__(parent=parent, flags=flags)

        # Build user interface
        #
        self.__build__(**kwargs)

    @abstractmethod
    def __build__(self, **kwargs):
        """
        Private method used to build the user interface.

        :rtype: None
        """

        # Modify window properties
        #
        self.setObjectName(self.className)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowIcon(self.__class__.__icon__)

        # Store reference to instance
        #
        if self.isSingleton:

            self.__class__.__instances__[self.className] = self

    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QProxyWindow, self).showEvent(event)

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QProxyWindow, self).closeEvent(event)

        # Perform cleanup steps
        #
        self.hideTearOffMenus()
        self.removeInstance()

    @classproperty
    def className(cls):
        """
        Getter method that returns the name of this class.

        :rtype: str
        """

        return cls.__name__

    @classproperty
    def isSingleton(cls):
        """
        Getter method that evaluates if this class uses a singleton pattern.

        :rtype: bool
        """

        return cls.__singleton__

    @classmethod
    def creator(cls, *args, **kwargs):
        """
        Returns a new instance of this class.
        Overload this to change the arguments supplied to the class constructor.

        :rtype: QProxyWindow
        """

        return cls(*args, **kwargs)

    @classmethod
    def overrideWindowIcon(cls, icon):
        """
        Registers a custom icon for all derived classes.

        :type icon: str
        :rtype: None
        """

        cls.__icon__ = QtGui.QIcon(icon)

    @staticmethod
    def getTextWidth(item, text, offset=12):
        """
        Static method used to calculate the pixel units from the supplied string value.

        :type item: QtGui.QStandardItem
        :type text: str
        :type offset: int
        :rtype: int
        """

        # Get font from item and calculate width
        #
        font = item.font()
        fontMetric = QtGui.QFontMetrics(font)

        width = fontMetric.width(text) + offset

        return width

    @classmethod
    def isInitialized(cls):
        """
        Evaluates whether this class has already been initialized.

        :rtype: bool
        """

        return cls.className in cls.__instances__

    @classmethod
    def hasInstance(cls):
        """
        Checks if an instance already exists for this class.

        :rtype: bool
        """

        return cls.__instances__.get(cls.__name__, None) is not None

    @classmethod
    def getInstance(cls):
        """
        Returns the instance for this class.
        If no window is found then a new instance is returned.

        :rtype: QProxyWindow
        """

        # Check if instance already exists
        #
        if not cls.hasInstance() and not cls.isSingleton:

            cls.__instances__[cls.__name__] = cls.creator()

        return cls.__instances__[cls.__name__]

    @classmethod
    def removeInstance(cls, *args):
        """
        Removes the supplied instance from the internal array.

        :rtype: bool
        """

        # Check if instance exists
        #
        if cls.className in cls.__instances__:

            del cls.__instances__[cls.className]
            return True

        else:

            log.debug('Unable to locate window: %s' % cls.className)
            return False

    def hideTearOffMenus(self):
        """
        Closes all of the separated menus from the menu bar.

        :rtype: None
        """

        # Check if menu bar exists
        #
        menuBar = self.menuBar()  # type: QtWidgets.QMenuBar

        if menuBar is None:

            return

        # Iterate through menu actions
        #
        for action in menuBar.actions():

            menu = action.menu()  # type: QtWidgets.QMenu

            if menu.isTearOffMenuVisible():

                menu.hideTearOffMenu()

            else:

                continue

    @classmethod
    def closeWindows(cls):
        """
        Closes all of the open windows.
        Only the windows that inherit from this class will be closed!

        :rtype: None
        """

        # Iterate through windows
        #
        for (name, window) in cls.__instances__.items():

            log.info('Closing window: %s' % name)
            window.close()
