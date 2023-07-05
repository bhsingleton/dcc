from maya import cmds as mc
from maya.api import OpenMaya as om, OpenMayaAnim as oma
from enum import IntEnum
from . import dagutils, attributeutils, plugutils
from ..decorators.undo import commit
from ...python import stringutils
from ...dataclasses import vector, keyframe

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BlendMode(IntEnum):
    """
    Collection of all the possible blend modes.
    """

    additive = 0
    multiply = 1


def isAnimCurve(obj):
    """
    Evaluates if the supplied object is an anim-curve.

    :type obj: om.MObject
    :rtype: bool
    """

    return obj.hasFn(om.MFn.kAnimCurve)


def isAnimBlend(obj):
    """
    Evaluates if the supplied object is an anim-blend.

    :type obj: om.MObject
    :rtype: bool
    """

    return obj.apiTypeStr.startswith('kBlendNode')  # FIXME: `MObject::hasFn` does not accept `MFn::kBlendNodeBase`


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


def expandUnits(value, asInternal=False):
    """
    Expands the supplied unit into a number.

    :type value: Any
    :type asInternal: bool
    :rtype: float
    """

    # Inspect value type
    #
    if not isinstance(value, (om.MDistance, om.MAngle, om.MTime)):

        return value

    # Check which unit type to return
    #
    if asInternal:

        internalUnit = type(value).internalUnit()
        return value.asUnits(internalUnit)

    else:

        uiUnit = type(value).uiUnit()
        return value.asUnits(uiUnit)


def uiToInternalUnit(value, animCurveType=oma.MFnAnimCurve.kAnimCurveTL):
    """
    Converts the supplied value to the associated curve type's internal unit.

    :type value: Union[int, float]
    :type animCurveType: int
    :rtype: Union[int, float]
    """

    # Evaluate anim-curve type
    #
    if animCurveType == oma.MFnAnimCurve.kAnimCurveTL:

        # Inspect value type
        #
        internalUnit = om.MDistance.internalUnit()

        if isinstance(value, (int, float)):

            uiUnit = om.MDistance.uiUnit()
            return om.MDistance(value, unit=uiUnit).asUnits(internalUnit)

        elif isinstance(value, om.MDistance):

            return value.asUnits(internalUnit)

        else:

            raise TypeError('uiToInternalUnit() expects an int or float (%s given!)' % type(value).__name__)

    elif animCurveType == oma.MFnAnimCurve.kAnimCurveTA:

        # Inspect value type
        #
        internalUnit = om.MAngle.internalUnit()

        if isinstance(value, (int, float)):

            uiUnit = om.MAngle.uiUnit()
            return om.MAngle(value, unit=uiUnit).asUnits(internalUnit)

        elif isinstance(value, om.MAngle):

            return value.asUnits(internalUnit)

        else:

            raise TypeError('uiToInternalUnit() expects an int or float (%s given!)' % type(value).__name__)

    else:

        return value


def internalToUiUnit(value, animCurveType=oma.MFnAnimCurve.kAnimCurveTL):
    """
    Converts the supplied value to the associated curve type's UI unit.

    :type value: Union[int, float]
    :type animCurveType: int
    :rtype: Union[int, float]
    """

    # Evaluate anim-curve type
    #
    if animCurveType == oma.MFnAnimCurve.kAnimCurveTL:

        # Inspect value type
        #
        uiUnit = om.MDistance.uiUnit()

        if isinstance(value, (int, float)):

            internalUnit = om.MDistance.internalUnit()
            return om.MDistance(value, unit=internalUnit).asUnits(uiUnit)

        elif isinstance(value, om.MDistance):

            return value.asUnits(uiUnit)

        else:

            raise TypeError('internalToUiUnit() expects an int or float (%s given!)' % type(value).__name__)

    elif animCurveType == oma.MFnAnimCurve.kAnimCurveTA:

        # Inspect value type
        #
        uiUnit = om.MAngle.uiUnit()

        if isinstance(value, (int, float)):

            internalUnit = om.MAngle.internalUnit()
            return om.MAngle(value, unit=internalUnit).asUnits(uiUnit)

        elif isinstance(value, om.MAngle):

            return value.asUnits(uiUnit)

        else:

            raise TypeError('internalToUiUnit() expects an int or float (%s given!)' % type(value).__name__)

    else:

        return value


def findAnimatedPlug(plug):
    """
    Returns the plug that is currently being animated on.
    If the plug is being used by an anim-layer then the input plug from the blend node will be returned!

    :type plug: om.MPlug
    :rtype: om.MPlug
    """

    # Check if plug is animated
    #
    isAnimated = plugutils.isAnimated(plug)

    if not isAnimated:

        return plug

    # Evaluate incoming connection
    #
    sourceNode = plug.source().node()

    if isAnimBlend(sourceNode):

        # Get preferred anim-layer
        #
        bestLayer = getBestAnimLayer(plug)

        if bestLayer.isNull():

            raise TypeError(f'findAnimLayerCurve() "{plug.info}" is not in an anim-layer!')

        # Get anim-blend associated with anim-layer
        #
        animBlends = getMemberBlends(plug)
        inputPlug = None

        if isBaseAnimLayer(bestLayer):

            inputPlug = plugutils.findPlug(animBlends[0], 'inputA')

        else:

            attribute = attributeutils.findAttribute(bestLayer, 'blendNodes')
            animLayers = [plugutils.findConnectedMessage(blend, attribute=attribute).node() for blend in animBlends]

            index = animLayers.index(bestLayer)
            inputPlug = plugutils.findPlug(animBlends[index], 'inputB')

        # Check if this is a compound plug
        # If so, then get the associated indexed child plug
        #
        if inputPlug.isCompound:

            inputChildren = list(plugutils.iterChildren(inputPlug))
            plugChildren = list(plugutils.iterChildren(plug.parent()))
            index = plugChildren.index(plug)

            return inputChildren[index]

        else:

            return inputPlug

    else:

        return plug


def findAnimCurve(plug, create=False):
    """
    Returns the anim-curve associated with the supplied plug.
    If the plug is not animated then a null object is returned!

    :type plug: om.MPlug
    :type create: bool
    :rtype: om.MObject
    """

    # Redundancy check
    #
    if not plugutils.isAnimatable(plug):

        return om.MObject.kNullObj

    # Evaluate animated plug
    #
    otherPlug = findAnimatedPlug(plug)
    isAnimated = plugutils.isAnimated(otherPlug)

    if isAnimated:

        return otherPlug.source().node()

    elif create:

        return createAnimCurve(otherPlug)

    else:

        return om.MObject.kNullObj


def createAnimCurve(plug):
    """
    Adds the supplied plug has an animation curve.

    :type plug: om.MPlug
    :rtype: om.MObject
    """

    # Create anim curve for plug
    # The constructor will also take care of renaming the new anim-curve!
    #
    animCurveType = getAnimCurveType(plug.attribute())
    modifier = om.MDGModifier()

    fnAnimCurve = oma.MFnAnimCurve()
    animCurve = fnAnimCurve.create(plug, animCurveType=animCurveType, modifier=modifier)

    # Cache and execute modifier
    #
    commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()

    return animCurve


def getOppositeBlendInput(plug):
    """
    Returns the other input plug on the supplied blend node.

    :type plug: om.MPlug
    :rtype: om.MPlug
    """

    # Evaluate plug name
    #
    plugName = plug.partialName(useLongNames=True)

    if plugName.startswith('inputA'):

        return plugutils.findPlug(plug.node(), plugName.replace('inputA', 'inputB'))

    elif plugName.startswith('inputB'):

        return plugutils.findPlug(plug.node(), plugName.replace('inputB', 'inputA'))

    else:

        raise TypeError(f'getOppositeBlendInput() expects an input plug ({plug.info} given)!')


def getBlendMode(blend):
    """
    Returns the blend mode for the supplied blend node.

    :type blend: om.MObject
    :rtype: BlendMode
    """

    fnBlend = om.MFnDependencyNode(blend)

    if blend.hasFn(om.MFn.kBlendNodeAdditiveScale):

        return BlendMode(fnBlend.findPlug('accumulationMode', False).asInt())

    elif blend.hasFn(om.MFn.kBlendNodeAdditiveRotation):

        return BlendMode.additive  # As far as I'm aware this only supports additive

    else:

        return BlendMode(fnBlend.findPlug('interpolateMode', False).asInt())


def getInputs(animCurve):
    """
    Returns the keyframe inputs from the supplied anim-curve.

    :type animCurve: om.MObject
    :rtype: List[float]
    """

    # Check if curve is valid
    #
    isNull = animCurve.isNull()

    if not isNull:

        fnAnimCurve = oma.MFnAnimCurve(animCurve)
        return [fnAnimCurve.input(i).value for i in range(fnAnimCurve.numKeys)]

    else:

        return []


def getInputRange(animCurve):
    """
    Returns the keyframe input range from the supplied anim-curve.

    :rtype: Tuple[int, int]
    """

    inputs = getInputs(animCurve)
    numInputs = len(inputs)

    if numInputs > 0:

        return inputs[0], inputs[-1]

    else:

        return None, None


def insertKeys(animCurve, keys, insertAt, animationRange=None, replace=False, change=None):
    """
    Inserts the supplied keys into the specified anim-curve.

    :type animCurve: om.MObject
    :type keys: List[keyframe.Keyframe]
    :type insertAt: Union[int, float]
    :type animationRange: Union[Tuple[int, int], None]
    :type replace: bool
    :type change: Union[oma.MAnimCurveChange, None]
    :rtype: None
    """

    # Redundancy check
    #
    isNull = animCurve.isNull()
    numKeys = len(keys)

    if isNull or numKeys == 0:

        return

    # Check if an animation range was supplied
    #
    startTime, endTime = None, None

    if not stringutils.isNullOrEmpty(animationRange):

        startTime, endTime = animationRange

    else:

        startTime, endTime = keys[0].time, keys[-1].time

    # Check if an anim-curve change was supplied
    #
    if change is None:

        change = oma.MAnimCurveChange()

    # Check if existing keys should be moved or replaced
    #
    timeOffset = insertAt - startTime
    timeLength = endTime - startTime

    newStartTime = startTime + timeOffset
    newEndTime = newStartTime + timeLength

    if replace:

        # Remove inputs to make room for new keys
        #
        clearKeys(animCurve, animationRange=(newStartTime, newEndTime), change=change)

    else:

        # Move inputs to make room for new keys
        #
        moveKeys(animCurve, newStartTime, newEndTime, timeOffset, change=change)

    # Iterate through keys
    #
    fnAnimCurve = oma.MFnAnimCurve(animCurve)

    for key in keys:

        # Insert key at time
        #
        time = om.MTime(key.time + timeOffset, unit=om.MTime.uiUnit())

        i = fnAnimCurve.addKey(
            time,
            key.value,
            tangentInType=key.inTangentType,
            tangentOutType=key.outTangentType,
            change=change
        )

        # Modify tangents
        #
        fnAnimCurve.setWeightsLocked(i, False, change=change)
        fnAnimCurve.setTangentsLocked(i, False, change=change)

        fnAnimCurve.setTangent(i, key.inTangent.x, key.inTangent.y, True, convertUnits=False, change=change)
        fnAnimCurve.setTangent(i, key.outTangent.x, key.outTangent.y, False, convertUnits=False, change=change)

        # Re-lock tangents
        #
        fnAnimCurve.setTangentsLocked(i, True, change=change)

    # Cache changes
    #
    commit(change.redoIt, change.undoIt)


def replaceKeys(animCurve, keys, insertAt=None, animationRange=None, change=None):
    """
    Replaces the keys on the supplied anim-curve.

    :type animCurve: om.MObject
    :type keys: List[keyframe.Keyframe]
    :type insertAt: Union[int, float, None]
    :type animationRange: Union[Tuple[int, int], None]
    :type change: Union[oma.MAnimCurveChange, None]
    :rtype: None
    """

    # Redundancy check
    #
    isNull = animCurve.isNull()
    numKeys = len(keys)

    if isNull or numKeys == 0:

        return

    # Check if an animation range was supplied
    #
    startTime, endTime = None, None

    if not stringutils.isNullOrEmpty(animationRange):

        startTime, endTime = animationRange

    else:

        startTime, endTime = keys[0].time, keys[-1].time

    # Check if an anim-curve change was supplied
    #
    if change is None:

        change = oma.MAnimCurveChange()

    # Iterate through keys
    #
    fnAnimCurve = oma.MFnAnimCurve(animCurve)
    timeOffset = (insertAt - startTime) if isinstance(insertAt, (int, float)) else 0

    clearKeys(animCurve, animationRange=(startTime + timeOffset, endTime + timeOffset), change=change)

    for key in keys:

        # Insert key at time
        #
        time = om.MTime(key.time + timeOffset, unit=om.MTime.uiUnit())

        i = fnAnimCurve.addKey(
            time,
            key.value,
            tangentInType=key.inTangentType,
            tangentOutType=key.outTangentType,
            change=change
        )

        # Modify tangents
        #
        fnAnimCurve.setWeightsLocked(i, False, change=change)
        fnAnimCurve.setTangentsLocked(i, False, change=change)

        fnAnimCurve.setTangent(i, key.inTangent.x, key.inTangent.y, True, convertUnits=False, change=change)
        fnAnimCurve.setTangent(i, key.outTangent.x, key.outTangent.y, False, convertUnits=False, change=change)

        # Re-lock tangents
        #
        fnAnimCurve.setTangentsLocked(i, True, change=change)


def moveKeys(animCurve, startTime, endTime, moveTo, change=None):
    """
    Moves the animation range to the specified time.

    :type animCurve: om.MObject
    :type startTime: int
    :type endTime: int
    :type moveTo: int
    :type change: Union[oma.MAnimCurveChange, None]
    :rtype: None
    """

    # Collect inputs that require moving
    #
    inputs = getInputs(animCurve)

    indices = [i for (i, time) in enumerate(inputs) if time >= startTime]
    numIndices = len(indices)

    if numIndices == 0:

        return

    # Check if an anim-curve change was supplied
    #
    if change is None:

        change = oma.MAnimCurveChange()

    # Move indices
    #
    fnAnimCurve = oma.MFnAnimCurve(animCurve)
    timeOffset = moveTo - startTime

    for index in reversed(indices):

        fnAnimCurve.setInput(index, inputs[index] + timeOffset, change=change)

    # Cache changes
    #
    commit(change.redoIt, change.undoIt)


def clearKeys(animCurve, animationRange=None, change=None):
    """
    Removes all keys from the supplied anim curve.

    :type animCurve: om.MObject
    :type animationRange: Union[Tuple[int, int], None]
    :type change: Union[oma.MAnimCurveChange, None]
    :rtype: None
    """

    # Check if an anim-curve change was supplied
    #
    if change is None:

        change = oma.MAnimCurveChange()

    # Check if an animation range was specified
    #
    fnAnimCurve = oma.MFnAnimCurve(animCurve)

    if not stringutils.isNullOrEmpty(animationRange):

        # Iterate through inputs in reverse
        #
        times = [fnAnimCurve.input(i).value for i in range(fnAnimCurve.numKeys)]
        startTime, endTime = animationRange

        log.debug(f'Removing input range: {startTime} - {endTime}')

        for (i, time) in reversed(list(enumerate(times))):

            # Check if time is in range
            #
            if startTime <= time <= endTime:

                fnAnimCurve.remove(i, change=change)

            else:

                continue

    else:

        # Remove inputs in reverse
        #
        log.debug('Removing all inputs!')

        for i in reversed(list(range(fnAnimCurve.numKeys))):

            fnAnimCurve.remove(i, change=change)

    # Cache change
    #
    commit(change.redoIt, change.undoIt)


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


def copyKeys(plug):
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

        caches[childName] = copyKeys(childPlug)

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

            fnAnimCurve.create(childPlug, animCurveType=animCurveType)
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
    Evaluates if the supplied layer is the base layer.

    :type animLayer: om.MObject
    :rtype: bool
    """

    return getAnimLayerParent(animLayer).isNull()


def getBestAnimLayer(plug):
    """
    Returns the active anim-layer.

    :type plug: om.MPlug
    :rtype: om.MObject
    """

    # Collect selected layers
    #
    animLayer = mc.animLayer(plug.info, query=True, bestLayer=True)

    if not stringutils.isNullOrEmpty(animLayer):

        return dagutils.getMObject(animLayer)

    else:

        return om.MObject.kNullObj


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
        objects = getAnimLayerObjects(childLayer)

        if any([node in objects for node in nodes]):

            animLayers.append(childLayer)

        else:

            continue

    return animLayers


def getMemberBlends(plug):
    """
    Returns a list of anim-blends that lead to the specified anim-layer member.

    :type plug: om.MPlug
    :rtype: List[om.MObject]
    """

    # Redundancy check
    #
    if not plug.isDestination:

        return []

    # Collect up-stream blend nodes
    #
    blend = plug.source().node()

    if isAnimBlend(blend):

        dependencies = dagutils.dependsOn(blend, apiType=blend.apiType())

        return [*reversed(dependencies), blend]

    else:

        return []


def getBlendLayer(blend):
    """
    Returns the anim-layer associated with the supplied blend.

    :type blend: om.MObject
    :rtype: om.MObject
    """

    plug = plugutils.findPlug(blend, 'message')

    animLayers = [otherPlug.node() for otherPlug in plug.destinations() if otherPlug.node().hasFn(om.MFn.kAnimLayer)]
    numAnimLayers = len(animLayers)

    if numAnimLayers == 0:

        return om.MObject.kNullObj

    elif numAnimLayers == 1:

        return animLayers[0]

    else:

        raise TypeError(f'getBlendLayer() expects a unique anim layer ({numAnimLayers} found)!')


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
    plug = plugutils.findPlug(animLayer, 'dagSetMembers')
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


def getAnimLayerIndex(animLayer):
    """
    Returns the index of the supplied layer.

    :type animLayer: om.MObject
    :rtype: int
    """

    # Check if this is the base layer
    #
    if isBaseAnimLayer(animLayer):

        return 0

    else:

        baseLayer = getBaseAnimLayer()
        childLayers = getAnimLayerChildren(baseLayer)

        return tuple(childLayers).index(animLayer) + 1  # Compensating for base layer!


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

    plug = plugutils.findPlug(animLayer, 'childrenLayers')
    return plugutils.getConnectedNodes(plug)


def getAnimLayerBlends(*animLayers):
    """
    Returns the anim curves from the supplied layer.

    :type animLayers: Union[om.MObject, Tuple[om.MObject]]
    :rtype: om.MObjectArray
    """

    # Iterate through anim layers
    #
    blends = om.MObjectArray()

    for animLayer in animLayers:

        plug = plugutils.findPlug(animLayer, 'blendNodes')
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
