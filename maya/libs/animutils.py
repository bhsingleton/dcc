from maya import cmds as mc
from maya.api import OpenMaya as om, OpenMayaAnim as oma
from dcc.dataclasses import vector, keyframe, bezierpoint

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


def synchronizeTangents(plug):
    """
    Synchronizes the in and out tangents on the start and last keys.

    :type plug: om.MPlug
    :rtype: None
    """

    # Check if plug is animated
    #
    if not isAnimated(plug):

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
    if not isAnimated(plug):

        return []

    # Iterate through keys
    #
    fnAnimCurve = oma.MFnAnimCurve(plug)
    keys = [None] * fnAnimCurve.numKeys

    for i in range(fnAnimCurve.numKeys):

        keys[i] = keyframe.Keyframe(
            value=fnAnimCurve.value(i),
            frame=fnAnimCurve.input(i).value,
            inTangent=vector.Vector(*fnAnimCurve.getTangentXY(i, True)),
            outTangent=vector.Vector(*fnAnimCurve.getTangentXY(i, False))
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

        if isAnimated(childPlug):

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
