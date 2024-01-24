import os
import sys

from Qt import QtCore, QtWidgets, QtGui, QtCompat
from . import resources  # Imports all DCC resources!
from .abstract import qsingleton
from .. import fnqt
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicWindow(QtWidgets.QMainWindow, metaclass=qsingleton.QSingleton):
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

        super(QUicWindow, self).__init__(parent=parent, flags=flags)

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        # Load user interface
        #
        self.preLoad(*args, **kwargs)
        self.__load__(*args, **kwargs)
        self.postLoad(*args, **kwargs)

        # Edit window properties
        #
        self.setObjectName(self.className)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        if not self.customIcon.isNull():

            self.setWindowIcon(self.customIcon)

    def __getattribute__(self, item):
        """
        Private method returns an internal attribute with the associated name.
        Sadly all pointers are lost from QUicLoader, so we have to relocate them on demand.

        :type item: str
        :rtype: Any
        """

        # Call parent method
        #
        obj = super(QUicWindow, self).__getattribute__(item)

        if isinstance(obj, QtCore.QObject):

            # Check if C++ pointer is still valid
            #
            if not QtCompat.isValid(obj):

                obj = self.findChild(QtCore.QObject, item)
                setattr(self, item, obj)

                return obj

            else:

                return obj

        else:

            return obj

    def __load__(self, *args, **kwargs):
        """
        Private method used to load the user interface from the associated .ui file.
        Be sure to overload the associated class methods to augment the behavior of this method.

        :rtype: QtWidgets.QWidget
        """

        # Concatenate ui path
        #
        filename = self.filename()
        workingDirectory = kwargs.get('workingDirectory', self.workingDirectory())

        filePath = os.path.join(workingDirectory, filename)

        # Load ui from file
        #
        if os.path.exists(filePath):

            log.info(f'Loading UI file: {filePath}')
            return QtCompat.loadUi(uifile=filePath, baseinstance=self)

        else:

            log.debug(f'Cannot locate UI file: {filePath}')
            return self
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
    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QUicWindow, self).showEvent(event)

        # Nativize window within DCC application
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
        super(QUicWindow, self).closeEvent(event)

        # Save user settings
        #
        settings = self.getSettings()
        self.saveSettings(settings)

        # Cleanup any torn-off menus
        #
        self.hideTearOffMenus()
    # endregion

    # region Methods
    @classmethod
    def filename(cls):
        """
        Returns the ui configuration filename for this class.
        This defaults to the name of this python file.

        :rtype: str
        """

        filePath = os.path.abspath(sys.modules[cls.__module__].__file__)
        directory, filename = os.path.split(filePath)
        name, ext = os.path.splitext(filename)

        return '{name}.ui'.format(name=name)

    @classmethod
    def workingDirectory(cls):
        """
        Returns the working directory for this class.
        This defaults to the directory this python file resides in.

        :rtype: str
        """

        return os.path.dirname(os.path.abspath(sys.modules[cls.__module__].__file__))

    def preLoad(self, *args, **kwargs):
        """
        Called before the user interface has been loaded.

        :rtype: None
        """

        pass

    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        pass

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

            menu = action.menu()  # type: QtWidgets.QMenu

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
