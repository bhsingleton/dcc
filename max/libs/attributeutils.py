import pymxs
import os

from itertools import chain
from collections import namedtuple
from dcc.max.libs import modifierutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


ParamBlockDefinition = namedtuple('ParamBlockDefinition', ['name', 'id', 'ref_no', 'keyword_params', 'parameters'])


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


def iterSceneDefinitions():
    """
    Returns a generator that yields attribute definitions from the scene.

    :rtype: iter
    """

    return iter(pymxs.runtime.CustAttributes.getSceneDefs())


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

    return len([x for x in iterSceneDefinitions() if x.name == name]) > 0


def getSceneDefinitionByName(name):
    """
    Returns a attribute definition with the specified name.
    If no definition is found then none is returned!
    If multiple definitions are found then a TypeError is raised!

    :type name: str
    :rtype: pymxs.runtime.AttributeDef
    """

    found = [x for x in iterSceneDefinitions() if x.name == name]
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


def iterParameterBlockDefinitions(definition):
    """
    Returns a generator that yields parameter block definitions.
    These parameters are yielded as: {paramName}, {paramSpecs}

    :rtype: iter
    """

    # Iterate through parameter blocks
    #
    paramBlocks = pymxs.runtime.CustAttributes.getPBlockDefs(definition)

    for paramBlock in paramBlocks:

        # Un-pack parameter block
        #
        name, index, ref_no, keyword_params = paramBlock[0], paramBlock[1], paramBlock[2], paramBlock[3]
        log.debug('Param Block:: {"name": %s, "id": %s, "ref_no": %s, "keyword_params": %s}' % (name, index, ref_no, keyword_params))

        numItems = len(paramBlock)
        parameters = [(paramBlock[i][0], paramBlock[i][0]) for i in range(4, numItems, 1)]

        yield ParamBlockDefinition(name=name, id=index, ref_no=ref_no, keyword_params=keyword_params, parameters=parameters)


def doesDefinitionHaveParameter(definition, name):
    """
    Evaluates if the supplied definition has a parameter with the given name.

    :type definition: pymxs.runtime.AttributeDef
    :type name: str
    :rtype: bool
    """

    return any(chain(*[[str(parameter.name) == name for parameter in paramBlock.parameters] for paramBlock in iterParameterBlockDefinitions(definition)]))


def iterDefinitionsWithParameter(name):
    """
    Returns a generator that yields definitions with the specified parameter.

    :type name: str
    :rtype: iter
    """

    # Iterate through scene definitions
    #
    for definition in iterSceneDefinitions():

        # Check if definition has parameter
        #
        if doesDefinitionHaveParameter(definition, name):

            yield definition

        else:

            continue


def getNodesWithParameter(name):
    """
    Returns a list of nodes with the given parameter name.

    :type name: str
    :rtype: List[pymxs.MXSWrapperBase]
    """

    return list(chain(*[list(iterNodesFromDefinition(x)) for x in iterDefinitionsWithParameter(name)]))


def clearDay1RefCA():
    """
    Removes all the day1RefCA definitions from the scene.

    :rtype: None
    """

    # Iterate through scene definitions
    #
    for definition in iterSceneDefinitions():

        # Check if this is a day1RefCA definition
        #
        name = str(definition.name)

        if name != 'day1RefCA':

            continue

        # Check if definition is in use
        #
        nodes = list(iterNodesFromDefinition(definition))
        numNodes = len(nodes)

        if numNodes == 0:

            log.info('Deleting attribute definition: %s' % definition)
            pymxs.runtime.CustAttributes.deleteDef(definition)

        else:

            continue
