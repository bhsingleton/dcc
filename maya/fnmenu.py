import maya.cmds as mc

from . import fnqt
from ..abstract import afnmenu

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMenu(afnmenu.AFnMenu):
    """
    Overload of AFnMenu that provides methods for creating menu interfaces in Maya.
    """

    __slots__ = ()

    @staticmethod
    def removeWhitespace(string):
        """
        Removes any whitespace from the supplied string.

        :type string: str
        :rtype: str
        """

        return string.replace(' ', '')

    def createMenuItem(self, xmlElement, parent=None):
        """
        Returns a new menu item using the supplied xml element.

        :type xmlElement: xml.etree.ElementTree.Element
        :type parent: str
        :rtype: str
        """

        # Query menu tag to determine menu type
        #
        label = xmlElement.get('label', default='untitled')

        menuItemName = '{name}MenuItem'.format(name=self.removeWhitespace(label))
        menuItemPath = '{parent}|{menuItem}'.format(parent=parent, menuItem=menuItemName)

        if xmlElement.tag == 'Menu':

            # Check if menu already exists
            # If it does then remove all children and start over
            #
            if mc.menu(menuItemPath, query=True, exists=True):

                log.info('Deleting %s items...' % menuItemPath)
                mc.menu(menuItemPath, edit=True, deleteAllItems=True)

                return

            else:

                tearOff = eval(xmlElement.get('tearOff', default='False'))
                mc.menu(menuItemName, parent=parent, tearOff=tearOff, label=label)

            # Create child menu items
            #
            menuItems = [self.createMenuItem(child, parent=menuItemPath) for child in iter(xmlElement)]
            return menuItemPath

        elif xmlElement.tag == 'MenuItem':

            # Create menu item with command
            #
            command = xmlElement.get('command', default='')
            sourceType = xmlElement.get('sourceType', default='mel')

            return mc.menuItem(menuItemName, parent=parent, label=label, command=command, sourceType=sourceType)

        elif xmlElement.tag == 'Divider':

            # Create divider
            #
            return mc.menuItem(divider=True, parent=parent)

        else:

            raise TypeError('createMenuItem() expects a valid xml tag (%s found)!' % xmlElement.tag)

    def getMainMenuBar(self):
        """
        Returns the main menu bar to parent new menu items to.

        :rtype: pymxs.runtime.MXSWrapperBase
        """

        return fnqt.FnQt().getMainWindow().objectName()
