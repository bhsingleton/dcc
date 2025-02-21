import json

from maya.api import OpenMaya as om
from ...python import stringutils
from ...vendor.six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MAttributeDecoder(json.JSONDecoder):
    """
    Overload of `JSONDecoder` used to deserialize custom Maya attributes.
    """

    # region Dunderscores
    __slots__ = (
        '_nodeHandle',
        '_nodeClass',
        '_attributes'
    )

    __numeric_types__ = {
        'bool': om.MFnNumericData.kBoolean,
        'boolean': om.MFnNumericData.kBoolean,
        'addr': om.MFnNumericData.kAddr,
        'address': om.MFnNumericData.kAddr,
        'long': om.MFnNumericData.kLong,
        'short': om.MFnNumericData.kShort,
        'int': om.MFnNumericData.kInt,
        'integer': om.MFnNumericData.kInt,
        'byte': om.MFnNumericData.kByte,
        'char': om.MFnNumericData.kChar,
        'character': om.MFnNumericData.kChar,
        'float': om.MFnNumericData.kFloat,
        'double': om.MFnNumericData.kFloat,
        'int2': om.MFnNumericData.k2Int,
        'int3': om.MFnNumericData.k3Int,
        'short2': om.MFnNumericData.k2Short,
        'short3': om.MFnNumericData.k3Short,
        'long2': om.MFnNumericData.k2Long,
        'long3': om.MFnNumericData.k3Long,
        'float2': om.MFnNumericData.k2Float,
        'float3': om.MFnNumericData.k3Float,
        'double2': om.MFnNumericData.k2Double,
        'double3': om.MFnNumericData.k3Double,
        'double4': om.MFnNumericData.k4Double,
        'intArray': om.MFnData.kIntArray,
        'floatArray': om.MFnNumericData.kFloatArray,
        'doubleArray': om.MFnNumericData.kDoubleArray,
        'vectorArray': om.MFnNumericData.kVectorArray,
        'pointArray': om.MFnNumericData.kPointArray,
        'matrixArray': om.MFnNumericData.kMatrixArray
    }

    __unit_types__ = {
        'angle': om.MFnUnitAttribute.kAngle,
        'doubleAngle': om.MFnUnitAttribute.kAngle,
        'distance': om.MFnUnitAttribute.kDistance,
        'doubleLinear': om.MFnUnitAttribute.kDistance,
        'time': om.MFnUnitAttribute.kTime
    }

    __data_types__ = {
        'string': om.MFnData.kString,
        'str': om.MFnData.kString,
        'unicode': om.MFnData.kString,
        'stringArray': om.MFnData.kStringArray,
        'nurbsCurve': om.MFnNumericData.kNurbsCurve,
        'nurbsSurface': om.MFnNumericData.kNurbsSurface,
        'mesh': om.MFnNumericData.kMesh,
        'lattice': om.MFnNumericData.kLattice
    }

    __matrix_types__ = {
        'matrix': om.MFnMatrixAttribute.kDouble,
        'doubleMatrix': om.MFnMatrixAttribute.kDouble,
        'fltMatrix': om.MFnMatrixAttribute.kFloat,
        'floatMatrix': om.MFnMatrixAttribute.kFloat
    }

    __other_types__ = {
        'enum': 'deserializeEnumAttribute',
        'message': 'deserializeMessageAttribute',
        'compound': 'deserializeCompoundAttribute'
    }

    __default_numeric_types__ = {
        om.MFnNumericData.kBoolean: bool,
        om.MFnNumericData.kInt: int,
        om.MFnNumericData.kFloat: float
    }

    __default_unit_types__ = {
        om.MFnUnitAttribute.kDistance: om.MDistance,
        om.MFnUnitAttribute.kAngle: om.MAngle,
        om.MFnUnitAttribute.kTime: om.MTime
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key node: om.MObject
        :key nodeClass: om.MNodeClass
        :rtype: None
        """

        # Declare private variables
        #
        self._nodeHandle = om.MObjectHandle(kwargs.pop('node', om.MObject.kNullObj))
        self._nodeClass = kwargs.pop('nodeClass', None)
        self._attributes = {}

        # Call parent method
        #
        kwargs['object_hook'] = self.default
        super(MAttributeDecoder, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def nodeHandle(self):
        """
        Getter method that returns the node handle for this instance.

        :rtype: om.MObjectHandle
        """

        return self._nodeHandle

    @property
    def nodeClass(self):
        """
        Getter method that returns the node class for this instance.

        :rtype: om.MNodeClass
        """

        return self._nodeClass
    # endregion

    # region Methods
    def attribute(self, *args):
        """
        Returns the attribute associated with the given name or JSON object.
        If no attribute is found then a null object is returned!

        :type args: Tuple[Union[str, dict]]
        :rtype: om.MObject
        """

        # Evaluate supplied arguments
        #
        numArgs = len(args)

        if numArgs != 1:

            raise TypeError(f'attribute() expects 1 argument ({numArgs} found)!')

        # Inspect first argument
        #
        arg = args[0]
        name = ''

        if isinstance(arg, dict):

            name = arg.get('shortName', arg.get('longName', ''))

        elif isinstance(arg, str):

            name = arg

        else:

            raise TypeError(f'attribute() expects either a str or dict ({type(arg).__name__} found)!')

        # Evaluate which lookup method
        #
        if self._nodeHandle.isAlive():

            dependNode = self._nodeHandle.object()
            fnDependNode = om.MFnDependencyNode(dependNode)

            return fnDependNode.attribute(name)

        elif self._nodeClass is not None:

            return self._nodeClass.attribute(name)

        else:

            return self._attributes.get(name, om.MObject.kNullObj)

    def default(self, obj):
        """
        Returns a deserialized object from the supplied dictionary.

        :type obj: dict
        :rtype: Any
        """

        # Check if attribute type exists
        #
        attributeType = obj.get('attributeType', '')

        if stringutils.isNullOrEmpty(attributeType):

            raise TypeError(f'default() expects an attribute type!')

        # Evaluate attribute type
        #
        if attributeType in self.__numeric_types__:

            return self.deserializeNumericAttribute(obj)

        elif attributeType in self.__unit_types__:

            return self.deserializeUnitAttribute(obj)

        elif attributeType in self.__data_types__:

            return self.deserializeTypedAttribute(obj)

        elif attributeType in self.__matrix_types__:

            return self.deserializeMatrixAttribute(obj)

        else:

            name = self.__other_types__.get(attributeType, '')
            func = getattr(self, name, None)

            if not callable(func):

                raise TypeError(f'default() expects a valid attribute type ({attributeType} given)!')

            return func(obj)

    def deserializeAttribute(self, obj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Edit properties
        #
        attribute = self.attribute(obj)

        fnAttribute = om.MFnAttribute(attribute)
        fnAttribute.readable = obj.get('readable', True)
        fnAttribute.writable = obj.get('writable', True)
        fnAttribute.connectable = obj.get('connectable', True)
        fnAttribute.storable = obj.get('storable', True)
        fnAttribute.cached = obj.get('cached', True)
        fnAttribute.array = obj.get('array', False)
        fnAttribute.keyable = obj.get('keyable', False)
        fnAttribute.channelBox = obj.get('channelBox', False)
        fnAttribute.hidden = obj.get('hidden', False)
        fnAttribute.usedAsColor = obj.get('usedAsColor', False)
        fnAttribute.usedAsFilename = obj.get('usedAsFilename', False)
        fnAttribute.disconnectBehavior = obj.get('disconnectBehavior', 2)

        # Check if a nice-name override was supplied
        #
        niceName = obj.get('niceName', None)

        if not stringutils.isNullOrEmpty(niceName):

            fnAttribute.setNiceNameOverride(niceName)

        # Check if array was enabled
        # If array is not enabled when setting `indexMatters` a runtime error will be raised!
        #
        if fnAttribute.array and not fnAttribute.readable:

            fnAttribute.indexMatters = obj.get('indexMatters', True)

        # Check if attribute has a category
        #
        category = obj.get('category', '')

        if not stringutils.isNullOrEmpty(category) and not fnAttribute.hasCategory(category):

            fnAttribute.addToCategory(category)

        return attribute

    def deserializeNumericAttribute(self, obj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Initialize function set
        #
        attribute = self.attribute(obj)
        fnAttribute = om.MFnNumericAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)
            attributeType = obj['attributeType']

            attribute = fnAttribute.create(longName, shortName, self.__numeric_types__[attributeType])
            self._attributes[shortName] = attribute

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        self.deserializeAttribute(obj)

        # Set default value
        #
        default = obj.get('default', None)

        if isinstance(default, (int, float)):

            fnAttribute.default = default

        # Set min value
        #
        minValue = obj.get('min', None)

        if isinstance(minValue, (int, float)):

            fnAttribute.setMin(minValue)

        # Set max value
        #
        maxValue = obj.get('max', None)

        if isinstance(maxValue, (int, float)):

            fnAttribute.setMax(maxValue)

        # Set soft min value
        #
        softMinValue = obj.get('softMin', None)

        if isinstance(softMinValue, (int, float)):

            fnAttribute.setSoftMin(softMinValue)

        # Set soft max value
        #
        softMaxValue = obj.get('softMax', None)

        if isinstance(softMaxValue, (int, float)):

            fnAttribute.setSoftMax(softMaxValue)

        return attribute

    def deserializeUnitAttribute(self, obj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Initialize function set
        #
        attribute = self.attribute(obj)
        fnAttribute = om.MFnUnitAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)
            attributeType = obj['attributeType']

            attribute = fnAttribute.create(longName, shortName, self.__unit_types__[attributeType])
            self._attributes[shortName] = attribute

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        self.deserializeAttribute(obj)

        # Set default value
        #
        default = obj.get('default', None)

        if isinstance(default, (int, float)):

            cls = self.__default_unit_types__[fnAttribute.unitType()]
            fnAttribute.default = cls(default, unit=cls.uiUnit())

        elif isinstance(default, (om.MDistance, om.MAngle, om.MTime)):

            fnAttribute.default = default

        else:

            pass

        # Set min value
        #
        minValue = obj.get('min', None)

        if isinstance(minValue, (int, float)):

            fnAttribute.setMin(minValue)

        # Set max value
        #
        maxValue = obj.get('max', None)

        if isinstance(maxValue, (int, float)):

            fnAttribute.setMax(maxValue)

        # Set soft min value
        #
        softMinValue = obj.get('softMin', None)

        if isinstance(softMinValue, (int, float)):

            fnAttribute.setSoftMin(softMinValue)

        # Set soft max value
        #
        softMaxValue = obj.get('softMax', None)

        if isinstance(softMaxValue, (int, float)):

            fnAttribute.setSoftMax(softMaxValue)

        return attribute

    def deserializeTypedAttribute(self, obj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Initialize function set
        #
        attribute = self.attribute(obj)
        fnAttribute = om.MFnTypedAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)
            attributeType = obj['attributeType']

            attribute = fnAttribute.create(longName, shortName, self.__data_types__[attributeType])
            self._attributes[shortName] = attribute

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        return self.deserializeAttribute(obj)

    def deserializeEnumFields(self, string):
        """
        Returns a dictionary field name-values from the supplied string.
        This string must use the following format: "{fieldName}={fieldValue}:{fieldName}={fieldValue}"

        :type string: str
        :rtype: dict
        """

        # Split fields using delimiter
        #
        strings = string.split(':')
        fields = {}

        for index, string in enumerate(strings):

            # Check if field has a value pair
            #
            items = string.split('=')
            numItems = len(items)

            fieldName = items[0]

            if numItems == 2:

                fields[fieldName] = int(items[1])

            else:

                fields[fieldName] = index

        return fields

    def deserializeEnumAttribute(self, obj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Initialize function set
        #
        attribute = self.attribute(obj)
        fnAttribute = om.MFnEnumAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)

            attribute = fnAttribute.create(longName, shortName)
            self._attributes[shortName] = attribute

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        self.deserializeAttribute(obj)

        # Get enum fields
        #
        fields = obj.get('fields', {})

        if isinstance(fields, string_types):

            fields = self.deserializeEnumFields(fields)

        elif isinstance(fields, (list, tuple)):

            fields = {field: i for (i, field) in enumerate(fields)}

        elif hasattr(fields, '__members__'):  # Reserved for enum types

            fields = dict(fields.__members__.items())

        else:

            pass

        # Iterate through fields
        #
        for (fieldName, fieldValue) in fields.items():

            # Check item types
            #
            if not isinstance(fieldName, string_types) or not isinstance(fieldValue, int):

                log.warning('editAttribute() expects a valid field name-value pair!')
                continue

            # Add field value pair to attribute
            #
            try:

                fnAttribute.addField(fieldName, fieldValue)

            except RuntimeError:

                continue

        # Set default value
        #
        default = obj.get('default', None)

        if default is not None:

            fnAttribute.default = int(default)

        return attribute

    def deserializeMatrixAttribute(self, obj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Initialize function set
        #
        attribute = self.attribute(obj)
        fnAttribute = om.MFnMatrixAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)
            attributeType = obj['attributeType']

            attribute = fnAttribute.create(longName, shortName, self.__matrix_types__[attributeType])
            self._attributes[shortName] = attribute

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        return self.deserializeAttribute(obj)

    def deserializeMessageAttribute(self, obj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Initialize function set
        #
        attribute = self.attribute(obj)
        fnAttribute = om.MFnMessageAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)

            attribute = fnAttribute.create(longName, shortName)
            self._attributes[shortName] = attribute

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        return self.deserializeAttribute(obj)

    def deserializeCompoundAttribute(self, obj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Initialize function set
        #
        attribute = self.attribute(obj)
        fnAttribute = om.MFnCompoundAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)

            attribute = fnAttribute.create(longName, shortName)
            self._attributes[shortName] = attribute

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        self.deserializeAttribute(obj)

        # Iterate through children
        #
        for child in obj['children']:

            # Evaluate child type
            #
            if isinstance(child, om.MObject):

                fnAttribute.addChild(child)

            elif isinstance(child, dict):

                child = self.default(child)
                fnAttribute.addChild(child)

            else:

                continue

        return attribute
    # endregion
