import pymxs
import os

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def maxscriptToString(filePath):
    """
    Converts the contents of a maxscript file to an executable string.

    :type filePath: str
    :rtype: str
    """

    # Check if file exists
    #
    if not os.path.exists(filePath):

        return

    # Open maxscript file
    #
    string = ''

    with open(filePath, 'rt') as maxscriptFile:

        # Read lines from file
        #
        for line in maxscriptFile:

            # Check number of characters
            # Skip if there are none
            #
            charCount = len(line)

            if charCount == 0:

                continue

            # Append characters to string
            #
            string += '{line}\r'.format(line=line)

    return string


def loadDefinition(filePath):
    """
    Loads an attribute definition from the supplied maxscript file.
    Be sure to check if the definition exists before calling this method!

    :type filePath: str
    :rtype: pymxs.runtime.AttributeDef
    """

    return pymxs.runtime.execute(maxscriptToString(filePath))


def iterDefinitions(obj, baseObject=True):
    """
    Returns a generator that yields attribute definitions from the supplied node.

    :type obj: pymxs.runtime.MXSWrapperBase
    :type baseObject: bool
    :rtype: iter
    """

    definitionCount = pymxs.runtime.CustAttributes.count(obj, baseObject=baseObject)

    for i in range(definitionCount):

        yield pymxs.runtime.CustAttributes.get(obj, i + 1)


def doesNodeHaveDefinition(node, name):
    """
    Evaluates if an attribute definition with the specified name exists.

    :type node: pymxs.runtime.Node
    :type name: str
    :rtype: bool
    """

    return len([x for x in iterDefinitions(node) if x.name == name]) > 0


def doesSceneHaveDefinition(name):
    """
    Evaluates if an attribute definition with the specified name exists.

    :type name: str
    :rtype: bool
    """

    return len([x for x in pymxs.runtime.CustAttributes.getSceneDefs() if x.name == name]) > 0


def getSceneDefinitionByName(name):
    """
    Returns a attribute definition with the specified name.
    If no definition is found then none is returned!
    If multiple definitions are found then a TypeError is raised!

    :type name: str
    :rtype: pymxs.runtime.AttributeDef
    """

    found = [x for x in pymxs.runtime.CustAttributes.getSceneDefs() if x.name == name]
    numFound = len(found)

    if found == 0:

        return None

    elif found == 1:

        return found[0]

    else:

        raise TypeError('Multiple attribute definitions found with the name: %s' % name)


def getNodesByDefinition(definition):
    pass


def deleteDefinitionsByName():

    pass
