from abc import ABCMeta, abstractmethod
from six import with_metaclass

from . import afnbase
from ..xml import xmlutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnMenu(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC menu creation.
    """

    __slots__ = ()

    @abstractmethod
    def createMenuItem(self, xmlElement, parent=None):
        """
        Returns a new menu item using the supplied xml element.

        :type xmlElement: xml.etree.ElementTree.Element
        :type parent: Any
        :rtype: Any
        """

        pass

    @abstractmethod
    def getMainMenuBar(self):
        """
        Returns the main menu bar to parent new menu items to.
        Be sure to return an object that is compatible with your DCC overloads!

        :rtype: Any
        """

        pass

    def createMenuFromFile(self, filePath):
        """
        Creates a menu system from the supplied xml file configuration.

        :type filePath: str
        :rtype: None
        """

        # Parse xml file
        #
        xmlTree = xmlutils.parse(filePath)
        xmlElement = xmlTree.getroot()

        # Inspect xml root element
        #
        if xmlElement.tag == 'Menu':

            parent = self.getMainMenuBar()
            topLevelMenuItem = self.createMenuItem(xmlElement, parent=parent)

            return topLevelMenuItem

        else:

            raise TypeError('createMenuFromFile() expects Menu tag for root element (%s given)!' % xmlElement.tag)
