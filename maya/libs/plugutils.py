import re

from maya import cmds as mc
from maya.api import OpenMaya as om
from collections import deque
from dcc.maya.libs import attributeutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__plugparser__ = re.compile(r'([a-zA-Z0-9_]+)(?:\[([0-9]+)\])?')


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


def findPlug(dependNode, plugName):
    """
    Returns the plug derived from the supplied string path relative to the given node.
    Unlike the API method derived from MFnDependencyNode this function supports indices and children.
    This method also accepts partial paths in that a parent attribute can be omitted and still resolved.

    :type dependNode: om.MObject
    :type plugName: str
    :rtype: om.MPlug
    """

    # Break down string path into groups
    #
    fnDependNode = om.MFnDependencyNode(dependNode)

    groups = __plugparser__.findall(plugName)
    numGroups = len(groups)

    if numGroups == 0:

        raise TypeError('findPlug() unable to parse "%s" path!' % plugName)

    # Find leaf attribute
    #
    attributeName = groups[-1][0]
    attribute = fnDependNode.attribute(attributeName)

    if attribute.isNull():

        raise TypeError('findPlug() cannot find "%s" attribute!' % attributeName)

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

            plug = om.MPlug(dependNode, attribute)

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


def walk(plug):
    """
    Returns a generator that can iterate over a plug's descendants.

    :type plug: om.MPlug
    :rtype: iter
    """

    # Check if this plug is walkable
    # If it is then collect child plugs
    #
    queue = None

    if plug.isArray and not plug.isElement:

        queue = deque(iterElements(plug))

    elif plug.isCompound:

        queue = deque(iterChildren(plug))

    else:

        return

    # Walk through plug hierarchy
    #
    while len(queue):

        plug = queue.popleft()
        yield plug

        if plug.isArray and not plug.isElement:

            queue.extend(list(iterElements(plug)))

        elif plug.isCompound:

            queue.extend(list(iterChildren(plug)))

        else:

            continue


def iterElements(plug):
    """
    Returns a generator that can iterate over a plugs elements.
    This generator only works on array plugs and not elements!

    :type plug: om.MPlug
    :rtype: iter
    """

    # Check if this is an array plug
    #
    if not plug.isArray or plug.isElement:

        return

    # Iterate through plug elements
    #
    numElements = plug.numElements()

    for i in range(numElements):

        yield plug.elementByPhysicalIndex(i)


def iterChildren(plug):
    """
    Returns a generator that can iterate over a plugs children.
    This generator only works on compound plugs!

    :type plug: om.MPlug
    :rtype: iter
    """

    # Check if this is a compound plug
    #
    if not plug.isCompound:

        return

    # Iterate through children
    #
    numChildren = plug.numChildren()

    for i in range(numChildren):

        yield plug.child(i)


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
    numElements = plug.evaluateNumElements()

    for physicalIndex in range(numElements):

        # Check if physical index matched logical index
        #
        element = plug.elementByPhysicalIndex(physicalIndex)
        logicalIndex = element.logicalIndex()

        # Check if physical index does not match logical index
        #
        if physicalIndex != logicalIndex:

            return physicalIndex

        else:

            continue

    return numElements


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
    numElements = plug.evaluateNumElements()

    for physicalIndex in range(numElements):

        # Check if physical index matched logical index
        #
        element = plug.elementByPhysicalIndex(physicalIndex)
        logicalIndex = element.logicalIndex()

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

    return numElements
