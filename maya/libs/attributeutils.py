import os
import json

from maya.api import OpenMaya as om
from six import string_types
from dcc.maya.libs import dagutils
from dcc.maya.json import mattributeparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'schemas')
ATTRIBUTES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'attributes')


def addAttribute(dependNode, **kwargs):
    """
    Adds an attribute to the supplied node with the specified parameters.
    Do not use this method with compound attributes!
    Create the attribute then add the children before committing to the node!

    :type dependNode: om.MObject
    :key longName: str
    :key shortName: str
    :key attributeType: str
    :rtype: om.MObject
    """

    fnDependNode = om.MFnDependencyNode(dependNode)

    attribute = createAttribute(**kwargs)
    fnAttribute = om.MFnAttribute(attribute)

    if not fnDependNode.hasAttribute(fnAttribute.name):

        fnDependNode.addAttribute(attribute)

    return attribute


def createAttribute(**kwargs):
    """
    Creates an attribute based on the supplied parameters.
    This method does not add an attribute to a node, it only creates the attribute definition!

    :key longName: str
    :key shortName: str
    :key attributeType: str
    :rtype: om.MObject
    """

    decoder = mattributeparser.MAttributeDecoder()
    return decoder.default(kwargs)


def applyAttributeTemplate(dependNode, filePath):
    """
    Applies an attribute template to the supplied dependency node.

    :type dependNode: Union[str, om.MObject]
    :type filePath: str
    :rtype: List[om.MObject]
    """

    # Check value type
    #
    if isinstance(dependNode, string_types):

        dependNode = dagutils.getMObject(dependNode)

    # Load json data
    #
    attributes = []

    with open(filePath, 'r') as jsonFile:

        attributes = json.load(jsonFile, cls=mattributeparser.MAttributeDecoder, node=dependNode)

    # Iterate through attributes
    #
    fnDependNode = om.MFnDependencyNode(dependNode)
    fnAttribute = om.MFnAttribute()

    for attribute in attributes:

        fnAttribute.setObject(attribute)

        if not fnDependNode.hasAttribute(fnAttribute.name):

            fnDependNode.addAttribute(attribute)

        else:

            continue

    return attributes


def applyAttributeExtensionTemplate(nodeClass, filePath):
    """
    Applies an attribute template to the supplied node class.

    :type nodeClass: Union[str, om.MNodeClass]
    :type filePath: str
    :rtype: List[om.MObject]
    """

    # Check value type
    #
    if isinstance(nodeClass, string_types):

        nodeClass = om.MNodeClass(nodeClass)

    # Load json data
    #
    attributes = []

    with open(filePath, 'r') as jsonFile:

        attributes = json.load(jsonFile, cls=mattributeparser.MAttributeDecoder, nodeClass=nodeClass)

    # Iterate through attributes
    #
    fnAttribute = om.MFnAttribute()

    for attribute in attributes:

        fnAttribute.setObject(attribute)

        if not nodeClass.hasAttribute(fnAttribute.name):

            nodeClass.addExtensionAttribute(attribute)

        else:

            continue

    return attributes


def getAttributeTypeName(attribute):
    """
    Returns the type name for the supplied attribute.
    This is the string that correlates with setAttr commands.

    :type attribute: om.MObject
    :rtype: str
    """

    # Check attribute type
    #
    if attribute.hasFn(om.MFn.kNumericAttribute):

        fnNumericAttribute = om.MFnNumericAttribute(attribute)
        dataType = NUMERIC_TYPES[fnNumericAttribute.numericType()][1:]  # Strip the 'k' prefix

        if dataType[0].isdigit():

            return '{letter}{name}{digit}'.format(
                letter=dataType[1].lower(),
                name=dataType[2:],
                digit=dataType[0]
            )

        else:

            return '{letter}{name}'.format(
                letter=dataType[0].lower(),
                name=dataType[1:]
            )

    elif attribute.hasFn(om.MFn.kTypedAttribute):

        fnTypedAttribute = om.MFnTypedAttribute(attribute)
        dataType = ATTR_TYPES[fnTypedAttribute.attrType()][1:]  # Strip the 'k' prefix

        return '{letter}{name}'.format(
            letter=dataType[0].lower(),
            name=dataType[1:]
        )

    elif attribute.hasFn(om.MFn.kUnitAttribute):

        fnUnitAttribute = om.MFnUnitAttribute(attribute)
        dataType = UNIT_TYPES[fnUnitAttribute.unitType()][1:]  # Strip the 'k' prefix

        return '{letter}{name}'.format(
            letter=dataType[0].lower(),
            name=dataType[1:]
        )

    else:

        return '{letter}{name}'.format(
            letter=attribute.apiTypeStr[1].lower(),
            name=attribute.apiTypeStr[2:-9]  # Strip the 'Attribute' suffix
        )


def iterParents(attribute):
    """
    Returns a generator that yields the parents from the supplied attribute.

    :type attribute: om.MObject
    :rtype: iter
    """

    fnAttribute = om.MFnAttribute(attribute)
    current = fnAttribute.parent

    while not current.isNull():

        yield current

        fnAttribute.setObject(current)
        current = fnAttribute.parent


def iterChildren(attribute):
    """
    Returns a generator that yields the children from the supplied attribute.

    :type attribute: om.MObject
    :rtype: iter
    """

    fnAttribute = om.MFnCompoundAttribute(attribute)
    numChildren = fnAttribute.numChildren()

    for i in range(numChildren):

        yield fnAttribute.child(i)


def trace(attribute):
    """
    Returns a generator that yields the all the attributes leading to the supplied attribute.

    :type attribute: om.MObject
    :rtype: iter
    """

    for parent in reversed(list(iterParents(attribute))):

        yield parent

    yield attribute


def iterAttributes(dependNode):
    """
    Returns a generator that yields attributes.

    :type dependNode: om.MObject
    :rtype: iter
    """

    fnDependNode = om.MFnDependencyNode(dependNode)
    numAttributes = fnDependNode.attributeCount()

    for i in range(numAttributes):

        yield fnDependNode.attribute(i)


def iterAttributeNames(dependNode, shortNames=False):
    """
    Returns a generator that yields attribute names.

    :type dependNode: om.MObject
    :type shortNames: bool
    :rtype: iter
    """

    fnAttribute = om.MFnAttribute()

    for attribute in iterAttributes(dependNode):

        fnAttribute.setObject(attribute)

        if shortNames:

            yield fnAttribute.shortName

        else:

            yield fnAttribute.name


def iterEnums(obj):
    """
    Returns a generator that yields Maya enums pairs from the supplied object.

    :type obj: Any
    :rtype: iter
    """

    for (key, value) in obj.__dict__.items():

        if key.startswith('k') and isinstance(value, int):

            yield key, value

        else:

            continue


NUMERIC_TYPES = dict(iterEnums(om.MFnNumericData))
ATTR_TYPES = dict(iterEnums(om.MFnData))
UNIT_TYPES = dict(iterEnums(om.MFnUnitAttribute))
