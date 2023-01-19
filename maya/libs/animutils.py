from maya import cmds as mc
from maya.api import OpenMaya as om, OpenMayaAnim as oma
from dcc.dataclasses import vector, keyframe, bezierpoint
from . import dagutils, plugutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getAnimCurveType(attribute):
    """
    Returns the anim-curve type associated with the given attribute.

    :type attribute: om.MObject
    :rtype: int
    """

    # Check if this is a unit attribute
    #
    if not attribute.hasFn(om.MFn.kUnitAttribute):

        return oma.MFnAnimCurve.kAnimCurveTU

    # Evaluate unit type
    #
    fnUnitAttribute = om.MFnUnitAttribute(attribute)
    unitType = fnUnitAttribute.unitType()

    if unitType == om.MFnUnitAttribute.kDistance:

        return oma.MFnAnimCurve.kAnimCurveTL

    elif unitType == om.MFnUnitAttribute.kAngle:

        return oma.MFnAnimCurve.kAnimCurveTA

    else:

        return oma.MFnAnimCurve.kAnimCurveTT


def ensureKeyed(plug):
    """
    Ensures the supplied plug is keyed.

    :type plug: om.MPlug
    :rtype: om.MObject
    """

    # Redundancy check
    #
    if not plug.isKeyable:

        return

    # Check if plug is already animated
    #
    if plugutils.isAnimated(plug):

        return plug.source().node()

    # Create anim curve for plug
    #
    animCurveType = getAnimCurveType(plug.attribute())

    fnAnimCurve = oma.MFnAnimCurve()
    animCurve = fnAnimCurve.create(plug, animCurveType=animCurveType)

    return animCurve


def clearKeys(animCurve):
    """
    Removes all keys from the supplied anim curve.

    :type animCurve: om.MObject
    :rtype: None
    """

    fnAnimCurve = oma.MFnAnimCurve(animCurve)

    for i in reversed(range(fnAnimCurve.numKeys)):

        fnAnimCurve.remove(i)


def uiToInternalUnit(value, animCurveType=oma.MFnAnimCurve.kAnimCurveTL):
    """
    Converts the supplied value to the associated curve type's internal unit.

    :type value: Union[int, float]
    :type animCurveType: int
    :rtype: Union[int, float]
    """

    if animCurveType == oma.MFnAnimCurve.kAnimCurveTL:

        uiUnit = om.MDistance.uiUnit()
        internalUnit = om.MDistance.internalUnit()
        return om.MDistance(value, unit=uiUnit).asUnits(internalUnit)

    elif animCurveType == oma.MFnAnimCurve.kAnimCurveTA:

        uiUnit = om.MAngle.uiUnit()
        internalUnit = om.MAngle.internalUnit()
        return om.MAngle(value, unit=uiUnit).asUnits(internalUnit)

    else:

        return value


def internalToUiUnit(value, animCurveType=oma.MFnAnimCurve.kAnimCurveTL):
    """
    Converts the supplied value to the associated curve type's UI unit.

    :type value: Union[int, float]
    :type animCurveType: int
    :rtype: Union[int, float]
    """

    if animCurveType == oma.MFnAnimCurve.kAnimCurveTL:

        uiUnit = om.MDistance.uiUnit()
        internalUnit = om.MDistance.internalUnit()
        return om.MDistance(value, unit=internalUnit).asUnits(uiUnit)

    elif animCurveType == oma.MFnAnimCurve.kAnimCurveTA:

        uiUnit = om.MAngle.uiUnit()
        internalUnit = om.MAngle.internalUnit()
        return om.MAngle(value, unit=internalUnit).asUnits(uiUnit)

    else:

        return value


def synchronizeTangents(plug):
    """
    Synchronizes the in and out tangents on the start and last keys.

    :type plug: om.MPlug
    :rtype: None
    """

    # Check if plug is animated
    #
    if not plugutils.isAnimated(plug):

        return

    # Check if there are enough keys
    #
    fnAnimCurve = oma.MFnAnimCurve(plug)
    numKeys = fnAnimCurve.numKeys

    lastIndex = numKeys - 1

    if numKeys < 2:

        return

    # Unlock tangents
    #
    fnAnimCurve.setTangentsLocked(0, False)
    fnAnimCurve.setTangentsLocked(lastIndex, False)

    # Synchronize tangents
    #
    outTangentX, outTangentY = fnAnimCurve.getTangentXY(0, False)
    inTangentX, inTangentY = fnAnimCurve.getTangentXY(lastIndex, True)

    fnAnimCurve.setTangent(0, inTangentX, inTangentY, True, convertUnits=False)
    fnAnimCurve.setTangent(lastIndex, outTangentX, outTangentY, False, convertUnits=False)

    # Lock tangents
    #
    fnAnimCurve.setTangentsLocked(0, True)
    fnAnimCurve.setTangentsLocked(lastIndex, True)


def cacheKeys(plug):
    """
    Returns a keyframe cache from the supplied plug.

    :type plug: om.MPlug
    :rtype: List[keyframe.Keyframe]
    """

    # Evaluate if plug is animated
    #
    if not plugutils.isAnimated(plug):

        return []

    # Iterate through keys
    #
    fnAnimCurve = oma.MFnAnimCurve(plug)
    keys = [None] * fnAnimCurve.numKeys

    for i in range(fnAnimCurve.numKeys):

        keys[i] = keyframe.Keyframe(
            time=fnAnimCurve.input(i).value,
            value=fnAnimCurve.value(i),
            inTangent=vector.Vector(*fnAnimCurve.getTangentXY(i, True)),
            inTangentType=fnAnimCurve.inTangentType(i),
            outTangent=vector.Vector(*fnAnimCurve.getTangentXY(i, False)),
            outTangentType=fnAnimCurve.outTangentType(i)
        )

    return keys


def synchronizeCompoundInputs(plug):
    """
    Synchronizes the key inputs on the supplied compound plug by inserting new keys.
    This method will return a dictionary containing the original key inputs.

    :type plug: om.MPlug
    :rtype: Dict[str, List[keyframe.Keyframe]]
    """

    # Check if plug is valid
    #
    inputs = {}

    if plug.isNull or not plug.isCompound:

        return inputs

    # Collect key inputs from compound plug
    #
    numChildren = plug.numChildren()
    caches = {}

    for i in range(numChildren):

        # Check if plug is animated
        #
        childPlug = plug.child(i)
        childName = childPlug.partialName(useLongNames=True)

        caches[childName] = cacheKeys(childPlug)

    # Check if there are any inputs
    #
    inputs = set.union(*[set(handle.time for handle in cache) for cache in caches.values()])
    numInputs = len(inputs)

    if numInputs == 0:

        return caches

    # Insert any missing key inputs on child plugs
    #
    fnAnimCurve = oma.MFnAnimCurve()

    for i in range(numChildren):

        # Check if plug is animated
        #
        childPlug = plug.child(i)

        if plugutils.isAnimated(childPlug):

            animCurve = childPlug.source().node()
            fnAnimCurve.setObject(animCurve)

        else:

            animCurveType = getAnimCurveType(childPlug.attribute())

            fnAnimCurve.create(plug.node(), childPlug.attribute(), animCurveType=animCurveType)
            fnAnimCurve.setPreInfinityType(oma.MFnAnimCurve.kConstant)
            fnAnimCurve.setPostInfinityType(oma.MFnAnimCurve.kConstant)
            fnAnimCurve.setIsWeighted(True)

        # Iterate through inputs
        #
        for value in inputs:

            time = om.MTime(value, unit=om.MTime.uiUnit())
            index = fnAnimCurve.find(time)

            if index is None:

                fnAnimCurve.insertKey(time)

            else:

                continue

    return caches


def getBaseAnimLayer():
    """
    Returns the base anim layer.

    :rtype: om.MObject
    """

    animLayers = [animLayer for animLayer in dagutils.iterNodes(apiType=om.MFn.kAnimLayer) if isBaseAnimLayer(animLayer)]
    numAnimLayers = len(animLayers)

    if numAnimLayers == 1:

        return animLayers[0]

    else:

        return om.MObject.kNullObj


def isBaseAnimLayer(animLayer):
    """
    Evaluates if the supplied layer is top-level.

    :type animLayer: om.MObject
    :rtype: bool
    """

    return getAnimLayerParent(animLayer).isNull()


def getAssociatedAnimLayers(*nodes):
    """
    Returns the anim layers associated with the supplied node.
    Layers are ordered based on their child index in the base anim layer.

    :type nodes: Union[om.MObject, Tuple[om.MObject]]
    :rtype: om.MObjectArray
    """

    # Iterate through layers
    #
    baseLayer = getBaseAnimLayer()
    childLayers = getAnimLayerChildren(baseLayer)

    animLayers = om.MObjectArray()

    for childLayer in childLayers:

        # Check if child layer contains nodes
        #
        layerObjects = getAnimLayerObjects(childLayer)

        if any([node in layerObjects for node in nodes]):

            animLayers.append(childLayer)

        else:

            continue

    return animLayers


def iterAnimLayerMembers(animLayer, node=om.MObject.kNullObj):
    """
    Returns a generator that yields plug members from the supplied anim layer.
    An optional node can be supplied to limit the yielded members.

    :type animLayer: om.MObject
    :type node: om.MObject
    :rtype: Iterator[om.MPlug]
    """

    # Iterate through plug elements
    #
    fnDependNode = om.MFnDependencyNode(animLayer)
    plug = fnDependNode.findPlug('dagSetMembers', True)

    indices = plug.getExistingArrayAttributeIndices()

    for (physicalIndex, logicalIndex) in enumerate(indices):

        # Check if element is connected
        #
        element = plug.elementByPhysicalIndex(physicalIndex)
        otherPlug = element.source()

        if otherPlug.isNull:

            continue

        # Check if a node was supplied
        #
        if not node.isNull():

            # Compare nodes
            #
            if node == otherPlug.node():

                yield otherPlug

            else:

                continue

        else:

            yield otherPlug


def getAnimLayerMembers(animLayer, node=om.MObject.kNullObj):
    """
    Returns a list of plug members from the supplied anim layer.

    :type animLayer: om.MObject
    :type node: om.MObject
    :rtype: om.MPlugArray
    """

    return om.MPlugArray(list(iterAnimLayerMembers(animLayer, node=node)))


def getAnimLayerObjects(*animLayers):
    """
    Returns a list of nodes associated with the supplied anim layer.

    :type animLayers: Union[om.MObject, Tuple[om.MObject]]
    :rtype: om.MObjectArray
    """

    # Iterate through anim layers
    #
    objects = om.MObjectArray()
    traversed = {}

    for animLayer in animLayers:

        # Iterate through anim layer members
        #
        for plug in iterAnimLayerMembers(animLayer):

            # Check if node has already been appended
            #
            node = plug.node()
            hashCode = om.MObjectHandle(node).hashCode()

            hasObject = traversed.get(hashCode, False)

            if not hasObject:

                traversed[hashCode] = True
                objects.append(node)

            else:

                continue

    return objects


def getAnimLayerParent(animLayer):
    """
    Returns the parent of the supplied anim layer.

    :type animLayer: om.MObject
    :rtype: om.MObject
    """

    fnDependNode = om.MFnDependencyNode(animLayer)
    plug = fnDependNode.findPlug('parentLayer', True)

    destinations = plug.destinations()
    numDestinations = len(destinations)

    if numDestinations == 1:

        return destinations[0].node()

    else:

        return om.MObject.kNullObj


def getAnimLayerChildren(animLayer):
    """
    Returns a list of children from the supplied anim layer.

    :type animLayer: om.MObject
    :rtype: om.MObjectArray
    """

    fnDependNode = om.MFnDependencyNode(animLayer)
    plug = fnDependNode.findPlug('childrenLayers', True)

    return plugutils.getConnectedNodes(plug)


def getAnimLayerBlends(*animLayers):
    """
    Returns the anim curves from the supplied layer.

    :type animLayers: Union[om.MObject, Tuple[om.MObject]]
    :rtype: om.MObjectArray
    """

    # Iterate through anim layers
    #
    fnDependNode = om.MFnDependencyNode()
    blends = om.MObjectArray()

    for animLayer in animLayers:

        # Extend blend array
        #
        fnDependNode.setObject(animLayer)
        plug = fnDependNode.findPlug('blendNodes', True)

        blends += plugutils.getConnectedNodes(plug)

    return blends


def getBlendAnimCurves(*blends, inputA=False, inputB=True):
    """
    Returns a list of anim curves from the supplied blend nodes.
    Overriding the `input` flags changes which curves are returned.

    :type blends: Union[om.MObject, Tuple[om.MObject]]
    :type inputA: bool
    :type inputB: bool
    :rtype: om.MObjectArray
    """

    # Iterate through blends
    #
    fnDependNode = om.MFnDependencyNode()
    animCurves = om.MObjectArray()

    for blend in blends:

        # Check if `inputA` should be included
        #
        fnDependNode.setObject(blend)

        if inputA:

            plug = fnDependNode.findPlug('inputA', True)
            animCurves += plugutils.getConnectedNodes(plug, includeNullObjects=True)

        # Check if `inputB` should be included
        #
        if inputB:

            plug = fnDependNode.findPlug('inputB', True)
            animCurves += plugutils.getConnectedNodes(plug, includeNullObjects=True)

    return animCurves


def getAnimLayerCurves(animLayer, node=om.MObject.kNullObj, inputA=False, inputB=True):
    """
    Returns member-curve pairs from the supplied anim layer for the specified node.
    If no node is specified then all anim curves are returned instead!

    :type animLayer: om.MObject
    :type node: om.MObject
    :type inputA: bool
    :type inputB: bool
    :rtype: om.MObjectArray
    """

    # Get input curves from anim layer
    #
    blends = getAnimLayerBlends(animLayer)
    animCurves = getBlendAnimCurves(*blends, inputA=inputA, inputB=inputB)

    if node.isNull():

        return animCurves

    # Get indices associated with node
    #
    members = getAnimLayerMembers(animLayer, node=node)
    indices = [index for (index, member) in enumerate(members) if member.node() == node]

    if len(animCurves) == len(members):

        return [animCurves[index] for index in indices]

    else:

        return []


def getNodeAnimCurves(node):
    """
    Returns a list of attribute-curve pairs from the supplied node.
    If the node is using anim layers then no curves will be returned!

    :type node: om.MObject
    :rtype: Dict[str, om.MObject]
    """

    # Iterate through channel-box plug
    #
    animCurves = {}

    for plug in plugutils.iterChannelBoxPlugs(node):

        # Check if plug is animated
        #
        if plugutils.isAnimated(plug):

            name = plug.partialName(useLongNames=True)
            animCurves[name] = plug.source().node()

        else:

            continue

    return animCurves


def getNodeAnimLayers(node):
    """
    Returns a list of attribute-layer pairs from the supplied node.

    :type node: om.MObject
    :rtype: Dict[str, Dict[str, om.MObject]]
    """

    # Iterate through associated anim layers
    #
    animLayers = getAssociatedAnimLayers(node)
    animCurves = {}

    for (i, animLayer) in enumerate(animLayers):

        # Check if we need to include the base layer
        #
        members = getAnimLayerMembers(animLayer, node=node)

        if i == 0:

            baseCurves = getAnimLayerCurves(animLayer, node=node, inputA=True, inputB=False)
            animCurves['BaseAnimation'] = {member.partialName(useLongNames=True): animCurve for (member, animCurve) in zip(members, baseCurves)}

        # Add layer member-curves
        #
        layerName = dagutils.getNodeName(animLayer)
        layerCurves = getAnimLayerCurves(animLayer, node=node, inputA=False, inputB=True)

        animCurves[layerName] = {member.partialName(useLongNames=True): animCurve for (member, animCurve) in zip(members, layerCurves)}

    return animCurves
