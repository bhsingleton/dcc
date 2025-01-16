import pymxs
import shlex

from dataclasses import dataclass, fields, replace

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


ACTION_TABLE_ID = 647394  # All macroscript actions share the same table ID!


@dataclass
class MacroSpec(object):
    """
    Dataclass for macroscript specs.
    """

    # region Fields
    id: int = 0
    name: str = ''
    category: str = ''
    internalCategory: str = ''
    filePath: str = ''
    iconPath: str = ''
    iconIndex: int = 0
    # endregion


def dequote(string):
    """
    Removes any surrounding quotes from the supplied string.

    :type string: str
    :rtype: str
    """

    if string.startswith('"'):

        string = string[1:]

    if string.endswith('"'):

        string = string[:-1]

    return string


def iterMacroscripts():
    """
    Returns a generator that yields all macroscript specs.

    :rtype: Iterator[MacroSpec]
    """

    # Send macro specs to string stream
    #
    stream = pymxs.runtime.StringStream('')
    pymxs.runtime.macros.list(to=stream)
    pymxs.runtime.seek(stream, 0)

    # Decompose string stream
    #
    while not pymxs.runtime.eof(stream):

        # Split line
        #
        rawString = pymxs.runtime.readLine(stream)

        strings = shlex.split(rawString)
        numStrings = len(strings)

        if numStrings != 7:

            continue

        # Decompose macro spec
        #
        id = int(strings[0])
        name = dequote(strings[1])
        category = dequote(strings[2])
        internalCategory = dequote(strings[3])
        filePath = dequote(strings[4])
        iconPath = dequote(strings[5])
        iconIndex = int(strings[6])

        yield MacroSpec(
            id=id,
            name=name,
            category=category,
            internalCategory=internalCategory,
            filePath=filePath,
            iconPath=iconPath,
            iconIndex=iconIndex
        )


def listMacroscripts():
    """
    Returns a list of macroscript specs.

    :rtype: List[MacroSpec]
    """

    return list(iterMacroscripts())


def findMacroByPersistentActionId(persistentActionId):
    """
    Returns the macro spec associated with the supplied persistent action ID.

    :type persistentActionId: str
    :rtype: MacroSpec
    """

    name, internalCategory = persistentActionId.split('`')

    found = [macro for macro in iterMacroscripts() if macro.name == name and macro.internalCategory == internalCategory]
    numFound = len(found)

    if numFound == 0:

        return None

    elif numFound == 1:

        return found[0]

    else:

        raise TypeError(f'findMacroByPersistentActionId() expects a unique id ({numFound} found)!')
