import pymxs

from ..abstract import afnmenu

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMenu(afnmenu.AFnMenu):
    """
    Overload of AFnMenu that provides methods for creating menu interfaces in 3ds Max.
    """

    __slots__ = ()

    def createMenuItem(self, xmlElement, parent=None):
        """
        Returns a new menu item using the supplied xml element.

        :type xmlElement: xml.etree.ElementTree.Element
        :type parent: pymxs.MXSWrapperBase
        :rtype: pymxs.MXSWrapperBase
        """

        # Query menu tag to determine menu type
        #
        title = xmlElement.get('title', '')
        log.info('Creating menu item: %s' % title)

        if xmlElement.tag == 'Menu':

            # Check if submenu already exists
            # If it does then reuse it
            #
            menuItem = pymxs.runtime.menuMan.findMenu(title)

            if menuItem is not None:

                # Remove all child items
                # Make sure to do this in reverse!
                #
                numItems = menuItem.numItems()

                for i in range(numItems, 0, -1):

                    menuItem.removeItemByPosition(i)

            else:

                # Create new menu item
                #
                menuItem = pymxs.runtime.menuMan.createMenu(title)
                subMenuItem = pymxs.runtime.menuMan.createSubMenuItem(title, menuItem)

                parent.addItem(subMenuItem, -1)

            # Create child menu items
            #
            menuItems = [self.createMenuItem(child, parent=menuItem) for child in iter(xmlElement)]
            return menuItem

        elif xmlElement.tag == 'MenuItem':

            # Create menu item using action
            # If the action doesn't exist then the menu item will not be created!
            #
            action = xmlElement.get('action', '')
            category = xmlElement.get('category', '')

            actionItem = pymxs.runtime.menuMan.createActionItem(action, category)

            if actionItem is not None:

                # Enable custom title
                # Otherwise Max will use the tooltip in its place...
                #
                actionItem.setUseCustomTitle(True)
                actionItem.setTitle(title)

                parent.addItem(actionItem, -1)
                return actionItem

            else:

                raise TypeError('createMenuItem() expects a valid macroscript action (%s given)!' % action)

        elif xmlElement.tag == 'Separator':

            # Create separator
            #
            separator = pymxs.runtime.menuMan.createSeparatorItem()
            parent.addItem(separator, -1)

            return separator

        else:

            raise TypeError('createMenuItem() expects a valid xml tag (%s found)!' % xmlElement.tag)

    def getMainMenuBar(self):
        """
        Returns the main menu bar to parent new menu items to.

        :rtype: pymxs.runtime.MXSWrapperBase
        """

        return pymxs.runtime.menuMan.getMainMenuBar()

    def createMenuFromFile(self, filePath):
        """
        Creates a menu system from the supplied xml file configuration.
        This method has been overloaded to force max to update upon completion.

        :type filePath: str
        :rtype: None
        """

        # Call parent method
        #
        topLevelMenuItem = super(FnMenu, self).createMenuFromFile(filePath)

        # Update menu bar to solidify update
        #
        pymxs.runtime.menuMan.updateMenuBar()
        return topLevelMenuItem
