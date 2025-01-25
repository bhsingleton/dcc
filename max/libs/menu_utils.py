"""
This module provides menu utilities prior to 3dsMax 2025!
"""
import os
import pymxs

from collections import deque
from ...python import stringutils
from ...xml import xmlutils
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getMainMenubar():
    """
    Returns the main menu bar.

    :rtype: pymxs.MXSWrapperBase
    """

    return pymxs.runtime.MenuMan.getMainMenuBar()


def iterSubMenus(menu):
    """
    Returns a generator that yields sub-menus from the supplied menu.

    :type menu: pymxs.MXSWrapperBase
    :rtype: Iterator[pymxs.MXSWrapperBase]
    """

    numItems = menu.numItems()

    for i in inclusiveRange(1, numItems, 1):

        item = menu.getItem(i)
        subMenu = item.getSubMenu()

        if isinstance(subMenu, pymxs.MXSWrapperBase):

            yield subMenu

        else:

            continue


def iterInternalMenus():
    """
    Returns a generator that yields internal menus from the menu manager.

    :rtype: Iterator[pymxs.MXSWrapperBase]
    """

    numMenus = pymxs.runtime.MenuMan.numMenus()

    for i in inclusiveRange(1, numMenus, 1):

        yield pymxs.runtime.MenuMan.getMenu(i)


def walkMenus(menu):
    """
    Returns a generator that yields all sub menus.

    :type menu: pymxs.MXSWrapperBase
    :rtype: iter
    """

    queue = deque(iterSubMenus(menu))

    while len(queue):

        subMenu = queue.popleft()
        yield subMenu

        queue.extend(list(iterSubMenus(subMenu)))


def iterTopLevelMenus():
    """
    Returns a generator that yields top-level menus from the main menubar.

    :rtype: Iterator[pymxs.MXSWrapperBase]
    """

    return iterSubMenus(getMainMenubar())


def topLevelMenus():
    """
    Returns a list of top-level menus from the main menubar.

    :rtype: List[pymxs.MXSWrapperBase]
    """

    return list(iterTopLevelMenus())


def topLevelMenuCount():
    """
    Evaluates the number of top-level menus.

    :rtype: int
    """

    return len(topLevelMenus())


def getMenuTitle(menu, stripAmpersand=False):
    """
    Returns the title from the supplied menu.

    :type menu: Any
    :type stripAmpersand: bool
    :rtype: str
    """

    title = menu.getTitle()  # type: str

    if stripAmpersand:

        return title.strip('&')

    else:

        return title


def removeMenuItems(menu):
    """
    Removes all the items from the given menu.

    :type menu: pymxs.MXSWrapperBase
    :rtype: None
    """

    numItems = menu.numItems()

    for i in reversed(list(inclusiveRange(1, numItems, 1))):

        menu.removeItemByPosition(i)


def removeTopLevelMenu(menu):
    """
    Removes the given menu from the menubar.

    :type menu: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Iterate through sub-menus
    #
    subMenus = list(walkMenus(menu))

    for subMenu in reversed(subMenus):

        removeMenuItems(subMenu)
        pymxs.runtime.MenuMan.unRegisterMenu(subMenu)

    # Un-register top-level menu
    # Refresh menubar
    #
    pymxs.runtime.MenuMan.unRegisterMenu(menu)
    pymxs.runtime.MenuMan.updateMenuBar()


def removeTopLevelMenusByTitle(title):
    """
    Removes any top-level menus with the same title.
    This will also cover all internal menus that might not be in use.

    :type title: str
    :rtype: None
    """

    menus = [menu for menu in iterInternalMenus() if getMenuTitle(menu, stripAmpersand=True) == title]

    for menu in reversed(menus):

        removeTopLevelMenu(menu)


def createMenuFromXmlElement(xmlElement, insertAt=-1, parent=None):
    """
    Returns a menu item using the supplied xml element.

    :type xmlElement: xml.etree.Element
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

        log.info(f'Creating menu: {title}')
        menu = pymxs.runtime.MenuMan.createMenu(title)

        # Parent sub-menu item
        #
        if isinstance(parent, pymxs.MXSWrapperBase):

            subMenuItem = pymxs.runtime.MenuMan.createSubMenuItem(title, menu)
            parent.addItem(subMenuItem, insertAt)

        # Append child menu items
        #
        for child in iter(xmlElement):

            createMenuFromXmlElement(child, parent=menu)

        return menu

    elif xmlElement.tag == 'Action':

        # Create new action item
        #
        macro = xmlElement.get('macro', default='')
        category = xmlElement.get('category', default='')

        log.info(f'Creating action item: {macro}')
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

        raise TypeError(f'createMenuFromXmlElement() expects a valid XML tag ({xmlElement.tag} given)!')


def loadXmlConfiguration(filePath):
    """
    Loads the supplied configuration file onto the main menubar.

    :type filePath: str
    :rtype: Any
    """

    # Check if file exists
    #
    if not os.path.exists(filePath):

        log.warning(f'Cannot locate XML configuration: {filePath}')
        return

    # Initialize XML element tree
    # Remove any pre-existing top-level menus
    #
    elementTree = xmlutils.cParse(filePath)
    root = elementTree.getroot()

    title = root.get('title', None)

    if not stringutils.isNullOrEmpty(title):

        removeTopLevelMenusByTitle(title)

    # Create menu layout
    #
    parent = getMainMenubar()
    insertAt = topLevelMenuCount() - 1

    createMenuFromXmlElement(root, insertAt=insertAt, parent=parent)

    # Update menubar
    #
    pymxs.runtime.MenuMan.updateMenuBar()


def unloadXmlConfiguration(filePath):
    """
    Unloads the supplied configuration file from the main menubar.

    :type filePath: str
    :rtype: None
    """

    # Check if file exists
    #
    if not os.path.exists(filePath):

        log.warning(f'Cannot locate XML configuration: {filePath}')
        return

    # Load XML element tree
    # Remove and pre-existing top-level menus
    #
    elementTree = xmlutils.cParse(filePath)
    root = elementTree.getroot()

    title = root.get('title', None)

    if not stringutils.isNullOrEmpty(title):

        removeTopLevelMenusByTitle(title)

    # Save changes to menubar
    #
    pymxs.runtime.MenuMan.updateMenuBar()

    menuFilePath = pymxs.runtime.MenuMan.getMenuFile()
    pymxs.runtime.MenuMan.saveMenuFile(menuFilePath)


def registerTopLevelMenu(creator, deletor):
    """
    Registers a set of create and delete menu functions within 3dsMax's callback system.

    :type creator: Callable[loadXmlConfiguration]
    :type deletor: Callable[unloadXmlConfiguration]
    :rtype: None
    """

    if callable(creator):

        pymxs.runtime.callbacks.addScript(
            pymxs.runtime.Name('welcomeScreenDone'),
            creator,
            persistent=False
        )

    if callable(deletor):

        pymxs.runtime.callbacks.addScript(
            pymxs.runtime.Name('preSystemShutdown'),
            deletor,
            persistent=False
        )
