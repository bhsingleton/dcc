import pymxs

from collections import deque
from dcc.abstract import afnmenubar

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMenubar(afnmenubar.AFnMenubar):
    """
    Overload of AFnMenubar that implements the menubar interface for 3ds Max.
    """

    __slots__ = ()

    def getMainMenubar(self):
        """
        Returns the main menu bar.

        :rtype: pymxs.MXSWrapperBase
        """

        return pymxs.runtime.MenuMan.getMainMenuBar()

    def iterMenus(self):
        """
        Returns a generator that yields main menus.

        :rtype: iter
        """

        menuBar = self.getMainMenubar()
        return self.iterSubMenus(menuBar)

    def iterInternalMenus(self):
        """
        Returns a generator that yields internal menus.

        :rtype: iter
        """

        numMenus = pymxs.runtime.MenuMan.numMenus()

        for i in range(1, numMenus + 1, 1):

            yield pymxs.runtime.MenuMan.getMenu(i)

    def getMenuTitle(self, menu, stripAmpersand=False):
        """
        Returns the title of the given menu.

        :type menu: Any
        :type stripAmpersand: bool
        :rtype: str
        """

        title = menu.getTitle()  # type: str

        if stripAmpersand:

            return title.strip('&')

        else:

            return title

    def iterSubMenus(self, menu):
        """
        Returns a generator that yields sub menus.

        :type menu: pymxs.MXSWrapperBase
        :rtype: iter
        """

        numItems = menu.numItems()

        for i in range(1, numItems + 1, 1):

            item = menu.getItem(i)
            subMenu = item.getSubMenu()

            if isinstance(subMenu, pymxs.MXSWrapperBase):

                yield subMenu

            else:

                continue

    def walkSubMenus(self, menu):
        """
        Returns a generator that yields all sub menus.

        :type menu: pymxs.MXSWrapperBase
        :rtype: iter
        """

        queue = deque(self.iterSubMenus(menu))

        while len(queue):

            subMenu = queue.popleft()
            yield subMenu

            queue.extend(list(self.iterSubMenus(subMenu)))

    def removeMenuItems(self, menu):
        """
        Removes all the items from the given menu.

        :type menu: pymxs.MXSWrapperBase
        :rtype: None
        """

        # Remove sub menu items
        #
        numItems = menu.numItems()

        for i in range(1, numItems + 1, 1):

            menu.removeItemByPosition(i)

    def removeMenu(self, menu):
        """
        Removes the given menu from the menubar.

        :type menu: pymxs.MXSWrapperBase
        :rtype: None
        """

        # Iterate through sub menus
        #
        subMenus = list(self.walkSubMenus(menu))

        for subMenu in reversed(subMenus):

            self.removeMenuItems(subMenu)
            pymxs.runtime.MenuMan.unRegisterMenu(subMenu)

        # Un-register top-level menu
        # Refresh menubar
        #
        pymxs.runtime.MenuMan.unRegisterMenu(menu)
        pymxs.runtime.MenuMan.updateMenuBar()

    def removeMenusByTitle(self, title):
        """
        Removes any menus with the matching title.
        This overload will also remove internal menus!

        :type title: str
        :rtype: None
        """

        menus = [x for x in self.iterInternalMenus() if x.getTitle().strip('&') == title]

        for menu in menus:

            self.removeMenu(menu)

    def default(self, xmlElement, insertAt=-1, parent=None):
        """
        Returns a menu item using the supplied xml element.

        :type xmlElement: etree.Element
        :type insertAt: int
        :type parent: pymxs.MXSWrapperBase
        :rtype: pymxs.MXSWrapperBase
        """

        # Evaluate xml element tag
        #
        if xmlElement.tag == 'Menu':

            # Create new menu
            #
            title = xmlElement.get('title', default='')

            log.info('Creating menu: %s' % title)
            menu = pymxs.runtime.MenuMan.createMenu(title)

            # Parent sub-menu item
            #
            if isinstance(parent, pymxs.MXSWrapperBase):

                subMenuItem = pymxs.runtime.MenuMan.createSubMenuItem(title, menu)
                parent.addItem(subMenuItem, insertAt)

            # Append child menu items
            #
            for child in iter(xmlElement):

                self.default(child, parent=menu)

            return menu

        elif xmlElement.tag == 'Action':

            # Create new action item
            #
            macro = xmlElement.get('macro', default='')
            category = xmlElement.get('category', default='')

            log.info('Creating action item: %s' % macro)
            actionItem = pymxs.runtime.MenuMan.createActionItem(macro, category)

            # Assign custom title
            #
            title = xmlElement.get('text', default='')
            actionItem.setTitle(title)
            actionItem.setUseCustomTitle(True)

            # Parent action to menu item
            #
            if isinstance(actionItem, pymxs.MXSWrapperBase) and isinstance(parent, pymxs.MXSWrapperBase):

                parent.addItem(actionItem, insertAt)

            return actionItem

        elif xmlElement.tag == 'Separator':

            # Create new separator
            #
            separator = pymxs.runtime.MenuMan.createSeparatorItem()

            if isinstance(parent, pymxs.MXSWrapperBase):

                parent.addItem(separator, insertAt)

            return separator

        else:

            raise TypeError('default() expects a valid xml tag (%s given)!' % xmlElement.tag)

    def loadConfiguration(self, filePath):
        """
        Loads the supplied configuration file onto the main menubar.

        :type filePath: str
        :rtype: Any
        """

        # Call parent method
        #
        super(FnMenubar, self).loadConfiguration(filePath)

        # Update menubar
        #
        pymxs.runtime.MenuMan.updateMenuBar()

    def unloadConfiguration(self, filePath):
        """
        Unloads the supplied configuration file from the main menubar.

        :type filePath: str
        :rtype: Any
        """

        # Call parent method
        #
        super(FnMenubar, self).unloadConfiguration(filePath)

        # Save changes to menubar
        #
        pymxs.runtime.MenuMan.updateMenuBar()

        menuFilePath = pymxs.runtime.MenuMan.getMenuFile()
        pymxs.runtime.MenuMan.saveMenuFile(menuFilePath)
