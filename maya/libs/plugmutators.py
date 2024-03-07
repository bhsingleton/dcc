from maya.api import OpenMaya as om, OpenMayaAnim as oma
from six.moves import collections_abc
from . import sceneutils, plugutils, animutils
from ..decorators.undo import commit
from ..decorators.locksmith import locksmith
from ...python import arrayutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


# region Getters
def getBoolean(plug, **kwargs):
    """
    Gets the boolean value from the supplied plug.

    :type plug: om.MPlug
    :rtype: bool
    """

    return plug.asBool()


def getInteger(plug, **kwargs):
    """
    Gets the integer value from the supplied plug.

    :type plug: om.MPlug
    :rtype: int
    """

    return plug.asInt()


def getFloat(plug, **kwargs):
    """
    Gets the float value from the supplied plug.

    :type plug: om.MPlug
    :rtype: float
    """

    return plug.asFloat()


def getMatrix(plug, **kwargs):
    """
    Gets the matrix value from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MMatrix
    """

    fnMatrixData = om.MFnMatrixData(plug.asMObject())

    if fnMatrixData.isTransformation():

        return fnMatrixData.transformation().asMatrix()

    else:

        return fnMatrixData.matrix()


def getMatrixArray(plug, **kwargs):
    """
    Gets the matrix array from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MMatrixArray
    """

    try:

        return om.MFnMatrixArrayData(plug.asMObject()).array()

    except RuntimeError:

        return om.MMatrixArray()


def getIntArray(plug, **kwargs):
    """
    Gets the float array from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MIntArray
    """

    try:

        return om.MFnIntArrayData(plug.asMObject()).array()

    except RuntimeError:

        return om.MIntArray()


def getDoubleArray(plug, **kwargs):
    """
    Gets the float array from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MDoubleArray
    """

    try:

        return om.MFnDoubleArrayData(plug.asMObject()).array()

    except RuntimeError:

        return om.MDoubleArray()


def getMObject(plug, **kwargs):
    """
    Gets the MObject from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MObject
    """

    return plug.asMObject()


def getString(plug, **kwargs):
    """
    Gets the string value from the supplied plug.

    :type plug: om.MPlug
    :rtype: str
    """

    return plug.asString()


def getStringArray(plug, **kwargs):
    """
    Gets the string array from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MStringArray
    """

    try:

        return om.MFnStringArrayData(plug.asMObject()).array()

    except RuntimeError:

        return om.MStringArray()


def getMAngle(plug, **kwargs):
    """
    Gets the MAngle value from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MAngle
    """

    return plug.asMAngle()


def getMDistance(plug, **kwargs):
    """
    Gets the MDistance value from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MDistance
    """

    return plug.asMDistance()


def getMTime(plug, **kwargs):
    """
    Gets the MTime value from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MTime
    """

    return plug.asMTime()


def getMessage(plug, **kwargs):
    """
    Gets the connected node from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MObject
    """

    source = plug.source()

    if not source.isNull:

        return source.node()

    else:

        return om.MObject.kNullObj


def getGeneric(plug, **kwargs):
    """
    Gets the generic value from the supplied plug.

    :type plug: om.MPlug
    :rtype: None
    """

    return None  # TODO: Implement support for generic types!


def getAny(plug, **kwargs):
    """
    Gets the value from the supplied plug.

    :type plug: om.MPlug
    :rtype: None
    """

    return None  # TODO: Implement support for any types!


def getCompound(plug, **kwargs):
    """
    Returns all the child values from the compound plug.

    :type plug: om.MPlug
    :rtype: dict
    """

    values = {}

    for child in plugutils.iterChildren(plug):

        name = child.partialName(useLongNames=True)
        values[name] = getValue(child)

    return values


__get_numeric_value__ = {
    om.MFnNumericData.kByte: getInteger,
    om.MFnNumericData.kBoolean: getBoolean,
    om.MFnNumericData.kShort: getInteger,
    om.MFnNumericData.kLong: getInteger,
    om.MFnNumericData.kInt: getInteger,
    om.MFnNumericData.kFloat: getFloat,
    om.MFnNumericData.kDouble: getFloat,
    om.MFnNumericData.kMatrix: getMatrix
}


__get_typed_value__ = {
    om.MFnData.kMatrix: getMatrix,
    om.MFnData.kMatrixArray: getMatrixArray,
    om.MFnData.kNurbsCurve: getMObject,
    om.MFnData.kNurbsSurface: getMObject,
    om.MFnData.kLattice: getMObject,
    om.MFnData.kComponentList: getMObject,
    om.MFnData.kMesh: getMObject,
    om.MFnData.kString: getString,
    om.MFnData.kIntArray: getIntArray,
    om.MFnData.kFloatArray: getDoubleArray,
    om.MFnData.kDoubleArray: getDoubleArray,
    om.MFnData.kStringArray: getStringArray,
    om.MFnData.kAny: getAny
}


__get_unit_value__ = {
    om.MFnUnitAttribute.kAngle: getMAngle,
    om.MFnUnitAttribute.kDistance: getMDistance,
    om.MFnUnitAttribute.kTime: getMTime
}


def getNumericType(attribute):
    """
    Gets the numeric type from the supplied numeric attribute.

    :type attribute: om.MObject
    :rtype: int
    """

    return om.MFnNumericAttribute(attribute).numericType()


def getNumericValue(plug, **kwargs):
    """
    Gets the numeric value from the supplied plug.

    :type plug: om.MPlug
    :rtype: Union[bool, int, float, tuple]
    """

    return __get_numeric_value__[getNumericType(plug.attribute())](plug, **kwargs)


def getUnitType(attribute):
    """
    Gets the unit type from the supplied unit attribute.

    :type attribute: om.MObject
    :rtype: int
    """

    return om.MFnUnitAttribute(attribute).unitType()


def getUnitValue(plug, **kwargs):
    """
    Gets the unit value from the supplied plug.

    :type plug: om.MPlug
    :rtype: Union[om.MDistance, om.MAngle]
    """

    return __get_unit_value__[getUnitType(plug.attribute())](plug, **kwargs)


def getDataType(attribute):
    """
    Gets the data type from the supplied typed attribute.

    :type attribute: om.MObject
    :rtype: int
    """

    return om.MFnTypedAttribute(attribute).attrType()


def getTypedValue(plug, **kwargs):
    """
    Gets the typed value from the supplied plug.

    :type plug: om.MPlug
    :rtype: Union[om.MMatrix, om.MObject]
    """

    return __get_typed_value__[getDataType(plug.attribute())](plug, **kwargs)


__get_value__ = {
    om.MFn.kNumericAttribute: getNumericValue,
    om.MFn.kUnitAttribute: getUnitValue,
    om.MFn.kTimeAttribute: getUnitValue,
    om.MFn.kTypedAttribute: getTypedValue,
    om.MFn.kEnumAttribute: getInteger,
    om.MFn.kMatrixAttribute: getMatrix,
    om.MFn.kMessageAttribute: getMessage,
    om.MFn.kCompoundAttribute: getCompound,
    om.MFn.kDoubleAngleAttribute: getMAngle,
    om.MFn.kDoubleLinearAttribute: getMDistance,
    om.MFn.kGenericAttribute: getGeneric
}


def getValue(plug, convertUnits=True, bestLayer=False):
    """
    Gets the value from the supplied plug.
    Enabling `convertUnits` will convert any internal units to UI values!
    Whereas `bestLayer` affects whether the value from the active anim-layer is returned instead!

    :type plug: om.MPlug
    :type convertUnits: bool
    :type bestLayer: bool
    :rtype: Any
    """

    # Check if this is a null plug
    #
    if plug.isNull:

        return None

    # Evaluate plug type
    #
    if plug.isArray and not plug.isElement:

        # Iterate through existing indices
        #
        indices = plug.getExistingArrayAttributeIndices()
        numIndices = len(indices)

        plugValues = [None] * numIndices

        for (physicalIndex, logicalIndex) in enumerate(indices):

            element = plug.elementByLogicalIndex(logicalIndex)
            plugValues[physicalIndex] = getValue(element, convertUnits=convertUnits)

        return plugValues

    elif plugutils.isCompoundNumeric(plug):

        # Return list of values from parent plug
        #
        return [getValue(child, convertUnits=convertUnits) for child in plugutils.iterChildren(plug)]

    else:

        # Check if active anim-layer should be evaluated
        #
        if bestLayer and plugutils.isAnimated(plug):

            plug = animutils.findAnimatedPlug(plug)
            return getValue(plug, convertUnits=convertUnits)

        # Get value from plug
        # Check if any units require converting
        #
        attributeType = plugutils.getApiType(plug)
        plugValue = __get_value__[attributeType](plug)

        if convertUnits and isinstance(plugValue, (om.MDistance, om.MAngle, om.MTime)):

            return plugValue.asUnits(plugValue.uiUnit())

        else:

            return plugValue
# endregion


# region Setters
def setBoolean(plug, value, modifier=None, **kwargs):
    """
    Updates the boolean value on the supplied plug.

    :type plug: om.MPlug
    :type value: bool
    :type modifier: om.MDGModifier
    :rtype: None
    """

    modifier.newPlugValueBool(plug, bool(value))


def setInteger(plug, value, modifier=None, **kwargs):
    """
    Updates the integer value for the supplied plug.

    :type plug: om.MPlug
    :type value: int
    :type modifier: om.MDGModifier
    :rtype: None
    """

    modifier.newPlugValueInt(plug, int(value))


def setFloat(plug, value, modifier=None, **kwargs):
    """
    Updates the float value for the supplied plug.

    :type plug: om.MPlug
    :type value: float
    :type modifier: om.MDGModifier
    :rtype: None
    """

    modifier.newPlugValueFloat(plug, float(value))


def setMatrix(plug, value, modifier=None, **kwargs):
    """
    Updates the matrix value on the supplied plug.

    :type plug: om.MPlug
    :type value: om.MMatrix
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Create new matrix data object
    #
    fnMatrixData = om.MFnMatrixData()
    matrixData = fnMatrixData.create()

    fnMatrixData.set(value)

    # Assign data object to plug
    #
    modifier.newPlugValue(plug, matrixData)


def setMatrixArray(plug, value, modifier=None, **kwargs):
    """
    Updates the matrix array for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[List[om.MMatrix], om.MMatrixArray]
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check value type
    #
    matrixArrayData = None

    if isinstance(value, (list, tuple)):

        # Create new string array data
        #
        fnMatrixArrayData = om.MFnMatrixArrayData()
        matrixArrayData = fnMatrixArrayData.create()

        fnMatrixArrayData.set(value)

    elif isinstance(value, om.MMatrixArray):

        matrixArrayData = om.MFnMatrixArrayData(value).object()

    elif isinstance(value, om.MObject):

        matrixArrayData = value

    else:

        raise TypeError('setMatrixArray() expects a sequence of matrices!')

    # Assign data object to plug
    #
    modifier.newPlugValue(plug, matrixArrayData)


def setIntArray(plug, value, modifier=None, **kwargs):
    """
    Updates the double array for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[List[int], om.MIntArray]
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check value type
    #
    intArrayData = None

    if isinstance(value, (list, tuple)):

        # Create new string array data
        #
        fnIntArrayData = om.MFnDoubleArrayData()
        intArrayData = fnIntArrayData.create()

        fnIntArrayData.set(value)

    elif isinstance(value, (om.MFloatArray, om.MDoubleArray)):

        intArrayData = om.MFnDoubleArrayData(value).object()

    elif isinstance(value, om.MObject):

        intArrayData = value

    else:

        raise TypeError('setIntArray() expects a sequence of integers (%s given)!' % type(value).__name__)

    # Assign MObject to plug
    #
    modifier.newPlugValue(plug, intArrayData)


def setDoubleArray(plug, value, modifier=None, **kwargs):
    """
    Updates the double array for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[List[float], om.MFloatArray, om.MDoubleArray]
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check value type
    #
    doubleArrayData = None

    if isinstance(value, (list, tuple)):

        # Create new string array data
        #
        fnDoubleArrayData = om.MFnDoubleArrayData()
        doubleArrayData = fnDoubleArrayData.create()

        fnDoubleArrayData.set(value)

    elif isinstance(value, (om.MFloatArray, om.MDoubleArray)):

        doubleArrayData = om.MFnDoubleArrayData(value).object()

    elif isinstance(value, om.MObject):

        doubleArrayData = value

    else:

        raise TypeError('setDoubleArray() expects a sequence of floats (%s given)!' % type(value).__name__)

    # Assign MObject to plug
    #
    modifier.newPlugValue(plug, doubleArrayData)


def setMObject(plug, value, modifier=None, **kwargs):
    """
    Updates the MObject for the supplied plug.

    :type plug: om.MPlug
    :type value: om.MObject
    :type modifier: om.MDGModifier
    :rtype: None
    """

    modifier.newPlugValue(plug, value)


def setString(plug, value, modifier=None, **kwargs):
    """
    Updates the string value for the supplied plug.

    :type plug: om.MPlug
    :type value: str
    :type modifier: om.MDGModifier
    :rtype: None
    """

    modifier.newPlugValueString(plug, value)


def setStringArray(plug, value, modifier=None, **kwargs):
    """
    Gets the string array from the supplied plug.

    :type plug: om.MPlug
    :type value: om.MStringArray
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check value type
    #
    stringArrayData = None

    if isinstance(value, (list, tuple)):

        # Create new string array data
        #
        fnStringArrayData = om.MFnStringArrayData()
        stringArrayData = fnStringArrayData.create()

        fnStringArrayData.set(value)

    elif isinstance(value, om.MObject):

        stringArrayData = value

    else:

        raise TypeError('setStringArray() expects a sequence of strings (%s given)!' % type(value).__name__)

    # Assign data object to plug
    #
    modifier.newPlugValue(plug, stringArrayData)


def setMAngle(plug, value, modifier=None, **kwargs):
    """
    Updates the MAngle value for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[int, float, om.MAngle]
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check value type
    #
    if not isinstance(value, om.MAngle):

        convertUnits = kwargs.get('convertUnits', True)
        unit = om.MAngle.uiUnit() if convertUnits else om.MAngle.internalUnit()

        value = om.MAngle(value, unit=unit)

    # Assign value to plug
    #
    modifier.newPlugValueMAngle(plug, value)


def setMDistance(plug, value, modifier=None, **kwargs):
    """
    Updates the MDistance value for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[int, float, om.MDistance]
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check value type
    #
    if not isinstance(value, om.MDistance):

        convertUnits = kwargs.get('convertUnits', True)
        unit = om.MDistance.uiUnit() if convertUnits else om.MDistance.internalUnit()

        value = om.MDistance(value, unit=unit)

    # Assign value to plug
    #
    modifier.newPlugValueMDistance(plug, value)


def setMTime(plug, value, modifier=None, **kwargs):
    """
    Updates the MTime value for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[int, float, om.MTime]
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check value type
    #
    if not isinstance(value, om.MTime):

        value = om.MTime(value, om.MTime.uiUnit())

    # Assign value to plug
    #
    modifier.newPlugValueMTime(plug, value)


def setMessage(plug, value, modifier=None, **kwargs):
    """
    Updates the connected message plug node.

    :type plug: om.MPlug
    :type value: om.MObject
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check api type
    #
    if not value.isNull():

        otherPlug = om.MFnDependencyNode(value).findPlug('message', True)
        plugutils.connectPlugs(otherPlug, plug, force=True)

    else:

        plugutils.breakConnections(plug, source=True, destination=False)


def setCompound(plug, values, modifier=None, **kwargs):
    """
    Updates the compound value for the supplied plug.

    :type plug: om.MPlug
    :type values: Union[List[Any], Dict[str, Any]]
    :type modifier: om.MDGModifier
    :rtype: None
    """

    # Check value type
    #
    if isinstance(values, collections_abc.MutableMapping):

        # Iterate through values
        #
        fnDependNode = om.MFnDependencyNode(plug.node())

        for (name, value) in values.items():

            # Check if node has attribute
            #
            if not fnDependNode.hasAttribute(name):

                continue

            # Get child plug
            # TODO: Improve child plug lookup logic
            #
            attribute = fnDependNode.attribute(name)
            fnAttribute = om.MFnAttribute(attribute)

            parentAttribute = fnAttribute.parent
            hasParent = plug != parentAttribute and not parentAttribute.isNull()

            childPlug = None

            if hasParent:

                childPlug = plug.child(parentAttribute).child(attribute)

            else:

                childPlug = plug.child(attribute)

            # Update child plug
            #
            setValue(childPlug, value, modifier=modifier, **kwargs)

    elif arrayutils.isArrayLike(values):  # Maya dataclasses aren't derived from the `Sequence` abstract base class!

        # Iterate through values
        #
        fnCompoundAttribute = om.MFnCompoundAttribute(plug.attribute())
        childCount = fnCompoundAttribute.numChildren()

        for (i, value) in enumerate(values):

            # Check if indexed value is in range
            #
            if 0 <= i < childCount:

                childAttribute = fnCompoundAttribute.child(i)
                childPlug = plug.child(childAttribute)

                setValue(childPlug, values[i], **kwargs)

            else:

                continue

    else:

        raise TypeError('setCompound() expects either a dict or tuple (%s given)!' % type(values).__name__)


__set_numeric_value__ = {
    om.MFnNumericData.kByte: setInteger,
    om.MFnNumericData.kBoolean: setBoolean,
    om.MFnNumericData.kShort: setInteger,
    om.MFnNumericData.kLong: setInteger,
    om.MFnNumericData.kInt: setInteger,
    om.MFnNumericData.kFloat: setFloat,
    om.MFnNumericData.kDouble: setFloat,
    om.MFnNumericData.kMatrix: setMatrix
}


__set_typed_value__ = {
    om.MFnData.kMatrix: setMatrix,
    om.MFnData.kMatrixArray: setMatrixArray,
    om.MFnData.kNurbsCurve: setMObject,
    om.MFnData.kNurbsSurface: setMObject,
    om.MFnData.kLattice: setMObject,
    om.MFnData.kComponentList: setMObject,
    om.MFnData.kMesh: setMObject,
    om.MFnData.kString: setString,
    om.MFnData.kIntArray: setIntArray,
    om.MFnData.kFloatArray: setDoubleArray,
    om.MFnData.kDoubleArray: setDoubleArray,
    om.MFnData.kStringArray: setStringArray
}


__set_unit_value__ = {
    om.MFnUnitAttribute.kAngle: setMAngle,
    om.MFnUnitAttribute.kDistance: setMDistance,
    om.MFnUnitAttribute.kTime: setMTime
}


def setNumericValue(plug, value, modifier=None, **kwargs):
    """
    Updates the numeric value for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[bool, int, float, tuple]
    :type modifier: om.MDGModifier
    :key force: bool
    :rtype: None
    """

    return __set_numeric_value__[getNumericType(plug.attribute())](plug, value, modifier=modifier, **kwargs)


def setUnitValue(plug, value, modifier=None, **kwargs):
    """
    Updates the unit value for the supplied unit plug.

    :type plug: om.MPlug
    :type value: Union[om.MDistance, om.MAngle]
    :type modifier: om.MDGModifier
    :key force: bool
    :rtype: None
    """

    return __set_unit_value__[getUnitType(plug.attribute())](plug, value, modifier=modifier, **kwargs)


def setTypedValue(plug, value, modifier=None, **kwargs):
    """
    Gets the typed value from the supplied plug.

    :type plug: om.MPlug
    :type value: Union[om.MMatrix, om.MObject]
    :type modifier: om.MDGModifier
    :key force: bool
    :rtype: None
    """

    return __set_typed_value__[getDataType(plug.attribute())](plug, value, modifier=modifier, **kwargs)


__set_value__ = {
    om.MFn.kNumericAttribute: setNumericValue,
    om.MFn.kUnitAttribute: setUnitValue,
    om.MFn.kTimeAttribute: setMTime,
    om.MFn.kDoubleAngleAttribute: setUnitValue,
    om.MFn.kDoubleLinearAttribute: setUnitValue,
    om.MFn.kTypedAttribute: setTypedValue,
    om.MFn.kEnumAttribute: setInteger,
    om.MFn.kMatrixAttribute: setMatrix,
    om.MFn.kMessageAttribute: setMessage,
    om.MFn.kCompoundAttribute: setCompound,
    om.MFn.kAttribute2Float: setCompound,
    om.MFn.kAttribute3Float: setCompound,
    om.MFn.kAttribute2Double: setCompound,
    om.MFn.kAttribute3Double: setCompound,
    om.MFn.kAttribute4Double: setCompound,
    om.MFn.kAttribute2Int: setCompound,
    om.MFn.kAttribute3Int: setCompound,
    om.MFn.kAttribute2Short: setCompound,
    om.MFn.kAttribute3Short: setCompound
}


@locksmith
def setValue(plug, value, modifier=None, **kwargs):
    """
    Updates the value for the supplied plug.
    An optional force flag can be supplied to unlock the node before setting.

    :type plug: om.MPlug
    :type value: Any
    :type modifier: Union[om.MDGModifier, None]
    :rtype: None
    """

    # Check if this is a null plug
    #
    if plug.isNull:

        return None
    
    # Check if a dag modifier was supplied
    #
    if modifier is None:
        
        modifier = om.MDGModifier()
    
    # Evaluate plug type
    #
    if plug.isArray and not plug.isElement:

        # Check value type
        #
        if not (arrayutils.isArray(value) or arrayutils.isArrayLike(value)):

            raise TypeError(f'setValue() expects a sequence of values ({type(value).__name__} given)!')

        # Check if space should be reallocated
        #
        numElements = plug.numElements()
        numItems = len(value)

        if numItems > numElements:

            plug.setNumElements(numItems)

        elif numItems < numElements:

            plugutils.removeMultiInstances(plug, list(range(numItems, numElements)))

        else:

            pass

        # Assign values to plug elements
        #
        for (physicalIndex, item) in enumerate(value):

            element = plug.elementByLogicalIndex(physicalIndex)
            setValue(element, item, modifier=modifier, **kwargs)

        # Remove any excess elements
        #
        if numElements > numItems:

            plugutils.removeMultiInstances(plug, list(range(numItems, numElements)))

    elif plug.isCompound:

        # Assign values to children
        #
        setCompound(plug, value, modifier=modifier, **kwargs)

    else:

        # Check if plug is changeable
        #
        state = plug.isFreeToChange()

        if state != om.MPlug.kFreeToChange:

            log.debug(f'Plug is not free-to-change: {plug.info}')
            return

        # Check if auto-key is enabled
        #
        autoKey = sceneutils.autoKey()

        if autoKey and plugutils.isAnimatable(plug):

            keyValue(plug, value)

        else:

            attributeType = plugutils.getApiType(plug)
            __set_value__[attributeType](plug, value, modifier=modifier, **kwargs)

    # Cache and execute modifier
    #
    commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()
    

def resetValue(plug, modifier=None, **kwargs):
    """
    Resets the value for the supplied plug back to its default value.

    :type plug: om.MPlug
    :type modifier: Union[om.MDGModifier, None]
    :rtype: None
    """

    # Check if this is a null plug
    #
    if plug.isNull:

        return None

    # Check if this is an array plug
    #
    if plug.isArray and not plug.isElement:

        # Iterate through elements
        #
        numElements = plug.numElements()

        for i in range(numElements):

            resetValue(plug.elementByPhysicalIndex(i), modifier=modifier, **kwargs)

    elif plug.isCompound:

        # Iterate through children
        #
        numChildren = plug.numChildren()

        for i in range(numChildren):

            resetValue(plug.child(i), modifier=modifier, **kwargs)

    else:

        # Get default value
        #
        attribute = plug.attribute()
        defaultValue = om.MObject.kNullObj

        if attribute.hasFn(om.MFn.kNumericAttribute):

            defaultValue = om.MFnNumericAttribute(attribute).default

        elif attribute.hasFn(om.MFn.kUnitAttribute):

            defaultValue = om.MFnUnitAttribute(attribute).default

        elif attribute.hasFn(om.MFn.kEnumAttribute):

            defaultValue = om.MFnEnumAttribute(attribute).default

        else:

            pass

        # Reset plug
        #
        setValue(plug, defaultValue, modifier=modifier, **kwargs)
# endregion


# region Keyers
def keyValue(plug, value, time=None, convertUnits=True, change=None):
    """
    Keys the plug at the specified time.

    :type plug: om.MPlug
    :type value: Any
    :type time: Union[int, float, None]
    :type convertUnits: bool
    :type change: oma.MAnimCurveChange
    :rtype: None
    """

    # Redundancy check
    #
    if not plugutils.isAnimatable(plug):

        return

    # Check if value requires unit conversion
    #
    if convertUnits:

        animCurveType = animutils.getAnimCurveType(plug.attribute())
        value = animutils.uiToInternalUnit(value, animCurveType=animCurveType)

    # Check if an anim-curve change was supplied
    #
    if change is None:

        change = oma.MAnimCurveChange()

    # Check if plug is in an anim-layer
    # If so, adjust the value to compensate for the additive layer!
    # TODO: Add support for override layers!
    #
    animatedPlug = animutils.findAnimatedPlug(plug)
    animatedNode = animatedPlug.node()

    isAnimBlend = animutils.isAnimBlend(animatedNode)

    if isAnimBlend:

        otherPlug = animutils.getOppositeBlendInput(animatedPlug)
        otherValue = getValue(otherPlug, convertUnits=False)

        blendMode = animutils.getBlendMode(animatedNode)

        if blendMode == 0:  # Additive

            value = animutils.expandUnits(value, asInternal=True) - animutils.expandUnits(otherValue, asInternal=True)

        elif blendMode == 1:  # Multiply

            value = animutils.expandUnits(value, asInternal=True) / animutils.expandUnits(otherValue, asInternal=True)

        else:

            raise NotImplementedError(f'keyValue() no support for "{value.name}" blend mode!')

    # Find associated anim-curve from plug
    #
    animCurve = animutils.findAnimCurve(animatedPlug, create=True)
    fnAnimCurve = oma.MFnAnimCurve(animCurve)

    # Check if time input already exists
    #
    time = sceneutils.getTime() if time is None else time
    index = fnAnimCurve.find(time)

    if index is None:

        log.debug(f'Updating {fnAnimCurve.name()} anim-curve: {value} @ {time}')
        fnAnimCurve.addKey(
            om.MTime(time, unit=om.MTime.uiUnit()),
            value,
            tangentInType=fnAnimCurve.kTangentAuto,
            tangentOutType=fnAnimCurve.kTangentAuto,
            change=change
        )

    else:

        log.debug(f'Updating {fnAnimCurve.name()} anim-curve: {value} @ {time}')
        fnAnimCurve.setValue(index, value, change=change)

    # Cache anim-curve changes
    #
    commit(change.redoIt, change.undoIt)
# endregion
