from maya import cmds as mc
from maya import mel
from functools import partial
from dcc.abstract import afnmenubar
from dcc.python import stringutils

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

        return mel.eval('$temp = $gMainWindow;')

    def iterMenus(self):
        """
        Returns a generator that yields main menus.

        :rtype: iter
        """

        mainWindow = self.getMainMenubar()
        menus = mc.window(mainWindow, query=True, menuArray=True)

        if menus is not None:

            return iter(menus)

        else:

            return iter([])

    def getMenuTitle(self, menu, stripAmpersand=False):
        """
        Returns the title of the given menu.

        :type menu: Any
        :type stripAmpersand: bool
        :rtype: str
        """

        title = mc.menu(menu, query=True, label=True)  # type: str

        if stripAmpersand:

            return title.strip('&')

        else:

            return title

    def removeMenu(self, menu):
        """
        Removes the given menu from the menubar.

        :type menu: Any
        :rtype: None
        """

        if mc.menu(menu, query=True, exists=True):

            mc.deleteUI(menu, menu=True)

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
            label = xmlElement.get('title', default='')
            objectName = stringutils.slugify(label)

            menu = None

            if mc.objectTypeUI(parent, isType='menu'):

                menu = mc.menuItem(objectName, label=label, subMenu=True, parent=parent)

            else:

                menu = mc.menu(objectName, label=label, tearOff=True, parent=parent)

            # Append child menu items
            #
            for child in iter(xmlElement):

                self.default(child, parent=menu)

            return menu

        elif xmlElement.tag == 'Action':

            # Create new action
            #
            label = xmlElement.get('text', default='')
            objectName = stringutils.slugify(label)
            command = xmlElement.get('command', default='')

            return mc.menuItem(objectName, label=label, command=command, parent=parent)

        elif xmlElement.tag == 'Separator':

            return mc.menuItem(divider=True, parent=parent)

        else:

            raise TypeError('default() expects a valid xml tag (%s given)!' % xmlElement.tag)
