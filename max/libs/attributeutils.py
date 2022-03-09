import pymxs
import os

from dcc.max.libs import modifierutils

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


def iterNodesFromDefinition(definition):
    """
    Returns a list of nodes that use the supplied definition.

    :type definition: pymxs.runtime.AttributeDef
    :rtype: List[pymxs.MXSWrapperBase]
    """

    # Iterate through instances
    #
    instances = pymxs.runtime.CustAttributes.getDefInstances(definition)

    for instance in instances:

        # Get nodes from dependents
        #
        dependents = pymxs.runtime.Refs.dependents(instance)

        for dependent in dependents:

            # Evaluate dependent type
            #
            if pymxs.runtime.isValidNode(dependent):

                yield dependent

            elif modifierutils.isValidModifier(dependent):

                yield modifierutils.getNodeFromModifier(dependent)

            else:

                continue


def doesDefinitionHaveParameter(definition, name):
    """
    Evaluates if the supplied definition has a parameter with the given name.

    :type definition: pymxs.runtime.AttributeDef
    :type name: str
    :rtype: bool
    """

    return any(str(paramName) == name for (paramName, paramSpecs) in pymxs.runtime.CustAttributes.getPBlockDefs(definition))


def getNodesWithParameter(name):
    """
    Returns a list of nodes with the given parameter name.

    :type name: str
    :rtype: List[pymxs.MXSWrapperBase]
    """

    # Iterate through scene definitions
    #
    sceneDefinitions = pymxs.runtime.CustAttributes.getSceneDefs()
    nodes = []

    for definition in sceneDefinitions:

        # Check if definition has parameter
        #
        if doesDefinitionHaveParameter(definition, name):

            dependentNodes = list(iterNodesFromDefinition(definition))
            nodes.extend(dependentNodes)

        else:

            continue

    return list(set(nodes))


def clearDay1RefCA():
    """
    Removes all of the day1RefCA definitions from the scene.

    :rtype: None
    """

    sceneDefinitions = pymxs.runtime.CustAttributes.getSceneDefs()

    for definition in reversed(sceneDefinitions):

        if definition.name == 'day1RefCA':

            log.info('Deleting attribute defintion: %s' % definition)
            pymxs.runtime.CustAttributes.deleteDef(definition)

        else:

            continue
