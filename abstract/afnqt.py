from abc import ABCMeta, abstractmethod
from functools import partial
from . import afnbase
from ..ui import qloggingmenu
from ..vendor.six import with_metaclass
from ..vendor.Qt import QtCore, QtWidgets, QtCompat

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnQt(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC qt objects.
    """

    __slots__ = ()

    @abstractmethod
    def getMainWindow(self):
        """
        Returns the main window.

        :rtype: QtWidgets.QMainWindow
        """

        pass

    def getApplication(self):
        """
        Returns the current application instance.
        Some DCCs will try and return a QCoreApplication instance.
        This method will ensure that those instances are cast back to QApplication.

        :rtype: QtWidgets.QApplication
        """

        # Evaluate instance type
        #
        instance = QtWidgets.QApplication.instance()

        if isinstance(instance, QtWidgets.QApplication):

            return instance

        elif isinstance(instance, QtCore.QCoreApplication):

            return QtCompat.wrapInstance(QtCompat.getCppPointer(instance), QtWidgets.QApplication)

        else:

            raise RuntimeError('getApplication() unable to get application!')

    def getMainMenuBar(self):
        """
        Returns the menu bar from the main window.
        This is the safest approach to retrieve the current menu bar.

        :rtype: PySide2.QtWidgets.QMenuBar
        """

        # Iterate through children
        #
        for child in self.getMainWindow().children():

            # Check if this is a menu bar
            #
            if isinstance(child, QtWidgets.QMenuBar) and child.isVisible():

                return child

            else:

                continue

    def iterMainMenus(self):
        """
        Returns a generator that yields top-level menus.

        :rtype: Iterator[QtWidgets.QMenu]
        """

        # Iterate through actions
        #
        menuBar = self.getMainMenuBar()

        for child in menuBar.children():

            # Check if menu is visible
            #
            if isinstance(child, QtWidgets.QMenu):

                yield child

            else:

                continue

    def nativizeWindow(self, window):
        """
        Performs any necessary steps to nativize the supplied window with the associated DCC application.
        For instance, 3ds Max requires you disable accelerators in order to receive key press events.

        :type window: QtWidgets.QMainWindow
        :rtype: None
        """

        pass

    @abstractmethod
    def partial(self, command):
        """
        Returns a partial object for executing commands in a DCC embedded language.

        :type command: str
        :rtype: partial
        """

        pass

    @staticmethod
    def execute(string):
        """
        Executes the supplied string.

        :type string: str
        :rtype: None
        """

        try:

            exec(string)

        except Exception as exception:

            log.error(exception)

    def createLoggingMenu(self):
        """
        Creates a logging menu for modifying logger levels.
        If the menu already exists the current instance will be refreshed.

        :rtype: None
        """

        # Check if menu already exists
        #
        menuBar = self.getMainMenuBar()

        menus = [menu for menu in self.iterMainMenus() if menu.title() == 'Logging Control']
        numMenus = len(menus)

        if numMenus == 0:

            menu = qloggingmenu.QLoggingMenu('Logging Control', parent=menuBar)
            menuBar.insertMenu(menuBar.actions()[-1], menu)

        else:

            menu = menus[0]
            menu.refresh()

        return menu
