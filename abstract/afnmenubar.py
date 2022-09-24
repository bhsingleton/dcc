import os

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from xml.etree import ElementTree
from dcc.abstract import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnMenubar(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines menubar interfaces.
    """

    __slots__ = ()

    @abstractmethod
    def getMainMenubar(self):
        """
        Returns the main menu bar.

        :rtype: Any
        """

        pass

    @abstractmethod
    def iterMenus(self):
        """
        Returns a generator that yields main menus.

        :rtype: iter
        """

        pass

    @abstractmethod
    def getMenuTitle(self, menu, stripAmpersand=False):
        """
        Returns the title of the given menu.

        :type menu: Any
        :type stripAmpersand: bool
        :rtype: str
        """

        pass

    def findMenusByTitle(self, title):
        """
        Returns a list of menus with the given title.

        :type title: str
        :rtype: List[Any]
        """

        return [x for x in self.iterMenus() if self.getMenuTitle(x, stripAmpersand=True) == title]

    def hasMenu(self, title):
        """
        Evaluates if a menu with the given title exists.

        :type title: str
        :rtype: bool
        """

        return len(self.findMenuByTitle(title)) > 0

    @abstractmethod
    def removeMenu(self, menu):
        """
        Removes the given menu from the menubar.

        :type menu: Any
        :rtype: None
        """

        pass

    def removeMenusByTitle(self, title):
        """
        Removes any menus with the matching title.

        :type title: str
        :rtype: None
        """

        menus = self.findMenusByTitle(title)

        for menu in menus:

            self.removeMenu(menu)

    @abstractmethod
    def default(self, xmlElement, insertAt=-1, parent=None):
        """
        Returns a menu item using the supplied xml element.

        :type xmlElement: etree.Element
        :type insertAt: int
        :type parent: Any
        :rtype: Any
        """

        pass

    def loadConfiguration(self, filePath):
        """
        Loads the supplied configuration file onto the main menubar.

        :type filePath: str
        :rtype: Any
        """

        # Check if file exists
        #
        if not os.path.exists(filePath):

            log.warning('Cannot locate menu configuration: %s' % filePath)
            return

        # Initialize element tree
        #
        elementTree = ElementTree.parse(filePath)
        root = elementTree.getroot()

        # Remove any conflicting top-level menus
        #
        title = root.get('title', '')
        self.removeMenusByTitle(title)

        # Create menu layout
        #
        parent = self.getMainMenubar()
        insertAt = len(list(self.iterMenus())) - 1

        return self.default(root, insertAt=insertAt, parent=parent)

    def unloadConfiguration(self, filePath):
        """
        Unloads the supplied configuration file from the main menubar.

        :type filePath: str
        :rtype: Any
        """

        # Check if file exists
        #
        if not os.path.exists(filePath):

            log.warning('Cannot locate menu configuration: %s' % filePath)
            return

        # Initialize element tree
        #
        elementTree = ElementTree.parse(filePath)
        root = elementTree.getroot()

        # Remove top-level menus
        #
        title = root.get('title', '')
        self.removeMenusByTitle(title)
