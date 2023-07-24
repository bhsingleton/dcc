from Qt import QtCore, QtWidgets, QtGui, QtCompat
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
    __qt__ = fnqt.FnQt()
    __author__ = 'Ben Singleton'
    __keys__ = (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete)

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
        parent = kwargs.pop('parent', self.qt.getMainWindow())
        flags = kwargs.pop('flags', QtCore.Qt.WindowFlags())

        super(QProxyWindow, self).__init__(parent=parent, flags=flags)

        # Initialize user interface
        #
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
    def author(cls):
        """
        Getter method that returns the author of this class.

        :rtype: str
        """

        return cls.__author__

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

    # region Events
    def keyPressEvent(self, event):
        """
        This event handler can be reimplemented in a subclass to receive key press events for the widget.
        This implementation prevents any hotkeys from propagating to the DCC main window.

        :type event: QtGui.QKeyEvent
        :rtype: None
        """

        if event.key() in self.__class__.__keys__:

            event.accept()  # FYI this does not work in 3ds Max...

        else:

            super(QProxyWindow, self).keyPressEvent(event)

    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QProxyWindow, self).showEvent(event)

        # Nativize window with DCC application
        #
        self.qt.nativizeWindow(self)

        # Load user settings
        #
        settings = self.getSettings()
        self.loadSettings(settings)

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QProxyWindow, self).closeEvent(event)

        # Save user settings
        #
        settings = self.getSettings()
        self.saveSettings(settings)

        # Cleanup Qt resources
        #
        self.hideTearOffMenus()
        self.removeInstance(self)
    # endregion

    # region Methods
    @classmethod
    def getSettings(cls):
        """
        Returns the user settings for this class.

        :rtype: QtCore.QSettings
        """

        return QtCore.QSettings(cls.author, cls.className)

    def loadSettings(self, settings):
        """
        Loads the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Resize window
        #
        size = settings.value('editor/size')

        if size is not None:

            self.resize(size)

        # Move window
        #
        pos = settings.value('editor/pos')

        if pos is not None:

            self.move(pos)

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :rtype: None
        """

        settings.setValue('editor/size', self.size())
        settings.setValue('editor/pos', self.pos())

    def hideTearOffMenus(self):
        """
        Closes all the separated menus from the menu bar.

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

            return cls.hasInstance(cls.className)

        elif len(args) == 1:

            window = cls.__instances__.get(args[0], None)

            if window is not None:

                return QtCompat.isValid(window)

            else:

                return False

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

            return cls.getInstance(cls.className)

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
        Closes all the open windows.
        Only the windows that inherit from this class will be closed!

        :rtype: None
        """

        # Iterate through windows
        #
        names = list(cls.__instances__.keys())

        for name in names:

            # Check if instance is valid
            #
            window = cls.__instances__[name]

            if QtCompat.isValid(window):

                log.info('Closing window: %s' % name)
                window.close()

            else:

                log.debug('Cleaning up dead pointer: %s' % name)
                del cls.__instances__[name]
    # endregion
