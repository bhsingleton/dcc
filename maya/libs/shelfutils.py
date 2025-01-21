import os

from maya import cmds as mc, mel
from ...python import stringutils
from ...xml import xmlutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getTopLevelShelf():
    """
    Returns the top-level Maya shelf.

    :rtype: str
    """

    return mel.eval("$tmp=$gShelfTopLevel")


def createShelfTab(xmlElement, parent=None):
    """
    Creates a shelf tab from the supplied xml element.

    :type xmlElement: xml.eTree.ElementTree.Element
    :type parent: str
    :rtype: str
    """

    # Check if a parent was supplied
    #
    if stringutils.isNullOrEmpty(parent):

        parent = getTopLevelShelf()

    # Create new shelf tab
    #
    return mc.shelfLayout(xmlElement.attrib['title'], parent=parent)


def createShelfButton(xmlElement, parent=None):
    """
    Creates a shelf button from the supplied xml element.

    :type xmlElement: xml.eTree.ElementTree.Element
    :type parent: str
    :rtype: str
    """

    # Create shelf button from flags
    #
    flags = {child.attrib['name']: stringutils.eval(child.attrib['value']) for child in xmlElement if child.tag == 'Flag'}
    shelfButton = mc.shelfButton(parent=parent, **flags)

    # Check if any menu-items exist
    #
    xmlElements = [child for child in xmlElement if child.tag == 'MenuItem']

    for child in xmlElements:

        flags = {'menuItem': (child.attrib['name'], child.attrib['command'])}
        isPython = stringutils.eval(child.attrib.get('python', False))

        if isPython:

            flags['menuItemPython'] = 0

        mc.shelfButton(shelfButton, edit=True, **flags)

    return shelfButton


def createShelfSeparator(xmlElement, parent=None):
    """
    Creates a shelf separator from the supplied xml element.

    :type xmlElement: xml.eTree.ElementTree.Element
    :type parent: str
    :rtype: str
    """

    return mc.separator(
        enable=True,
        width=34,
        height=35,
        manage=True,
        visible=True,
        enableBackground=False,
        style='shelf',
        backgroundColor=(0, 0, 0),
        highlightColor=(0.321569, 0.521569, 0.65098),
        horizontal=False,
        parent=parent
    )


def clearShelfTab(tab):
    """
    Removes all children from the specified shelf tab.

    :type tab: str
    :rtype: None
    """

    # Check if shelf has children
    #
    children = mc.shelfLayout(tab, query=True, childArray=True)

    if stringutils.isNullOrEmpty(children):

        return

    # Delete children
    #
    for child in children:

        mc.deleteUI(child)


def getShelfTabByName(name, parent=None):
    """
    Returns the shelf tab with the associated name.
    If no tab exists then none is returned!

    :type name: str
    :type parent: str
    :rtype: Union[str, None]
    """

    # Check if a parent was supplied
    #
    if stringutils.isNullOrEmpty(parent):

        parent = getTopLevelShelf()

    # Get shelf tabs
    #
    shelves = mc.shelfTabLayout(parent, query=True, childArray=True)

    if stringutils.isNullOrEmpty(shelves):

        return None

    # Search for tab with name
    #
    absoluteName = name.replace(' ', '_')

    found = [shelf for shelf in shelves if shelf == absoluteName]
    numFound = len(found)

    if numFound == 0:

        return None

    elif numFound == 1:

        return found[0]

    else:

        raise TypeError(f'getShelfTabByName() expects a unique name ({numFound} found)!')


def loadXmlConfiguration(filePath, parent=None):
    """
    Loads the shelf from the supplied config file.

    :type filePath: str
    :type parent: Union[str, None]
    :rtype: None
    """

    # Check if a parent was supplied
    #
    if stringutils.isNullOrEmpty(parent):

        parent = getTopLevelShelf()

    # Load configuration file
    #
    xmlTree = xmlutils.cParse(filePath)
    rootElement = xmlTree.getroot()

    # Check if tab exists
    # If not, then create a new tab
    #
    tab = getShelfTabByName(rootElement.attrib['title'], parent=parent)

    if tab is None:

        tab = createShelfTab(rootElement, parent=parent)

    else:

        clearShelfTab(tab)

    # Iterate through xml elements
    #
    for element in rootElement:

        # Evaluate element tag
        #
        if element.tag == 'ShelfButton':

            createShelfButton(element, parent=tab)

        elif element.tag == 'Separator':

            createShelfSeparator(element, parent=tab)

        else:

            raise TypeError(f'loadShelfTab() expects a valid XML tag ({element.tag} given)')

    return parent
