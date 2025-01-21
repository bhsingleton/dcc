import os

from maya import cmds as mc, mel
from functools import partial
from ...python import stringutils
from ...xml import xmlutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getMainMenubar():
    """
    Returns the main menu bar.

    :rtype: str
    """

    return mel.eval('$temp = $gMainWindow;')


def iterTopLevelMenus():
    """
    Returns a generator that yields main menus.

    :rtype: iter
    """

    mainWindow = getMainMenubar()
    menus = mc.window(mainWindow, query=True, menuArray=True)

    if not stringutils.isNullOrEmpty(menus):

        return iter(menus)

    else:

        return iter([])


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


def findTopLevelMenusByTitle(title):
    """
    Returns a list of top-level menus with the given title.

    :type title: str
    :rtype: List[str]
    """

    return [menu for menu in iterTopLevelMenus() if getMenuTitle(menu, stripAmpersand=True) == title]


def removeMenu(menu):
    """
    Removes the given menu from the menubar.

    :type menu: Any
    :rtype: None
    """

    if mc.menu(menu, query=True, exists=True):

        mc.deleteUI(menu, menu=True)


def removeTopLevelMenusByTitle(title):
    """
    Removes any top-level menus with the same title.

    :type title: str
    :rtype: None
    """

    menus = findTopLevelMenusByTitle(title)

    for menu in menus:

        removeMenu(menu)


def createMenuFromXmlElement(xmlElement, parent=None):
    """
    Returns a menu item using the supplied xml element.

    :type xmlElement: xml.etree.Element
    :type parent: str
    :rtype: str
    """

    # Evaluate XML element tag
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

            createMenuFromXmlElement(child, parent=menu)

        return menu

    elif xmlElement.tag == 'Action':

        # Create new action
        #
        label = xmlElement.get('text', default='')
        objectName = stringutils.slugify(label)
        command = xmlElement.get('command', default='')
        sourceType = xmlElement.get('sourceType', default='python')

        return mc.menuItem(objectName, label=label, command=command, sourceType=sourceType, parent=parent)

    elif xmlElement.tag == 'Separator':

        return mc.menuItem(divider=True, parent=parent)

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

    # Load XML element tree
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
    createMenuFromXmlElement(root, parent=parent)
