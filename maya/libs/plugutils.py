import re

from maya import cmds as mc
from maya.api import OpenMaya as om
from collections import deque
from dcc.python import stringutils
from dcc.maya.libs import attributeutils

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


def findPlug(node, plugPath):
    """
    Returns the plug derived from the supplied string path relative to the given node.
    Unlike the API method derived from MFnDependencyNode this function supports indices and children.
    This method also accepts partial paths in that a parent attribute can be omitted and still resolved.

    :type node: om.MObject
    :type plugPath: str
    :rtype: om.MPlug
    """

    # Break down string path into groups
    #
    fnDependNode = om.MFnDependencyNode(node)
    nodeName = fnDependNode.name()

    groups = __plug_parser__.findall(plugPath)
    numGroups = len(groups)

    if numGroups == 0:

        raise TypeError('findPlug() unable to split path: "%s"!' % plugPath)

    # Find leaf attribute
    #
    attributeName = groups[-1][0]
    attribute = fnDependNode.attribute(attributeName)

    if attribute.isNull():

        raise TypeError('findPlug() cannot find "%s.%s" attribute!' % (nodeName, attributeName))

    # Trace attribute path
    # Collect all indices in plug path
    #
    attributes = list(attributeutils.trace(attribute))
    indices = {attribute: int(index) for (attribute, index) in groups if len(index) > 0}

    # Navigate through hierarchy
    #
    fnAttribute = om.MFnAttribute()
    plug = None

    for (index, attribute) in enumerate(attributes):

        # Get next child plug
        #
        if index == 0:

            plug = om.MPlug(node, attribute)

        else:

            plug = plug.child(attribute)

        # Check if plug was indexed
        # Make sure to check both the short and long names!
        #
        fnAttribute.setObject(attribute)
        longName = fnAttribute.name
        shortName = fnAttribute.shortName

        longIndex = indices.get(longName, None)
        shortIndex = indices.get(shortName, None)

        if shortIndex is not None:

            plug = plug.elementByLogicalIndex(shortIndex)

        elif longIndex is not None:

            plug = plug.elementByLogicalIndex(longIndex)

        else:

            continue

    return plug


def isConstrained(plug):
    """
    Evaluates if the supplied plug is constrained.

    :type plug: om.MPlug
    :rtype: bool
    """

    # Check if plug has a connection
    #
    source = plug.source()

    if source.isNull:

        return False

    # Evaluate node type
    #
    node = source.node()
    return node.hasFn(om.MFn.kConstraint)


def isAnimated(plug):
    """
    Evaluates if the supplied plug is animated.

    :type plug: om.MPlug
    :rtype: bool
    """

    # Check if plug has a connection
    #
    source = plug.source()

    if source.isNull:

        return False

    # Evaluate node type
    #
    node = source.node()
    return node.hasFn(om.MFn.kAnimCurve)


def connectPlugs(source, destination, force=False):
    """
    Method used to connect two plugs.
    By default, this method will not break pre-existing connections unless specified.

    :type source: Union[str, om.MPlug]
    :type destination: Union[str, om.MPlug]
    :type force: bool
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
    connectedPlug = destination.source()

    if not connectedPlug.isNull:

        # Check if connection should be broken
        #
        if force:

            breakConnections(destination, source=True, destination=False)

        else:

            raise RuntimeError('connectPlugs() "%s" plug has an incoming connection!' % destination.info)

    # Execute dag modifier
    #
    dagModifier = om.MDagModifier()
    dagModifier.connect(source, destination)
    dagModifier.doIt()


def disconnectPlugs(source, destination):
    """
    Static method used to disconnect two plugs using a dag modifier.

    :type source: Union[str, om.MPlug]
    :type destination: Union[str, om.MPlug]
    :rtype: None
    """

    # Check plug types
    #
    if not isinstance(source, om.MPlug) or not isinstance(destination, om.MPlug):

        raise TypeError('disconnectPlugs() expects 2 plugs!')

    # Check if plugs are valid
    #
    if source.isNull or destination.isNull:

        raise TypeError('disconnectPlugs() expects 2 valid plugs!')

    # Verify plugs are connected
    #
    connectedPlug = destination.source()

    if connectedPlug.isNull:

        log.debug('%s plug is not connected to %s!' % (source.info, destination.info))
        return

    # Check if plugs are identical
    #
    if connectedPlug != source:

        log.debug('%s is not connected to %s!' % (source.info, destination.info))
        return

    # Execute dag modifier
    #
    dagModifier = om.MDagModifier()
    dagModifier.disconnect(source, destination)
    dagModifier.doIt()


def breakConnections(plug, source=True, destination=True, recursive=False):
    """
    Break the connections to the supplied plug.
    Optional keyword arguments can be supplied to control the side the disconnect takes place.
    By default, these arguments are set to true for maximum breakage!

    :type plug: Union[str, om.MPlug]
    :type source: bool
    :type destination: bool
    :type recursive:bool
    :rtype: None
    """

    # Check if the source plug should be broken
    #
    otherPlug = plug.source()

    if source and not otherPlug.isNull:

        disconnectPlugs(otherPlug, plug)

    # Check if the destination plugs should be broken
    #
    if destination:

        for otherPlug in plug.destinations():

            disconnectPlugs(plug, otherPlug)

    # Check if children should be broken
    # Whatever you do don't enable recursive for children!!!
    #
    if recursive:

        for childPlug in walk(plug):

            breakConnections(childPlug, source=source, destination=destination)


def iterTopLevelPlugs(node):
    """
    Returns a generator that yields top-level plugs from the supplied node.

    :type node: om.MObject
    :rtype: iter
    """

    # Iterate through attributes
    #
    for attribute in attributeutils.iterAttributes(node):

        # Check if attribute is top-level
        #
        fnAttribute = om.MFnAttribute(attribute)

        if fnAttribute.parent.isNull():

            yield om.MPlug(node, attribute)

        else:

            continue


def iterChannelBoxPlugs(node):
    """
    Returns a generator that yields plugs that are in the channel-box.

    :type node: om.MObject
    :rtype: iter
    """

    # Iterate through top-level plugs
    #
    for plug in iterTopLevelPlugs(node):

        # Check if this is a compound plug
        #
        if plug.isCompound and not plug.isArray:

            yield from iterChildren(plug, writable=True, keyable=True)

        elif plug.isChannelBox:

            yield plug

        else:

            continue


def iterElements(plug, writable=False, nonDefault=False):
    """
    Returns a generator that yields all elements from the supplied plug.
    This generator only works on array plugs and not elements!

    :type plug: om.MPlug
    :type writable: bool
    :type nonDefault: bool
    :rtype: iter
    """

    # Check if this is an array plug
    #
    if not plug.isArray or plug.isElement:

        return iter([])

    # Iterate through plug elements
    #
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


def iterChildren(plug, writable=False, nonDefault=False, keyable=False):
    """
    Returns a generator that yields the children from the supplied plug.
    If the plug is not compound then no children are yielded!

    :type plug: om.MPlug
    :type writable: bool
    :type nonDefault: bool
    :type keyable: bool
    :rtype: iter
    """

    # Check if this is a compound plug
    #
    if not plug.isCompound:

        return iter([])

    # Iterate through children
    #
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

        yield child


def walk(plug, writable=False, channelBox=False, keyable=False):
    """
    Returns a generator that yields descendants from the supplied plug.

    :type plug: om.MPlug
    :type writable: bool
    :type channelBox: bool
    :type keyable: bool
    :rtype: iter
    """

    # Iterate through plug elements/children
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
    :type indices: list[int]
    :rtype: None
    """

    # Iterate through indices
    #
    plugName = plug.partialName(includeNodeName=True, useFullAttributePath=True, useLongNames=True)

    for index in indices:

        elementName = '{plugName}[{index}]'.format(plugName=plugName, index=index)
        log.info('Removing %s element...' % elementName)

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


def findConnectedMessage(dependNode, attribute):
    """
    Locates the connected destination plug for the given dependency node.

    :type dependNode: om.MObject
    :type attribute: om.MObject
    :rtype: om.MPlug
    """

    # Get message plug from dependency node
    #
    fnDepdendNode = om.MFnDependencyNode(dependNode)
    plug = fnDepdendNode.findPlug('message', True)

    destinations = plug.destinations()

    for destination in destinations:

        # Check if attributes match
        #
        if destination.attribute() == attribute:

            return destination

        else:

            continue

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

    :type plugs: om.MPlug
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
