"""
This module provides menu utilities for 3dsMax 2025 and above!
"""
import pymxs

from . import macroutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


menuMan = None  # This is only defined after you register a #cuiRegisterMenus callback!


def titleize(string):
    """
    Converts the supplied macro name into a title.

    :type string: str
    :rtype: str
    """

    return ''.join([f' {char}' if (i > 0 and char.isupper()) else char for (i, char) in enumerate(string)])


def findTopLevelMenuByTitle(title):
    """
    Returns the top-level menu with the specified title.

    :type title: str
    :rtype: Union[str, None]
    """

    global menuMan

    subMenus = [menuItem.subMenu for menuItem in menuMan.mainMenuBar.menuItems if menuItem.subMenu is not None]
    found = [subMenu for subMenu in subMenus if subMenu.title.replace('&', '') == title]
    numFound = len(found)

    if numFound == 0:

        return None

    elif numFound == 1:

        return found[0]

    else:

        raise TypeError(f'findTopLevelMenuByTitle() expects a unique title ({numFound} found)!')


def removeTopLevelMenuByPersistentActionId(persistentActionId):
    """
    Removes the top-level menu with the specified title.

    :type title: str
    :rtype: None
    """

    global menuMan

    macroSpec = macroutils.findMacroByPersistentActionId(persistentActionId)
    title = titleize(macroSpec.name)

    subMenu = findTopLevelMenuByTitle(title)

    if subMenu is not None:

        log.info(f'Removing top level menu: {title}')
        menuMan.mainMenuBar.deleteItem(subMenu.id)


def createTopLevelMenuByPersistentActionId(persistentActionId):
    """
    Creates a top-level menu from the specified persistent action id.
    Persistent action IDs are formatted by: "{macroName}`{nonLocalizedCategory}"

    :type persistentActionId: str
    :rtype: None
    """

    # Update menu manager global
    #
    global menuMan
    menuMan = pymxs.runtime.callbacks.notificationParam()

    # Remove any pre-existing menus
    #
    removeTopLevelMenuByPersistentActionId(persistentActionId)

    # Create menu
    #
    menuGuid = pymxs.runtime.genGUID()
    helpMenu = findTopLevelMenuByTitle('Help')

    menuMan.mainMenuBar.createAction(
        menuGuid,
        macroutils.ACTION_TABLE_ID,
        persistentActionId,
        beforeId=helpMenu.id
    )


def registerTopLevelMenu(creator, deletor):
    """
    Registers a set of create and delete menu functions within 3dsMax's callback system.

    :type creator: Callable[createMenuFromAction]
    :type deletor: Callable[removeTopLevelMenuByTitle]
    :rtype: None
    """

    if callable(creator):

        pymxs.runtime.callbacks.addScript(
            pymxs.runtime.Name('cuiRegisterMenus'),
            creator,
            persistent=False
        )

    if callable(deletor):

        pymxs.runtime.callbacks.addScript(
            pymxs.runtime.Name('preSystemShutdown'),
            deletor,
            persistent=False
        )
