from abc import ABCMeta, abstractmethod
from six import with_metaclass, integer_types
from functools import partial
from PySide2 import QtWidgets

from dcc.abstract import afnbase
from dcc.xml import xmlutils
from dcc.ui import qmainmenu, qloggingmenu

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

        :rtype: PySide2.QtWidgets.QMainWindow
        """

        pass

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

    @staticmethod
    def objectSafeName(string):
        """
        Returns a string that safe to assign as an object name.
        This string will be compliant with Maya's pathing syntax.

        :rtype: str
        """

        return string.replace(' ', '_')

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

    def iterMainMenus(self):
        """
        Returns a generator that yields all top-level main menu objects.

        :rtype: iter
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

    def findMainMenuByTitle(self, title):
        """
        Returns the top level menu associated with the given title.

        :type title: str
        :rtype: QtWidgets.QMenu
        """

        menus = [x for x in self.iterMainMenus() if x.title() == title]
        numMenus = len(menus)

        if numMenus == 0:

            return

        elif numMenus == 1:

            return menus[0]

        else:

            raise TypeError('findTopLevelMenuByTitle() expects a unique title!')

    def findMainMenuByName(self, name):
        """
        Returns the top level menu associated with the given object name.

        :type name: str
        :rtype: QtWidgets.QMenu
        """

        menus = [x for x in self.iterMainMenus() if x.objectName() == name]
        numMenus = len(menus)

        if numMenus == 0:

            return

        elif numMenus == 1:

            return menus[0]

        else:

            raise TypeError('findTopLevelMenuByName() expects a unique name!')

    def createMenuFromXmlElement(self, xmlElement, parent=None):
        """
        Returns a menu item using the supplied xml element.

        :type xmlElement: xml.etree.ElementTree.Element
        :type parent: Union[QtWidgets.QMenu, QtWidgets.QMenuBar]
        :rtype: Union[QtWidgets.QMenu, QtWidgets.QAction]
        """

        # Query menu tag to determine menu type
        #
        if xmlElement.tag == 'Menu':

            # Create new menu
            #
            title = xmlElement.get('title', default='')
            log.info('Creating menu: %s' % title)

            menu = QtWidgets.QMenu(title, parent)
            menu.setObjectName(self.objectSafeName(title))
            menu.setSeparatorsCollapsible(False)
            menu.setTearOffEnabled(bool(xmlElement.get('tearOff', default=False)))
            menu.setWindowTitle(title)

            # Create child menus
            #
            for child in iter(xmlElement):

                self.createMenuFromXmlElement(child, parent=menu)

            # Assign submenu to parent menu
            #
            if parent is not None:

                parent.addMenu(menu)

            return menu

        elif xmlElement.tag == 'Action':

            # Create new action
            #
            text = xmlElement.get('text', default='')
            log.info('Creating action: %s' % text)

            action = QtWidgets.QAction(text, parent)
            action.setObjectName(self.objectSafeName(text))
            action.setToolTip(xmlElement.get('tooltip', ''))

            # Configure trigger event
            #
            language = xmlElement.get('language', default='')
            command = xmlElement.get('command', default='')

            if language == 'python':

                action.triggered.connect(partial(self.execute, command))

            else:

                action.triggered.connect(self.partial(command))

            # Assign action to parent menu
            #
            parent.addAction(action)
            return action

        elif xmlElement.tag == 'Section':

            return parent.addSection(xmlElement.get('text', default=''))

        elif xmlElement.tag == 'Separator':

            return parent.addSeparator()

        else:

            raise TypeError('createMenuItem() expects a valid xml tag (%s found)!' % xmlElement.tag)

    def createMenuFromFile(self, filePath):
        """
        Creates a menu system from the supplied xml file configuration.

        :type filePath: str
        :rtype: QtWidgets.QMenu
        """

        # Parse xml file and inspect root element
        #
        xmlTree = xmlutils.parse(filePath)
        xmlElement = xmlTree.getroot()

        if xmlElement.tag != 'Menu':

            raise TypeError('createMenuFromFile() expects Menu tag for root element (%s given)!' % xmlElement.tag)

        # Create menu from xml element
        #
        title = xmlElement.get('title', '')
        tearOff = bool(xmlElement.get('tearOff', True))

        menu = self.findMainMenuByTitle(title)

        if menu is None:

            menuBar = self.getMainMenuBar()

            menu = qmainmenu.QMainMenu(title, tearOff=tearOff, parent=menuBar)
            menuBar.insertMenu(menuBar.actions()[-1], menu)

        # Append new menu to menu bar
        #
        menu.clear()

        for child in iter(xmlElement):

            self.createMenuFromXmlElement(child, parent=menu)

        return menu

    def removeMenuFromAssociatedFile(self, filePath):
        """
        Removes the menu that is associated with the supplied file.

        :type filePath: str
        :rtype: None
        """

        # Parse xml file and inspect root element
        #
        xmlTree = xmlutils.parse(filePath)
        xmlElement = xmlTree.getroot()

        if xmlElement.tag != 'Menu':

            raise TypeError('removeMenuFromAssociatedFile() expects Menu tag for root element (%s given)!' % xmlElement.tag)

        # Unregister top-level menu
        #
        title = xmlElement.get('title', '')
        menu = self.findMainMenuByTitle(title)

        if menu is not None:

            menu.deleteLater()

    def createLoggingMenu(self):
        """
        Creates a logging menu for modifying logger levels.
        If the menu already exists the current instance will be refreshed.

        :rtype: None
        """

        # Check if menu already exists
        #
        menuBar = self.getMainMenuBar()
        menu = self.findMainMenuByTitle('Logging Control')

        if menu is None:

            menu = qloggingmenu.QLoggingMenu('Logging Control', parent=menuBar)
            menuBar.insertMenu(menuBar.actions()[-1], menu)

        else:

            menu.refresh()

        return menu
