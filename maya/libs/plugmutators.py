from maya.api import OpenMaya as om
from . import plugutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


# region Getters
def getBoolean(plug, context=om.MDGContext.kNormal):
    """
    Gets the boolean value from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: bool
    """

    return plug.asBool(context=context)


def getInteger(plug, context=om.MDGContext.kNormal):
    """
    Gets the integer value from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: int
    """

    return plug.asInt(context=context)


def getFloat(plug, context=om.MDGContext.kNormal):
    """
    Gets the float value from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: float
    """

    return plug.asFloat(context=context)


def getMatrix(plug, context=om.MDGContext.kNormal):
    """
    Gets the matrix value from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MMatrix
    """

    return om.MFnMatrixData(plug.asMObject(context=context)).matrix()


def getMatrixArray(plug, context=om.MDGContext.kNormal):
    """
    Gets the matrix array from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MMatrixArray
    """

    return om.MFnMatrixArrayData(plug.asMObject(context=context)).array()


def getDoubleArray(plug, context=om.MDGContext.kNormal):
    """
    Gets the float array from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MDoubleArray
    """

    return om.MFnDoubleArrayData(plug.asMObject(context=context)).array()


def getMObject(plug, context=om.MDGContext.kNormal):
    """
    Gets the MObject from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MObject
    """

    return plug.asMObject(context=context)


def getString(plug, context=om.MDGContext.kNormal):
    """
    Gets the string value from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: str
    """

    return plug.asString(context=context)


def getStringArray(plug, context=om.MDGContext.kNormal):
    """
    Gets the string array from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MStringArray
    """

    return om.MFnStringArrayData(plug.asMObject(context=context)).array()


def getMAngle(plug, context=om.MDGContext.kNormal):
    """
    Gets the MAngle value from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MAngle
    """

    return plug.asMAngle(context=context)


def getMDistance(plug, context=om.MDGContext.kNormal):
    """
    Gets the MDistance value from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MDistance
    """

    return plug.asMDistance(context=context)


def getMTime(plug, context=om.MDGContext.kNormal):
    """
    Gets the MTime value from the supplied plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MTime
    """

    return plug.asMTime(context=context)


def getMessage(plug, context=om.MDGContext.kNormal):
    """
    Gets the connected message plug node.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: om.MObject
    """

    source = plug.source()

    if not source.isNull:

        return source.node()

    else:

        return om.MObject.kNullObj


def getCompound(plug, context=om.MDGContext.kNormal):
    """
    Returns all the child values from the compound plug.

    :type plug: om.MPlug
    :type context: om.MDGContext
    :rtype: dict
    """

    numChildren = plug.numChildren()
    values = {}

    for i in range(numChildren):

        child = plug.child(i)
        childName = child.partialName(useLongNames=True)

        values[childName] = getValue(child, context=context)

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


def getNumericValue(plug):
    """
    Gets the numeric value from the supplied plug.

    :type plug: om.MPlug
    :rtype: Union[bool, int, float, tuple]
    """

    return __get_numeric_value__[getNumericType(plug.attribute())](plug)


def getUnitType(attribute):
    """
    Gets the unit type from the supplied unit attribute.

    :type attribute: om.MObject
    :rtype: int
    """

    return om.MFnUnitAttribute(attribute).unitType()


def getUnitValue(plug):
    """
    Gets the unit value from the supplied plug.

    :type plug: om.MPlug
    :rtype: Union[om.MDistance, om.MAngle]
    """

    return __get_unit_value__[getUnitType(plug.attribute())](plug)


def getDataType(attribute):
    """
    Gets the data type from the supplied typed attribute.

    :type attribute: om.MObject
    :rtype: int
    """

    return om.MFnTypedAttribute(attribute).attrType()


def getTypedValue(plug):
    """
    Gets the typed value from the supplied plug.

    :type plug: om.MPlug
    :rtype: Union[om.MMatrix, om.MObject]
    """

    return __get_typed_value__[getDataType(plug.attribute())](plug)


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


def getValue(plug, convertUnits=True, context=om.MDGContext.kNormal):
    """
    Gets the value from the supplied plug.

    :type plug: om.MPlug
    :type convertUnits: bool
    :type context: om.MDGContext
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
            plugValues[physicalIndex] = getValue(element, convertUnits=convertUnits, context=context)

        return plugValues

    elif isCompoundNumeric(plug):

        # Return list of values from parent plug
        #
        return [getValue(plug.child(i), convertUnits=convertUnits, context=context) for i in range(plug.numChildren())]

    else:

        # Get value from plug
        # Check if units should also be converted
        #
        attributeType = plugutils.getApiType(plug)
        plugValue = __get_value__[attributeType](plug)

        if convertUnits and isinstance(plugValue, (om.MDistance, om.MAngle, om.MTime)):

            return plugValue.value

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

        return all([isNumeric(plug.child(i)) for i in range(plug.numChildren())])

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


def getAliases(dependNode):
    """
    Returns a dictionary of all the attribute aliases belonging to the supplied node.
    The keys represent the alias name and the values represent the original name.

    :type dependNode: om.MObject
    :rtype: Dict[str, str]
    """

    return dict(om.MFnDependencyNode(dependNode).getAliasList())
# endregion


# region Setters
def toggleLock(func):
    """
    Returns a function wrapper that toggles the lock state on a plug.

    :type func: function
    :rtype: function
    """

    # Define wrapper function
    #
    def wrapper(*args, **kwargs):

        # Check number of arguments
        #
        numArgs = len(args)

        if numArgs == 2:

            # Check if force was used
            #
            plug = args[0]
            value = args[1]

            force = kwargs.get('force', False)

            if force:

                plug.isLocked = False

            # Update plug value
            #
            func(plug, value)

            # Check if plug should be relocked
            #
            if force:

                plug.isLocked = True

        else:

            raise TypeError('toggleLock() expects 1 argument (%s given)!' % numArgs)

    # Return wrapper function
    #
    return wrapper


@toggleLock
def setBoolean(plug, value):
    """
    Updates the boolean value on the supplied plug.

    :type plug: om.MPlug
    :type value: bool
    :rtype: bool
    """

    plug.setBool(bool(value))


@toggleLock
def setInteger(plug, value):
    """
    Updates the integer value for the supplied plug.

    :type plug: om.MPlug
    :type value: int
    :rtype: None
    """

    plug.setInt(int(value))


@toggleLock
def setFloat(plug, value):
    """
    Updates the float value for the supplied plug.

    :type plug: om.MPlug
    :type value: float
    :rtype: None
    """

    plug.setFloat(float(value))


@toggleLock
def setMatrix(plug, matrix):
    """
    Updates the matrix value on the supplied plug.

    :type plug: om.MPlug
    :type matrix: om.MMatrix
    :rtype: None
    """

    # Create new matrix data object
    #
    fnMatrixData = om.MFnMatrixData()
    matrixData = fnMatrixData.create()

    # Assign matrix to empty object
    #
    fnMatrixData.set(matrix)

    # Assign MObject on plug
    #
    plug.setMObject(matrixData)


@toggleLock
def setMatrixArray(plug, value):
    """
    Updates the matrix array for the supplied plug.

    :type plug: om.MPlug
    :type value: om.MMatrixArray
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

    # Assign MObject to plug
    #
    plug.setMObject(matrixArrayData)


@toggleLock
def setDoubleArray(plug, value):
    """
    Updates the double array for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[om.MFloatArray, om.MDoubleArray]
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

        raise TypeError('setDoubleArray() expects a sequence of floats!')

    # Assign MObject to plug
    #
    plug.setMObject(doubleArrayData)


@toggleLock
def setMObject(plug, value):
    """
    Updates the MObject for the supplied plug.

    :type plug: om.MPlug
    :type value: om.MObject
    :rtype: None
    """

    return plug.setMObject(value)


@toggleLock
def setString(plug, value):
    """
    Updates the string value for the supplied plug.

    :type plug: om.MPlug
    :type value: str
    :rtype: None
    """

    return plug.setString(str(value))


@toggleLock
def setStringArray(plug, value):
    """
    Gets the string array from the supplied plug.

    :type plug: om.MPlug
    :type value: om.MStringArray
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

        raise TypeError('setStringArray() expects a sequence of strings!')

    # Assign MObject to plug
    #
    plug.setMObject(stringArrayData)


@toggleLock
def setMAngle(plug, angle):
    """
    Updates the MAngle value for the supplied plug.

    :type plug: om.MPlug
    :type angle: om.MAngle
    :rtype: None
    """

    # Check value type
    #
    if not isinstance(angle, om.MAngle):

        angle = om.MAngle(angle, unit=om.MAngle.uiUnit())

    return plug.setMAngle(angle)


@toggleLock
def setMDistance(plug, distance):
    """
    Updates the MDistance value for the supplied plug.

    :type plug: om.MPlug
    :type distance: om.MDistance
    :rtype: None
    """

    # Check value type
    #
    if not isinstance(distance, om.MDistance):

        distance = om.MDistance(distance, unit=om.MDistance.uiUnit())

    return plug.setMDistance(distance)


@toggleLock
def setMTime(plug, time):
    """
    Updates the MTime value for the supplied plug.

    :type plug: om.MPlug
    :type time: om.MTime
    :rtype: None
    """

    # Check value type
    #
    if not isinstance(time, om.MTime):

        time = om.MTime(time, om.MTime.uiUnit())

    return plug.setMTime(time)


@toggleLock
def setMessage(plug, dependNode):
    """
    Updates the connected message plug node.

    :type plug: om.MPlug
    :type dependNode: om.MObject
    :rtype: None
    """

    # Check api type
    #
    if not dependNode.isNull():

        otherPlug = om.MFnDependencyNode(dependNode).findPlug('message', True)
        plugutils.connectPlugs(otherPlug, plug, force=True)

    else:

        plugutils.breakConnections(plug, source=True, destination=False)


@toggleLock
def setCompound(plug, values):
    """
    Updates the compound value for the supplied plug.

    :type plug: om.MPlug
    :type values: Union[list, dict]
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

            setValue(childPlug, value)

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

            setValue(childPlug, values[i])

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


@toggleLock
def setNumericValue(plug, value):
    """
    Updates the numeric value for the supplied plug.

    :type plug: om.MPlug
    :type value: Union[bool, int, float, tuple]
    :rtype: None
    """

    return __set_numeric_value__[getNumericType(plug.attribute())](plug, value)


@toggleLock
def setUnitValue(plug, value):
    """
    Updates the unit value for the supplied unit plug.

    :type plug: om.MPlug
    :type value: Union[om.MDistance, om.MAngle]
    :rtype: None
    """

    return __set_unit_value__[getUnitType(plug.attribute())](plug, value)


@toggleLock
def setTypedValue(plug, value):
    """
    Gets the typed value from the supplied plug.

    :type plug: om.MPlug
    :type value: Union[om.MMatrix, om.MObject]
    :rtype: None
    """

    return __set_typed_value__[getDataType(plug.attribute())](plug, value)


__set_value__ = {
    om.MFn.kNumericAttribute: setNumericValue,
    om.MFn.kUnitAttribute: setUnitValue,
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


def setValue(plug, value, force=False):
    """
    Updates the value for the supplied plug.
    An optional force flag can be supplied to unlock the node before setting.

    :type plug: om.MPlug
    :type value: Any
    :type force: bool
    :rtype: None
    """

    # Check if this is a null plug
    #
    if plug.isNull:

        return None

    # Evaluate plug type
    #
    if plug.isArray and not plug.isElement:

        # Check value type
        #
        if not isinstance(value, (list, tuple)):

            raise TypeError('Array plugs expect a sequence of values!')

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
            setValue(element, item)

        # Remove any excess elements
        #
        if numElements > numItems:

            plugutils.removeMultiInstances(plug, list(range(numItems, numElements)))

    elif plug.isCompound:

        setCompound(plug, value)

    else:

        attributeType = plugutils.getApiType(plug)
        __set_value__[attributeType](plug, value, force=force)


def resetValue(plug):
    """
    Resets the value for the supplied plug back to its default value.

    :type plug: om.MPlug
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

            resetValue(plug.elementByPhysicalIndex(i))

    elif plug.isCompound:

        # Iterate through children
        #
        numChildren = plug.numChildren()

        for i in range(numChildren):

            resetValue(plug.child(i))

    else:

        # Get default value
        #
        attribute = plug.attribute()
        defaultValue = om.MObject.kNullObj

        if attribute.hasFn(om.MFn.kNumericAttribute):

            defaultValue = om.MFnNumericAttribute(attribute).default

        elif attribute.hasFn(om.MFn.kUnitAttribute):

            defaultValue = om.MFnUnitAttribute(attribute).default

        else:

            pass

        # Reset plug
        #
        setValue(plug, defaultValue)


def setAliases(plug, aliases):
    """
    Updates the values for the supplied plug while assigning aliases.
    The physical index will be used for each dictionary item.

    :type plug: om.MPlug
    :type aliases: dict[str: object]
    :rtype: None
    """

    # Check if this is an array plug
    #
    if not plug.isArray or plug.isElement:

        raise TypeError('setAliases() expects an array plug!')

    # Initialize function set
    #
    fnDependNode = om.MFnDependencyNode(plug.node())

    # Check if space should be reallocated
    #
    numElements = plug.numElements()
    numItems = len(aliases)

    if numItems > numElements:

        plug.setNumElements(numItems)

    elif numItems < numElements:

        plugutils.removeMultiInstances(plug, list(range(numItems, numElements)))

    else:

        pass

    # Iterate through elements
    #
    for (physicalIndex, (alias, value)) in enumerate(aliases.items()):

        # Update element value
        #
        element = plug.elementByLogicalIndex(physicalIndex)
        setValue(element, value)

        # Check if plug already has alias
        #
        plugAlias = fnDependNode.plugsAlias(element)
        hasAlias = len(plugAlias)

        if hasAlias and plugAlias != alias:

            fnDependNode.setAlias(plugAlias, element.partialName(), element, add=False)

        # Add new plug alias
        #
        fnDependNode.setAlias(alias, element.partialName(), element, add=True)
# endregion
