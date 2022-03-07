import json

from maya.api import OpenMaya as om
from six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AttributeEncoder(json.JSONEncoder):
    """
    Overload of JSONEncoder used to serialize custom Maya attributes.
    """

    __slots__ = ()

    def default(self, obj):
        """
        Returns a serializable object for the supplied value.

        :type obj: Any
        :rtype: Any
        """

        return super(AttributeEncoder, self).default(obj)


class AttributeDecoder(json.JSONDecoder):
    """
    Overload of JSONDecoder used to deserialize custom Maya attributes.
    """

    __slots__ = ('_nodeHandle', '_nodeClass')

    __numerictypes__ = {
        'bool': om.MFnNumericData.kBoolean,
        'long': om.MFnNumericData.kLong,
        'short': om.MFnNumericData.kShort,
        'int': om.MFnNumericData.kInt,
        'byte': om.MFnNumericData.kByte,
        'char': om.MFnNumericData.kChar,
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
        'doubleArray': om.MFnNumericData.kDoubleArray,
        'floatArray': om.MFnNumericData.kFloatArray,
        'vectorArray': om.MFnNumericData.kVectorArray,
        'pointArray': om.MFnNumericData.kPointArray,
        'matrixArray': om.MFnNumericData.kMatrixArray
    }

    __unittypes__ = {
        'angle': om.MFnUnitAttribute.kAngle,
        'doubleAngle': om.MFnUnitAttribute.kAngle,
        'distance': om.MFnUnitAttribute.kDistance,
        'doubleLinear': om.MFnUnitAttribute.kDistance,
        'time': om.MFnUnitAttribute.kTime
    }

    __datatypes__ = {
        'string': om.MFnData.kString,
        'str': om.MFnData.kString,
        'unicode': om.MFnData.kString,
        'stringArray': om.MFnData.kStringArray,
        'nurbsCurve': om.MFnNumericData.kNurbsCurve,
        'nurbsSurface': om.MFnNumericData.kNurbsSurface,
        'mesh': om.MFnNumericData.kMesh,
        'lattice': om.MFnNumericData.kLattice
    }

    __matrixtypes__ = {
        'matrix': om.MFnMatrixAttribute.kDouble,
        'doubleMatrix': om.MFnMatrixAttribute.kDouble,
        'fltMatrix': om.MFnMatrixAttribute.kFloat,
        'floatMatrix': om.MFnMatrixAttribute.kFloat
    }

    __types__ = {
        'enum': 'deserializeEnumAttribute',
        'message': 'deserializeMessageAttribute',
        'compound': 'deserializeCompoundAttribute'
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

        # Call parent method
        #
        super(AttributeDecoder, self).__init__(*args, **kwargs)

    def attribute(self, name):
        """
        Returns the attribute associated with the given name.
        If no attribute is found then a null object is returned!

        :type name: str
        :rtype: om.MObject
        """

        if self._nodeHandle.isAlive():

            dependNode = self._nodeHandle.object()
            fnDependNode = om.MFnDependencyNode(dependNode)

            return fnDependNode.attribute(name)

        elif self._nodeClass is not None:

            return self._nodeClass.attribute(name)

        else:

            return om.MObject.kNullObj

    def default(self, obj):
        """
        Returns a deserialized object from the supplied dictionary.

        :type obj: dict
        :rtype: Any
        """

        # Inspect attribute type
        #
        attribute = self.attribute(obj['longName'])
        attributeType = obj['attributeType']

        if attributeType in self.__numerictypes__:

            return self.deserializeNumericAttribute(obj, attribute=attribute)

        elif attributeType in self.__unittypes__:

            return self.deserializeUnitAttribute(obj, attribute=attribute)

        elif attributeType in self.__datatypes__:

            return self.deserializeTypedAttribute(obj, attribute=attribute)

        elif attributeType in self.__matrixtypes__:

            return self.deserializeMatrixAttribute(obj, attribute=attribute)

        else:

            name = self.__types__.get(attributeType, '')
            func = getattr(self, name, None)

            if callable(func):

                return func(obj, attribute=attribute)

            else:

                raise TypeError('default() unable to deserialize %s attribute type!' % attributeType)

    def deserializeAttribute(self, obj, attribute=om.MObject.kNullObj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Edit properties
        #
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

        # Check if array was enabled
        # If array is not enabled when setting indexMatters a runtime error will be raised!
        #
        if fnAttribute.array:

            fnAttribute.indexMatters = obj.get('indexMatters', True)

        # Check if attribute has a category
        #
        category = obj.get('category', '')

        if len(category) > 0 and not fnAttribute.hasCategory(category):

            fnAttribute.addToCategory(category)

        return attribute

    def deserializeNumericAttribute(self, obj, attribute=om.MObject.kNullObj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Initialize function set
        #
        fnAttribute = om.MFnNumericAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)
            attributeType = obj['attributeType']

            attribute = fnAttribute.create(longName, shortName, self.__numerictypes__[attributeType])

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        self.deserializeAttribute(obj, attribute=attribute)

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

    def deserializeUnitAttribute(self, obj, attribute=om.MObject.kNullObj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Initialize function set
        #
        fnAttribute = om.MFnUnitAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)
            attributeType = obj['attributeType']

            attribute = fnAttribute.create(longName, shortName, self.__unittypes__[attributeType])

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        self.deserializeAttribute(obj, attribute=attribute)

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

    def deserializeTypedAttribute(self, obj, attribute=om.MObject.kNullObj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Initialize function set
        #
        fnAttribute = om.MFnTypedAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)
            attributeType = obj['attributeType']

            attribute = fnAttribute.create(longName, shortName, self.__datatypes__[attributeType])

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        return self.deserializeAttribute(obj, attribute=attribute)

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

    def deserializeEnumAttribute(self, obj, attribute=om.MObject.kNullObj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Initialize function set
        #
        fnAttribute = om.MFnEnumAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)

            attribute = fnAttribute.create(longName, shortName)

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        self.deserializeAttribute(obj, attribute=attribute)

        # Get enum fields
        #
        fields = obj.get('fields', {})

        if isinstance(fields, string_types):

            fields = self.deserializeEnumFields(fields)

        elif isinstance(fields, (list, tuple)):

            fields = dict(enumerate(fields))

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

    def deserializeMatrixAttribute(self, obj, attribute=om.MObject.kNullObj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Initialize function set
        #
        fnAttribute = om.MFnMatrixAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)
            attributeType = obj['attributeType']

            attribute = fnAttribute.create(longName, shortName, self.__matrixtypes__[attributeType])

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        return self.deserializeAttribute(obj, attribute=attribute)

    def deserializeMessageAttribute(self, obj, attribute=om.MObject.kNullObj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Initialize function set
        #
        fnAttribute = om.MFnMessageAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)

            attribute = fnAttribute.create(longName, shortName)

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        return self.deserializeAttribute(obj, attribute=attribute)

    def deserializeCompoundAttribute(self, obj, attribute=om.MObject.kNullObj):
        """
        Returns a deserialized attribute from the supplied object.

        :type obj: dict
        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Initialize function set
        #
        fnAttribute = om.MFnCompoundAttribute()

        if attribute.isNull():

            longName = obj['longName']
            shortName = obj.get('shortName', longName)

            attribute = fnAttribute.create(longName, shortName)

        else:

            fnAttribute.setObject(attribute)

        # Deserialize base attribute
        #
        self.deserializeAttribute(obj, attribute=attribute)

        # Iterate through children
        #
        for child in obj['children']:

            fnAttribute.addChild(child)

        return attribute
