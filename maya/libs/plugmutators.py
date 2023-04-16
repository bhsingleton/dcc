from maya.api import OpenMaya as om
from . import plugutils
from ..decorators.locksmith import locksmith
from ..decorators.autokey import autokey
from ..decorators.undo import commit

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

    return om.MFnMatrixArrayData(plug.asMObject()).array()


def getDoubleArray(plug, **kwargs):
    """
    Gets the float array from the supplied plug.

    :type plug: om.MPlug
    :rtype: om.MDoubleArray
    """

    return om.MFnDoubleArrayData(plug.asMObject()).array()


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

    return om.MFnStringArrayData(plug.asMObject()).array()


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
    Gets the connected message plug node.

    :type plug: om.MPlug
    :rtype: om.MObject
    """

    source = plug.source()

    if not source.isNull:

        return source.node()

    else:

        return om.MObject.kNullObj


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
    om.MFnData.kFloatArray: getDoubleArray,
    om.MFnData.kDoubleArray: getDoubleArray,
    om.MFnData.kString: getString,
    om.MFnData.kStringArray: getStringArray
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
    om.MFn.kTypedAttribute: getTypedValue,
    om.MFn.kEnumAttribute: getInteger,
    om.MFn.kMatrixAttribute: getMatrix,
    om.MFn.kMessageAttribute: getMessage,
    om.MFn.kCompoundAttribute: getCompound,
    om.MFn.kDoubleAngleAttribute: getMAngle,
    om.MFn.kDoubleLinearAttribute: getMDistance
}


def getValue(plug, convertUnits=True):
    """
    Gets the value from the supplied plug.
    An optional `convertUnits` flag can be specified to convert values to UI units!

    :type plug: om.MPlug
    :type convertUnits: bool
    :rtype: object
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

    elif isCompoundNumeric(plug):

        # Return list of values from parent plug
        #
        return [getValue(child, convertUnits=convertUnits) for child in plugutils.iterChildren(plug)]

    else:

        # Get value from plug
        # Check if units should also be converted
        #
        attributeType = plugutils.getApiType(plug)
        plugValue = __get_value__[attributeType](plug)

        if convertUnits and isinstance(plugValue, (om.MDistance, om.MAngle, om.MTime)):

            return plugValue.asUnits(plugValue.uiUnit())

        else:

            return plugValue


def isCompoundNumeric(plug):
    """
    Evaluates if the supplied plug represents a compound numeric value.

    :type plug: om.MPlug
    :rtype: bool
    """

    # Check if the plug has children
    #
    if plug.isCompound:

        return all([isNumeric(child) for child in plugutils.iterChildren(plug)])

    else:

        return False


def isNumeric(plug):
    """
    Evaluates if the supplied plug is numeric.

    :type plug: om.MPlug
    :rtype: bool
    """

    attribute = plug.attribute()
    return attribute.hasFn(om.MFn.kNumericAttribute) or attribute.hasFn(om.MFn.kUnitAttribute)
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

        value = om.MAngle(value, unit=om.MAngle.uiUnit())

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

        value = om.MDistance(value, unit=om.MDistance.uiUnit())

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
    if isinstance(values, dict):

        # Iterate through values
        #
        fnDependNode = om.MFnDependencyNode(plug.node())

        for (name, value) in values.items():

            # Check if node has attribute
            #
            if not fnDependNode.hasAttribute(name):

                continue

            # Get child plug
            #
            childAttribute = fnDependNode.attribute(name)
            childPlug = plug.child(childAttribute)

            setValue(childPlug, value, modifier=modifier, **kwargs)

    elif hasattr(values, '__getitem__') and hasattr(values, '__len__'):

        # Iterate through values
        #
        fnCompoundAttribute = om.MFnCompoundAttribute(plug.attribute())
        childCount = fnCompoundAttribute.numChildren()

        for i in range(childCount):

            # Get child plug
            #
            childAttribute = fnCompoundAttribute.child(i)
            childPlug = plug.child(childAttribute)

            setValue(childPlug, values[i], **kwargs)

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
    om.MFnData.kFloatArray: setDoubleArray,
    om.MFnData.kDoubleArray: setDoubleArray,
    om.MFnData.kString: setString,
    om.MFnData.kStringArray: setStringArray,
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
@autokey
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
        if not isinstance(value, (list, tuple)):

            raise TypeError('setValue() expects a sequence of values for array plugs!')

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

        # Assign sequence to plug elements
        #
        for (physicalIndex, item) in enumerate(value):

            element = plug.elementByLogicalIndex(physicalIndex)
            setValue(element, item, modifier=modifier, **kwargs)

        # Remove any excess elements
        #
        if numElements > numItems:

            plugutils.removeMultiInstances(plug, list(range(numItems, numElements)))

    elif plug.isCompound:

        setCompound(plug, value, modifier=modifier, **kwargs)

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
