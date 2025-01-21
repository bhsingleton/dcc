import re

from maya import cmds as mc
from maya.api import OpenMaya as om, OpenMayaAnim as oma
from collections import deque
from six import string_types
from . import dagutils, attributeutils
from ..decorators import undo
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__plug_parser__ = re.compile(r'([a-zA-Z0-9_]+)(?:\[([0-9]+)\])?')


def getApiType(obj):
    """
    Gets the attribute type from the supplied plug.

    :type obj: Union[om.MObject, om.MPlug]
    :rtype: int
    """

    if isinstance(obj, om.MObject):

        return obj.apiType()

    elif isinstance(obj, om.MPlug):

        return obj.attribute().apiType()

    else:

        return om.MFn.kUnknown


def findPlug(node, path):
    """
    Returns the plug derived from the supplied node and string path.
    Unlike the API method `MFnDependencyNode::findPlug` this function supports element and child accessors.
    Partial paths and attribute aliases are also supported!

    :type node: Union[str, om.MObject, om.MDagPath]
    :type path: str
    :rtype: om.MPlug
    """

    # Evaluate supplied node
    #
    node = dagutils.getMObject(node)

    if node.isNull():

        raise TypeError('findPlug() expects a valid node!')

    # Check if path contains an alias
    #
    aliases = getAliases(node)
    alias = aliases.get(path, None)

    if alias is not None:

        log.debug(f'Converting path to alias: {path} > {alias}')
        path = alias

    # Evaluate supplied path
    #
    groups = __plug_parser__.findall(path)
    numGroups = len(groups)

    if numGroups == 0:

        raise TypeError(f'findPlug() expects a valid path ("{path}" given)!')

    # Evaluate if attribute exists
    #
    fnDependNode = om.MFnDependencyNode(node)
    nodeName = fnDependNode.name()

    attributeName = groups[-1][0]
    attribute = fnDependNode.attribute(attributeName)

    if attribute.isNull():

        raise TypeError(f'findPlug() cannot find "{nodeName}.{attributeName}" attribute!')

    # Trace plug path
    #
    attributes = list(attributeutils.trace(attribute))
    indices = {attribute: int(index) for (attribute, index) in groups if not stringutils.isNullOrEmpty(index)}

    fnAttribute = om.MFnAttribute()
    plug = None

    for (i, attribute) in enumerate(attributes):

        # Get next child plug
        #
        if i == 0:

            plug = om.MPlug(node, attribute)

        else:

            plug = plug.child(attribute)

        # Check if plug was indexed
        # Make sure to check both the short and long names!
        #
        fnAttribute.setObject(attribute)
        index = indices.get(fnAttribute.name, indices.get(fnAttribute.shortName, None))

        if index is not None:

            plug = plug.elementByLogicalIndex(index)

        else:

            continue

    return plug


def findPlugIndex(plug, logical=True):
    """
    Returns the index of the supplied plug.
    Unlike the default method this function takes child plugs into consideration.

    :type plug: om.MPlug
    :type logical: bool
    :rtype: Union[int, None]
    """

    # Redundancy check
    #
    if plug.isNull:

        return

    # Evaluate plug type
    #
    if plug.isArray and plug.isElement:

        return plug.logicalIndex() if logical else list(iterElements(plug.parent())).index(plug)

    elif plug.isChild:

        return list(iterChildren(plug.parent())).index(plug)

    else:

        return list(attributeutils.iterTopLevelAttributes(plug.node())).index(plug.attribute())


def findAnyPlug(*args):
    """
    Returns a plug from the supplied arguments.

    :type args: Union[Tuple[Union[str, om.MPlug]], Tuple[Union[str, om.MObject, om.MDagPath], Union[str, om.MObject]]]
    :rtype: om.MPlug
    """

    # Evaluate argument count
    #
    numArgs = len(args)

    if numArgs == 0:

        return om.MPlug()

    elif numArgs == 1:

        # Evaluate argument type
        #
        arg = args[0]

        if isinstance(arg, om.MPlug):

            return arg

        elif isinstance(arg, string_types):

            nodeName, attributeName = arg.split('.', maxsplit=1)
            node = dagutils.getMObject(nodeName)

            return findPlug(node, attributeName)

        else:

            raise TypeError(f'findAnyPlug() expects either a str or MPlug ({type(arg).__name__} given)!')

    else:

        # Evaluate first argument
        #
        node = dagutils.getMObject(args[0])

        if node.isNull():

            return om.MPlug()

        # Evaluate second argument
        #
        attribute = args[1]

        if isinstance(attribute, string_types):

            return findPlug(node, attribute)

        elif isinstance(attribute, om.MObject):

            return om.MPlug(node, attribute)

        else:

            raise TypeError(f'findAnyPlug() expects a str or MObject ({type(attribute).__name__} given)!')


def isConstrained(plug):
    """
    Evaluates if the supplied plug is constrained.

    :type plug: om.MPlug
    :rtype: bool
    """

    # Check if plug has a connection
    #
    if not plug.isDestination:

        return False

    # Evaluate connected node
    #
    node = plug.source().node()
    isConstraint = any(map(node.hasFn, (om.MFn.kConstraint, om.MFn.kPluginConstraintNode)))

    return isConstraint


def isAnimated(plug):
    """
    Evaluates if the supplied plug is animated.

    :type plug: om.MPlug
    :rtype: bool
    """

    # Check if plug has a connection
    #
    if not (plug.isKeyable or plug.isDestination):

        return False

    # Evaluate connected node
    #
    node = plug.source().node()
    fnNode = om.MFnDependencyNode(node)
    classification = fnNode.classification(fnNode.typeName)

    return classification == 'animation' and not isConstrained(plug)  # Constraints are classified under `animation`


def isAnimatable(plug):
    """
    Evaluates if the supplied plug is animatable.

    :type plug: om.MPlug
    :rtype: bool
    """

    # Check if plug is keyable
    #
    if not (plug.isKeyable or plug.isDestination):

        return False

    # Evaluate connections
    # If connected, make sure source node accepts keyframe data!
    #
    if plug.isDestination:

        return isAnimated(plug)

    else:

        return True


def isWritable(plug):
    """
    Evaluates if the supplied plug is writable.

    :type plug: om.MPlug
    :rtype: bool
    """

    # Redundancy check
    #
    if plug.isNull or plug.isLocked:

        return False

    # Evaluate attribute definition
    #
    attribute = plug.attribute()
    fnAttribute = om.MFnAttribute(attribute)

    if not fnAttribute.writable:

        return False

    # Evaluate plug connections
    #
    isConnected = bool(plug.isDestination)
    hasAnimation = isAnimated(plug)

    if hasAnimation:

        return True

    else:

        return not isConnected


def isNumeric(plug):
    """
    Evaluates if the supplied plug is numerical.

    :type plug: om.MPlug
    :rtype: bool
    """

    return any(map(plug.attribute().hasFn, (om.MFn.kNumericAttribute, om.MFn.kUnitAttribute, om.MFn.kEnumAttribute)))


def isCompoundNumeric(plug):
    """
    Evaluates if the supplied plug represents a compound numeric value.

    :type plug: om.MPlug
    :rtype: bool
    """

    if plug.isCompound:

        return all([isNumeric(child) for child in iterChildren(plug)])

    else:

        return False


def isString(plug):
    """
    Evaluates if the supplied plug is a string.

    :type plug: om.MPlug
    :rtype: bool
    """

    attribute = plug.attribute()

    if attribute.hasFn(om.MFn.kTypedAttribute):

        return om.MFnTypedAttribute(attribute).attrType() == om.MFnData.kString

    else:

        return False


def connectPlugs(source, destination, force=False, modifier=None):
    """
    Method used to connect two plugs.
    By default, this method will not break pre-existing connections unless specified.

    :type source: Union[str, om.MPlug]
    :type destination: Union[str, om.MPlug]
    :type force: bool
    :type modifier: Union[om.MDGModifier, None]
    :rtype: None
    """

    # Check plug types
    #
    if not isinstance(source, om.MPlug) or not isinstance(destination, om.MPlug):

        raise TypeError('connectPlugs() expects 2 plugs!')

    # Check if plugs are valid
    #
    if source.isNull or destination.isNull:

        raise TypeError('connectPlugs() expects 2 valid plugs!')

    # Check if other plug has a connection
    #
    otherPlug = destination.source()

    if not otherPlug.isNull:

        # Check if connection should be broken
        #
        if force:

            breakConnections(destination, source=True, destination=False)

        else:

            raise RuntimeError('connectPlugs() "%s" plug has an incoming connection!' % destination.info)

    # Check if a dag modifier was supplied
    #
    if modifier is None:

        modifier = om.MDGModifier()

    # Cache and execute dag modifier
    #
    log.debug(f'Connecting "{source.info}" > "{destination.info}"')
    modifier.connect(source, destination)

    undo.commitAndDoIt(modifier.doIt, modifier.undoIt)


def disconnectPlugs(source, destination, modifier=None):
    """
    Static method used to disconnect two plugs using a dag modifier.

    :type source: Union[str, om.MPlug]
    :type destination: Union[str, om.MPlug]
    :type modifier: Union[om.MDGModifier, None]
    :rtype: None
    """

    # Evaluate plug types
    #
    if not isinstance(source, om.MPlug) or not isinstance(destination, om.MPlug):

        raise TypeError('disconnectPlugs() expects 2 plugs!')

    # Check if plugs are valid
    #
    if source.isNull or destination.isNull:

        raise TypeError('disconnectPlugs() expects 2 valid plugs!')

    # Check if disconnection is legal
    #
    otherPlug = destination.source()

    if otherPlug != source or otherPlug.isNull:

        log.debug('%s is not connected to %s!' % (source.info, destination.info))
        return

    # Check if a dag modifier was supplied
    #
    if modifier is None:

        modifier = om.MDGModifier()

    # Commit and execute modifier
    #
    log.debug(f'Disconnecting "{source.info}" > "{destination.info}"')
    modifier.disconnect(source, destination)

    undo.commitAndDoIt(modifier.doIt, modifier.undoIt)


def breakConnections(plug, source=True, destination=True, recursive=False, modifier=None):
    """
    Break the connections to the supplied plug.
    Optional keyword arguments can be supplied to control the side the disconnect takes place.
    By default, these arguments are set to true for maximum breakage!

    :type plug: Union[str, om.MPlug]
    :type source: bool
    :type destination: bool
    :type recursive:bool
    :type modifier: Union[om.MDGModifier, None]
    :rtype: None
    """

    # Check if a dag modifier was supplied
    #
    if modifier is None:

        modifier = om.MDGModifier()

    # Check if the source plug should be broken
    #
    otherPlug = plug.source()

    if source and not otherPlug.isNull:

        modifier.disconnect(otherPlug, plug)

    # Check if the destination plugs should be broken
    #
    otherPlugs = plug.destinations()

    if destination and len(otherPlugs) > 0:

        for otherPlug in otherPlugs:

            modifier.disconnect(plug, otherPlug)

    # Check if children should be broken as well
    #
    if recursive:

        for childPlug in walk(plug):

            # Check if the source plug should be broken
            #
            otherPlug = childPlug.source()

            if source and not otherPlug.isNull:

                modifier.disconnect(otherPlug, childPlug)

            # Check if the destination plugs should be broken
            #
            otherPlugs = childPlug.destinations()

            if destination and len(otherPlugs) > 0:

                for otherPlug in otherPlugs:

                    modifier.disconnect(childPlug, otherPlug)

    # Commit and execute modifier
    #
    undo.commitAndDoIt(modifier.doIt, modifier.undoIt)


def iterTopLevelPlugs(node, **kwargs):
    """
    Returns a generator that yields top-level plugs from the supplied node.

    :type node: om.MObject
    :key readable: bool
    :key writable: bool
    :key keyable: bool
    :key affectsWorldSpace: bool
    :key skipUserAttributes: bool
    :rtype: Iterator[om.MPlug]
    """

    # Iterate through attributes
    #
    fnAttribute = om.MFnAttribute()

    readable = kwargs.get('readable', False)
    writable = kwargs.get('writable', False)
    keyable = kwargs.get('keyable', False)
    affectsWorldSpace = kwargs.get('affectsWorldSpace', False)
    skipUserAttributes = kwargs.get('skipUserAttributes', False)

    for attribute in attributeutils.iterTopLevelAttributes(node):

        # Check if attribute is readable
        #
        fnAttribute.setObject(attribute)

        if readable and not fnAttribute.readable:

            continue

        # Check if attribute is writable
        #
        if writable and not fnAttribute.writable:

            continue

        # Check if attribute is writable
        #
        if keyable and not fnAttribute.keyable:

            continue

        # Check if attribute affects world-space
        #
        if affectsWorldSpace and not fnAttribute.affectsWorldSpace:

            continue

        # Check if attribute is dynamic
        #
        if skipUserAttributes and fnAttribute.dynamic:

            continue

        yield om.MPlug(node, attribute)


def iterChannelBoxPlugs(node, **kwargs):
    """
    Returns a generator that yields plugs that are in the channel-box.

    :type node: om.MObject
    :key readable: bool
    :key writable: bool
    :key nonDefault: bool
    :key affectsWorldSpace: bool
    :key skipUserAttributes: bool
    :rtype: Iterator[om.MPlug]
    """

    # Iterate through top-level plugs
    #
    for plug in iterTopLevelPlugs(node, **kwargs):

        # Evaluate plug type
        #
        if plug.isArray:

            continue

        elif plug.isCompound:

            yield from iterChildren(plug, keyable=True, channelBox=True)

        else:

            isChannelBox = (plug.isKeyable or plug.isChannelBox) and isNumeric(plug)
            isWritable = plug.isFreeToChange() == om.MPlug.kFreeToChange

            if isChannelBox and isWritable:

                yield plug

            else:

                continue


def iterElements(plug, **kwargs):
    """
    Returns a generator that yields all elements from the supplied plug.
    This generator only works on array plugs and not elements!

    :type plug: om.MPlug
    :key writable: bool
    :key nonDefault: bool
    :rtype: Iterator[om.MPlug]
    """

    # Check if this is an array plug
    #
    if not plug.isArray or plug.isElement:

        return iter([])

    # Iterate through plug elements
    #
    writable = kwargs.get('writable', False)
    nonDefault = kwargs.get('nonDefault', False)

    indices = plug.getExistingArrayAttributeIndices()

    for (physicalIndex, logicalIndex) in enumerate(indices):

        # Check if element is writable
        #
        element = plug.elementByPhysicalIndex(physicalIndex)

        if writable and not (element.isFreeToChange() == om.MPlug.kFreeToChange):

            continue

        # Check if element is in non-default
        #
        if nonDefault and element.isDefaultValue:

            continue

        yield element


def iterChildren(plug, **kwargs):
    """
    Returns a generator that yields the children from the supplied plug.
    If the plug is not compound then no children are yielded!

    :type plug: om.MPlug
    :key readable: bool
    :key writable: bool
    :key nonDefault: bool
    :key keyable: bool
    :key channelBox: bool
    :rtype: Iterator[om.MPlug]
    """

    # Check if this is a compound plug
    #
    if not plug.isCompound:

        return iter([])

    # Iterate through children
    #
    writable = kwargs.get('writable', False)
    nonDefault = kwargs.get('nonDefault', False)
    keyable = kwargs.get('keyable', False)
    channelBox = kwargs.get('channelBox', False)

    numChildren = plug.numChildren()

    for i in range(numChildren):

        # Check if child is writable
        #
        child = plug.child(i)

        if writable and not (child.isFreeToChange() == om.MPlug.kFreeToChange):

            continue

        # Check if child is non-default
        #
        if nonDefault and child.isDefaultValue:

            continue

        # Check if child is keyable
        #
        if keyable and not child.isKeyable:

            continue

        # Check if child is in channel-box
        #
        if channelBox and (not child.isChannelBox and not child.isKeyable):

            continue

        yield child


def walk(plug, writable=False, channelBox=False, keyable=False):
    """
    Returns a generator that yields descendants from the supplied plug.

    :type plug: om.MPlug
    :type writable: bool
    :type channelBox: bool
    :type keyable: bool
    :rtype: Iterator[om.MPlug]
    """

    # Iterate through plug elements and children
    #
    elements = list(iterElements(plug, writable=writable))
    children = list(iterChildren(plug, writable=writable, channelBox=channelBox, keyable=keyable))

    queue = deque(elements + children)

    while len(queue):

        # Evaluate plug type
        #
        plug = queue.popleft()
        yield plug

        if plug.isArray and not plug.isElement:

            queue.extend(list(iterElements(plug, writable=writable)))

        elif plug.isCompound:

            queue.extend(list(iterChildren(plug, writable=writable, channelBox=channelBox, keyable=keyable)))

        else:

            continue


def removeMultiInstances(plug, indices):
    """
    Removes the indexed elements from the supplied plug.
    This method expects the plug to be an array and not an element!

    :type plug: om.MPlug
    :type indices: List[int]
    :rtype: None
    """

    # Iterate through indices
    #
    plugName = plug.partialName(includeNodeName=True, useFullAttributePath=True, useLongNames=True)

    for index in reversed(sorted(indices)):

        elementName = '{plugName}[{index}]'.format(plugName=plugName, index=index)
        log.info(f'Removing {elementName} element...')

        mc.removeMultiInstance(elementName)


def getConnectedNodes(plug, includeNullObjects=False):
    """
    Returns the nodes connected to the supplied plug.
    If the plug is an array or compound then a list of nodes is returned instead!

    :type plug: om.MPlug
    :type includeNullObjects: bool
    :rtype: Union[om.MObject, om.MObjectArray]
    """

    # Check if plug is array
    #
    nodes = om.MObjectArray()

    if plug.isArray and not plug.isElement:

        # Iterate through plug elements
        #
        for element in iterElements(plug):

            nodes += getConnectedNodes(element, includeNullObjects=includeNullObjects)

    elif plug.isCompound:

        # Iterate through plug children
        #
        for child in iterChildren(plug):

            nodes += getConnectedNodes(child, includeNullObjects=includeNullObjects)

    else:

        # Get source plug
        #
        otherPlug = plug.source()

        if not otherPlug.isNull:

            nodes.append(otherPlug.node())

        elif includeNullObjects:

            nodes.append(om.MObject.kNullObj)

        else:

            pass

    return nodes


def findConnectedMessage(dependNode, attribute=om.MObject.kNullObj):
    """
    Locates the connected destination plug for the given dependency node.

    :type dependNode: om.MObject
    :type attribute: om.MObject
    :rtype: Union[om.MPlug, None]
    """

    # Get message plug from dependency node
    #
    fnDepdendNode = om.MFnDependencyNode(dependNode)
    plug = fnDepdendNode.findPlug('message', True)

    destinations = plug.destinations()
    destinationCount = len(destinations)

    attributeSupplied = not attribute.isNull()

    if destinationCount == 0:

        return None

    elif destinationCount == 1:

        # Evaluate destination attribute
        #
        destination = destinations[0]

        if attributeSupplied:

            return destination if (destination.attribute() == attribute) else None

        else:

            return destination

    elif attributeSupplied:

        # Evaluate destination attributes
        #
        for destination in destinations:

            if destination.attribute() == attribute:

                return destination

            else:

                continue

        return None

    else:

        return None


def getNextAvailableElement(plug):
    """
    Finds the next available plug element a value can be set to.
    If there are no gaps then the last element will be returned.

    :type plug: Union[str, om.MPlug]
    :rtype: int
    """

    # Verify this is an array plug
    #
    if not plug.isArray:

        return None

    # Evaluate existing array indices
    #
    indices = plug.getExistingArrayAttributeIndices()
    numIndices = len(indices)

    for (physicalIndex, logicalIndex) in enumerate(indices):

        # Check if physical index does not match logical index
        #
        if physicalIndex != logicalIndex:

            return physicalIndex

        else:

            continue

    return indices[-1] + 1 if numIndices > 0 else 0


def getNextAvailableConnection(plug, child=om.MObject.kNullObj):
    """
    Finds the next available plug element a connection can be made to.
    If there are no gaps then the last element will be returned.
    An optional child attribute can be supplied if the element to test is nested.

    :type plug: Union[str, om.MPlug]
    :type child: om.MObject
    :rtype: int
    """

    # Verify this is an array plug
    #
    if not plug.isArray:

        return None

    # Evaluate existing array indices
    #
    indices = plug.getExistingArrayAttributeIndices()
    numIndices = len(indices)

    for (physicalIndex, logicalIndex) in enumerate(indices):

        # Check if physical index matched logical index
        #
        element = plug.elementByLogicalIndex(logicalIndex)

        if not child.isNull():

            element = element.child(child)

        # Check if physical index does not match logical index
        # Otherwise, check if element is connected
        #
        if physicalIndex != logicalIndex:

            return physicalIndex

        elif not element.isConnected:

            return logicalIndex

        else:

            continue

    return indices[-1] + 1 if numIndices > 0 else 0


def consolidateConnectedElements(plug):
    """
    Ensures all connected elements are ordered with no gaps starting at zero.

    :type plug: om.MPlug
    :rtype: None
    """

    # Compare connected elements to physical indices
    #
    logicalIndices = plug.getExistingArrayAttributeIndices()
    elements = [plug.elementByLogicalIndex(logicalIndex) for logicalIndex in logicalIndices]

    connectedElements = [element for element in elements if element.isDestination]
    numConnectedElements = len(connectedElements)

    for (physicalIndex, destination) in enumerate(connectedElements):

        logicalIndex = destination.logicalIndex()

        if physicalIndex != logicalIndex:

            source = destination.source()
            disconnectPlugs(source, destination)

            newDestination = plug.elementByLogicalIndex(physicalIndex)
            log.info(f'Moving {destination.info} to {newDestination.info}')
            connectPlugs(source, newDestination)

        else:

            continue

    # Remove any unused indices
    #
    unusedIndices = [logicalIndex for logicalIndex in logicalIndices if logicalIndex >= numConnectedElements]
    removeMultiInstances(plug, unusedIndices)



def moveConnectedElements(plug, index):
    """
    Moves all the connected elements at the specified index down the array.

    :type plug: om.MPlug
    :type index: int
    :rtype: None
    """

    # Evaluate existing elements
    #
    logicalIndices = [logicalIndex for logicalIndex in plug.getExistingArrayAttributeIndices() if logicalIndex >= index]
    numLogicalIndices = len(logicalIndices)

    if numLogicalIndices == 0:

        return

    # Iterate through logical indices
    #
    for logicalIndex in reversed(sorted(logicalIndices)):

        # Check if element is connected
        #
        element = plug.elementByLogicalIndex(logicalIndex)

        if not element.isDestination:

            continue

        # Reconnect to next element
        #
        nextLogicalIndex = logicalIndex + 1
        nextElement = plug.elementByLogicalIndex(nextLogicalIndex)
        source = element.source()

        disconnectPlugs(source, element)
        connectPlugs(source, nextElement)


def hasConnection(plug):
    """
    Evaluates if the supplied plug or any of its children have incoming connections.

    :type plug: om.MPlug
    :rtype: bool
    """

    isArray = plug.isArray and not plug.isElement
    isCompound = plug.isCompound and not plug.isChild

    if isArray:

        return plug.isDestination or any([element.isDestination for element in iterElements(plug)])

    elif isCompound:

        return plug.isDestination or any([child.isDestination for child in iterChildren(plug)])

    else:

        return plug.isDestination


def hasAlias(plug):
    """
    Evaluates if the supplied node has an alias.

    :type plug: om.MPlug
    :rtype: bool
    """

    return not stringutils.isNullOrEmpty(getAlias(plug))


def getAlias(plug):
    """
    Returns the alias for the supplied plug.

    :type plug: om.MPlug
    :rtype: str
    """

    return om.MFnDependencyNode(plug.node()).plugsAlias(plug)


def getAliases(node):
    """
    Returns a dictionary of aliases from the supplied node.

    :type node: om.MObject
    :rtype: Dict[str, str]
    """

    return dict(om.MFnDependencyNode(node).getAliasList())


def setAlias(plug, alias):
    """
    Assigns the alias to the supplied plug.

    :type plug: om.MPlug
    :type alias: str
    :rtype: bool
    """

    # Check if alias should be replaced
    #
    if hasAlias(plug):

        removeAlias(plug)

    # Create new plug alias
    #
    fnDependNode = om.MFnDependencyNode(plug.node())
    return fnDependNode.setAlias(alias, plug.partialName(useLongNames=True), plug, add=True)


def removeAlias(*plugs):
    """
    Removes any aliases from the supplied plugs.

    :type plugs: Union[om.MPlug, Tuple[om.MPlug]]
    :rtype: bool
    """

    # Iterate through plugs
    #
    fnDependNode = om.MFnDependencyNode()

    numPlugs = len(plugs)
    success = [None] * numPlugs

    for (i, plug) in enumerate(plugs):

        # Check if plug has an alias
        #
        alias = getAlias(plug)

        if stringutils.isNullOrEmpty(alias):

            continue

        # Remove alias from plug
        #
        fnDependNode.setObject(plug.node())
        success[i] = fnDependNode.setAlias(alias, plug.partialName(useLongNames=True), plug, add=False)

    return all(success)
