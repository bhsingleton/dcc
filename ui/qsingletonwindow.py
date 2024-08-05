from Qt import QtCore, QtWidgets, QtGui, QtCompat
from . import resources  # Imports all DCC resources!
from .abstract import qsingleton
from .. import fnqt
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QSingletonWindow(QtWidgets.QMainWindow, metaclass=qsingleton.QSingleton):
    """
    Overload of `QMainWindow` that loads custom windows via .ui file.
    """

    # region Dunderscores
    __qt__ = fnqt.FnQt()
    __icon__ = QtGui.QIcon()
    __author__ = 'Ben Singleton'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.pop('parent', self.qt.getMainWindow())
        flags = kwargs.pop('flags', QtCore.Qt.WindowFlags())

        super(QSingletonWindow, self).__init__(parent=parent, flags=flags)

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        # Setup user interface
        #
        self.__setup_ui__(*args, **kwargs)

        # Load user settings
        #
        settings = self.getSettings()
        self.loadSettings(settings)

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Initialize main window
        #
        self.setObjectName(self.className)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # Override default window icon
        #
        if not self.customIcon.isNull():

            self.setWindowIcon(self.customIcon)

        # Nativize window with DCC application
        #
        self.qt.nativizeWindow(self)
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
    def mousePressEvent(self, event):
        """
        Event method called after a mouse press.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Evaluate focused widget
        #
        focusedWidget = self.focusWidget()

        if isinstance(focusedWidget, (QtWidgets.QAbstractSpinBox, QtWidgets.QLineEdit)):

            focusedWidget.clearFocus()

        # Call parent method
        #
        super(QSingletonWindow, self).mousePressEvent(event)

    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QSingletonWindow, self).showEvent(event)

        # Add callbacks
        #
        self.addCallbacks()

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Remove callbacks
        #
        self.removeCallbacks()

        # Next, remove any torn-off menus
        #
        self.hideTearOffMenus()

        # Finally, save user settings
        #
        settings = self.getSettings()
        self.saveSettings(settings)

        # Call parent method
        #
        super(QSingletonWindow, self).closeEvent(event)
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

        if isinstance(size, QtCore.QSize):

            self.resize(size)

        # Move window
        #
        pos = settings.value('editor/pos')

        if isinstance(pos, QtCore.QPoint):

            screens = QtWidgets.QApplication.screens()
            isValid = any([screen.geometry().contains(pos) for screen in screens])

            if isValid:

                self.move(pos)

            else:

                log.debug(f'{self.className} window is out of bounds @ {pos}')

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :rtype: None
        """

        settings.setValue('editor/size', self.size())
        settings.setValue('editor/pos', self.pos())

    def addCallbacks(self):
        """
        Adds any callbacks required by this window.

        :rtype: None
        """

        pass

    def removeCallbacks(self):
        """
        Removes any callbacks created by this window.

        :rtype: None
        """

        pass

    def hideTearOffMenus(self):
        """
        Closes all the separated menus from the menu bar.

        :rtype: None
        """

        # Check if menu bar exists
        #
        menuBar = self.menuBar()  # type: QtWidgets.QMenuBar

        if not isinstance(menuBar, QtWidgets.QMenuBar):

            return

        # Iterate through menu actions
        #
        for action in menuBar.actions():

            # Check if menu exists
            #
            menu = action.menu()  # type: QtWidgets.QMenu

            if not isinstance(menu, QtWidgets.QMenu):

                continue

            # Check if menu was torn off
            #
            if menu.isTearOffMenuVisible():

                menu.hideTearOffMenu()

            else:

                continue

    @classmethod
    def closeWindows(cls):
        """
        Closes all the open windows.
        Only the windows that inherit from this class will be closed!

        :rtype: None
        """

        # Iterate through instances
        #
        for (name, window) in cls.__singletons__.items():

            # Check if instance is valid
            #
            if not isinstance(window, QtWidgets.QMainWindow):

                continue

            # Check if instance is alive
            #
            if not QtCompat.isValid(window):

                continue

            # Close window
            #
            log.info(f'Closing window: {name}')
            window.close()

        # Clear instance tracker
        #
        cls.__singletons__.clear()
    # endregion
