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
        """
        Private method called before a new instance has been created.

        :keyword parent: QtWidgets.QWidget
        :keyword flags: QtCore.Qt.WindowFlags
        :rtype: QProxyWindow
        """

        # Check if this class uses a singleton pattern
        #
        if cls.isSingleton and cls.hasInstance():

            return cls.__instances__[cls.__name__][0]

        else:

            return super(QProxyWindow, cls).__new__(cls, *args, **kwargs)

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
        self.__instances__[self.className].append(self)

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
        self.removeInstance(self)

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
        Getter method that determines if this class uses a singleton pattern.

        :rtype: bool
        """

        return cls.__singleton__

    @classproperty
    def instances(cls):
        """
        Getter method that returns a dictionary of all existing instances.

        :rtype: dict[str:QProxyWindow]
        """
        return cls.__instances__

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

        if cls.isSingleton:

            return len(cls.__instances__[cls.className]) == 1

        else:

            return False

    @classmethod
    def hasInstance(cls, *args):
        """
        Checks if an instance already exists for this class.
        Optional names can be supplied as arguments to be evaluated instead.

        :rtype: Union[bool, list]
        """

        if len(args) == 0:

            return len(cls.__instances__[cls.__name__]) > 0

        elif len(args) == 1:

            return len(cls.__instances__[args[0]]) > 0

        else:

            return [cls.hasInstance(x) for x in args]

    @classmethod
    def getInstance(cls, *args):
        """
        Returns the instance for this class.
        An optional name can be supplied to be returned instead.

        :rtype: QProxyWindow
        """

        # Check if a class name was supplied
        #
        className = cls.__name__

        if len(args) > 0:

            className = args[0]

        # Check if this window uses a singleton pattern
        # If not then a list of all existing instances
        #
        instances = cls.__instances__[className]

        if cls.isSingleton:

            if len(instances) == 1:

                return instances[0]

            else:

                return None

        else:

            return instances

    @classmethod
    def removeInstance(cls, instance):
        """
        Removes the supplied instance from the internal array.

        :type instance: QProxyWindow
        :rtype: bool
        """

        index = cls.__instances__[instance.className].index(instance)
        del cls.__instances__[instance.className][index]

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
