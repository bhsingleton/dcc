import os
import json

from maya.api import OpenMaya as om
from six import string_types
from . import dagutils, iterEnumMembers
from ..json import mattributeparser
from ..decorators.undo import commit

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


NUMERIC_TYPES = {value: key for (key, value) in iterEnumMembers(om.MFnNumericData)}
ATTR_TYPES = {value: key for (key, value) in iterEnumMembers(om.MFnData)}
UNIT_TYPES = {value: key for (key, value) in iterEnumMembers(om.MFnUnitAttribute)}
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'schemas')
ATTRIBUTES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'attributes')


def addAttribute(node, **kwargs):
    """
    Adds an attribute to the supplied node with the specified parameters.
    Do not use this method with compound attributes!
    Create the attribute then add the children before committing to the node!

    :type node: om.MObject
    :key longName: str
    :key shortName: str
    :key attributeType: str
    :key modifier: Union[om.MDGModifier, None]
    :rtype: om.MObject
    """

    # Check if a modifier was supplied
    #
    modifier = kwargs.get('modifier', None)

    if modifier is None:

        modifier = om.MDGModifier()

    # Check if attribute already exists
    #
    node = dagutils.getMObject(node)
    fnDependNode = om.MFnDependencyNode(node)

    attributeName = kwargs.get('longName', kwargs.get('shortName', ''))

    if not fnDependNode.hasAttribute(attributeName):

        # Add attribute to node
        #
        attribute = createAttribute(**kwargs)
        modifier.addAttribute(node, attribute)

        # Cache and execute modifier
        #
        commit(modifier.doIt, modifier.undoIt)
        modifier.doIt()

        return attribute

    else:

        return fnDependNode.attribute(attributeName)


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


def applyAttributeTemplate(node, filePath, **kwargs):
    """
    Applies an attribute template to the supplied dependency node.

    :type node: Union[str, om.MObject]
    :type filePath: str
    :rtype: List[om.MObject]
    """

    # Check if a modifier was supplied
    #
    modifier = kwargs.get('modifier', None)

    if modifier is None:

        modifier = om.MDGModifier()

    # Deserialize attribute template
    #
    node = dagutils.getMObject(node)
    attributes = []

    with open(filePath, 'r') as jsonFile:

        attributes = json.load(jsonFile, cls=mattributeparser.MAttributeDecoder, node=node)

    # Iterate through attributes
    #
    fnDependNode = om.MFnDependencyNode(node)
    fnAttribute = om.MFnAttribute()

    for attribute in attributes:

        fnAttribute.setObject(attribute)

        if not fnDependNode.hasAttribute(fnAttribute.name):

            modifier.addAttribute(node, attribute)

        else:

            continue

    # Cache and execute modifier
    #
    commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()

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


def findAttribute(*args):
    """
    Returns the attribute associated with the supplied arguments.

    :type args: Union[str, Tuple[om.MObject, str], om.MPlug]
    :rtype: om.MObject
    """

    # Evaluate number of arguments
    #
    numArgs = len(args)

    if numArgs == 1:

        # Evaluate argument
        #
        arg = args[0]

        if isinstance(arg, om.MObject):

            return arg

        elif isinstance(arg, om.MPlug):

            return arg.attribute()

        elif isinstance(arg, string_types):

            node, plug = dagutils.getMObject(arg)
            return plug.attribute()

        else:

            raise TypeError('findAttribute() expects either a str of MPlug (%s given)!' % type(arg).__name__)

    elif numArgs == 2:

        # Lookup attribute from node
        #
        node, attribute = args

        if isinstance(node, om.MObject) and isinstance(attribute, string_types):

            return om.MFnDependencyNode(node).attribute(attribute)

        else:

            raise TypeError('findAttribute() expects an MObject and str!')

    else:

        raise TypeError('findAttribute() expects 1-2 arguments (%s given)!' % numArgs)


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


def iterAttributes(dependNode, userDefined=False):
    """
    Returns a generator that yields attributes.

    :type dependNode: om.MObject
    :type userDefined: bool
    :rtype: Iterator[om.MObject]
    """

    # Iterate through attributes
    #
    fnDependNode = om.MFnDependencyNode(dependNode)
    numAttributes = fnDependNode.attributeCount()

    fnAttribute = om.MFnAttribute()

    for i in range(numAttributes):

        # Check if attribute is dynamic
        #
        attribute = fnDependNode.attribute(i)
        fnAttribute.setObject(attribute)

        if userDefined and not fnAttribute.dynamic:

            continue

        yield attribute


def iterTopLevelAttributes(dependNode, userDefined=False):
    """
    Returns a generator that yields top-level attributes.

    :type dependNode: om.MObject
    :type userDefined: bool
    :rtype: Iterator[om.MObject]
    """

    # Iterate through attributes
    #
    fnAttribute = om.MFnAttribute()

    for attribute in iterAttributes(dependNode, userDefined=userDefined):

        # Check if attribute has a parent
        #
        fnAttribute.setObject(attribute)
        isTopLevel = fnAttribute.parent.isNull()

        if isTopLevel:

            yield attribute

        else:

            continue


def iterAttributeNames(dependNode, shortNames=False, topLevel=False, userDefined=False):
    """
    Returns a generator that yields attribute names.

    :type dependNode: om.MObject
    :type shortNames: bool
    :type topLevel: bool
    :type userDefined: bool
    :rtype: iter
    """

    # Iterate through attributes
    #
    generator = iterTopLevelAttributes if topLevel else iterAttributes
    fnAttribute = om.MFnAttribute()

    for attribute in generator(dependNode, userDefined=userDefined):

        # Check if short name should be yielded
        #
        fnAttribute.setObject(attribute)

        if shortNames:

            yield fnAttribute.shortName

        else:

            yield fnAttribute.name


def getAttributeTypeName(attribute):
    """
    Returns the type name for the supplied attribute.
    This is the string that correlates with setAttr commands.

    :type attribute: Union[om.MObject, om.MPlug]
    :rtype: str
    """

    # Inspect supplied argument
    #
    if isinstance(attribute, om.MPlug):

        attribute = attribute.attribute()

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


def getDefaultValue(attribute, convertUnits=False):
    """
    Returns the default value from the supplied attribute.

    :type attribute: Union[om.MObject, om.MPlug]
    :type convertUnits: bool
    :rtype: Union[bool, int, float, None]
    """

    # Inspect supplied argument
    #
    if isinstance(attribute, om.MPlug):

        attribute = attribute.attribute()

    # Evaluate attribute type
    #
    value = None

    if attribute.hasFn(om.MFn.kNumericAttribute):

        value = om.MFnNumericAttribute(attribute).default

    elif attribute.hasFn(om.MFn.kUnitAttribute):

        value = om.MFnUnitAttribute(attribute).default

    elif attribute.hasFn(om.MFn.kEnumAttribute):

        value = om.MFnEnumAttribute(attribute).default

    else:

        pass

    # Check if units require converting
    #
    if convertUnits and isinstance(value, (om.MDistance, om.MAngle, om.MTime)):

        cls = type(value)
        uiUnit = cls.uiUnit()

        return value.asUnits(uiUnit)

    else:

        return value
