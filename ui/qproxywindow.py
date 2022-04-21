from PySide2 import QtCore, QtWidgets, QtGui
from dcc import fnqt
from dcc.ui import resources  # Initializes dcc resources!
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QProxyWindow(QtWidgets.QMainWindow):
    """
    Overload of QMainWindow used to provide an interface for tracking all derived windows.
    """

    # region Dunderscores
    __instances__ = {}
    __icon__ = QtGui.QIcon()
    __author__ = 'Ben Singleton'

    def __new__(cls, *args, **kwargs):
        """
        Private method called before a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: QProxyWindow
        """

        # Check if this class uses a singleton pattern
        #
        if cls.hasInstance():

            return cls.__instances__[cls.className]

        else:

            return super(QProxyWindow, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Check if instance has been initialized
        #
        if self.isInitialized():

            return

        # Call parent method
        #
        parent = kwargs.pop('parent', fnqt.FnQt().getMainWindow())
        flags = kwargs.pop('flags', QtCore.Qt.WindowFlags())

        super(QProxyWindow, self).__init__(parent=parent, flags=flags)

        # Initialize user interface
        #
        self.__settings__ = QtCore.QSettings(self.__author__, self.className)
        self.__build__(*args, **kwargs)
        self.__instances__[self.className] = self

    def __build__(self, *args, **kwargs):
        """
        Private method that builds the user interface.

        :rtype: None
        """

        # Modify window properties
        #
        self.setObjectName(self.className)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Check if custom icon exists
        #
        if not self.customIcon.isNull():

            self.setWindowIcon(self.customIcon)
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

    @property
    def settings(self):
        """
        Getter method that returns the settings for this window.

        :rtype: QtCore.QSettings
        """

        return self.__settings__
    # endregion

    # region Methods
    def hasSettings(self):
        """
        Evaluates if this window has any settings.

        :rtype: bool
        """

        return len(self.settings.allKeys()) > 0

    def loadSettings(self):
        """
        Loads the user settings.
        The base implementation handles size and location.

        :rtype: None
        """

        log.info('Loading settings from: %s' % self.settings.fileName())
        self.resize(self.settings.value('editor/size'))
        self.move(self.settings.value('editor/pos'))

    def saveSettings(self):
        """
        Saves the user settings.
        The base implementation handles size and location.

        :rtype: None
        """

        log.info('Saving settings to: %s' % self.settings.fileName())
        self.settings.setValue('editor/size', self.size())
        self.settings.setValue('editor/pos', self.pos())

    @classmethod
    def overrideWindowIcon(cls, icon):
        """
        Registers a custom icon for all derived classes.

        :type icon: str
        :rtype: None
        """

        cls.__icon__ = QtGui.QIcon(icon)

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
    def isInitialized(cls):
        """
        Evaluates whether this class has already been initialized.

        :rtype: bool
        """

        return cls.hasInstance(cls.className)

    @classmethod
    def hasInstance(cls, *args):
        """
        Checks if an instance already exists for this class.
        Optional names can be supplied as arguments to be evaluated instead.

        :rtype: Union[bool, list]
        """

        if len(args) == 0:

            return cls.__instances__.get(cls.className, None) is not None

        elif len(args) == 1:

            return cls.__instances__.get(args[0], None) is not None

        else:

            return [cls.hasInstance(x) for x in args]

    @classmethod
    def getInstance(cls, *args):
        """
        Returns the instance for this class.
        An optional name can be supplied to be returned instead.

        :rtype: QProxyWindow
        """

        if len(args) == 0:

            return cls.__instances__.get(cls.className, None)

        elif len(args) == 1:

            return cls.__instances__.get(args[0], None)

        else:

            return [cls.getInstance(arg) for arg in args]

    @classmethod
    def removeInstance(cls, *args):
        """
        Removes the supplied instance from the internal array.

        :type args: Sequence[QProxyWindow]
        :rtype: None
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            # Retrieve instance using class name
            #
            instance = cls.__instances__.get(cls.className, None)

            if instance is not None:

                cls.removeInstance(instance)

        else:

            # Iterate through arguments
            #
            for arg in args:

                del cls.__instances__[arg.className]

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
    # endregion

    # region Events
    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QProxyWindow, self).showEvent(event)

        # Perform startup routines
        #
        if self.hasSettings():

            self.loadSettings()

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QProxyWindow, self).closeEvent(event)

        # Perform closing routines
        #
        self.saveSettings()
        self.hideTearOffMenus()
        self.removeInstance(self)
    # endregion
