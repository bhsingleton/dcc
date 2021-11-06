"""
This modules provides developers with a json approach to attribute templating.

Hard lessons learnt:
[CRASH] Attempting to add a compound attribute with no children will crash Maya.
[CRASH] Adding nested attributes to a pre-existing compound attribute can crash Maya when serializing files on save.
[LIMITATION] Compound attributes declared via the mel command "addAttr" have a fixed child size and cannot be changed.

All in all, be careful when updating this code.
A lot of the decisions made were to prevent fatal crashes.
"""
import re

from maya.api import OpenMaya as om
from abc import ABCMeta, abstractmethod
from six import with_metaclass, string_types
from collections import OrderedDict
from copy import deepcopy

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AttributeParser(with_metaclass(ABCMeta, object)):
    """
    Abstract base class used to interface with a json object.
    This class is responsible for extrapolating data used to construct attributes.
    It is important to note that the dataType keyword is not required.
    """

    __slots__ = (
        '_nodeHandle',
        '_nodeClass',
        '_longName',
        '_shortName',
        '_attributeType',
        '_flags',
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :keyword longName: str
        :keyword shortName: str
        :keyword attributeType: str
        :rtype: None
        """

        # Call parent method
        #
        super(AttributeParser, self).__init__()

        # Check if any arguments were supplied
        #
        numArgs = len(args)

        if numArgs != 1:

            raise TypeError('AttributeParser() expects 1 argument (%s given)!' % numArgs)

        # Declare class variables
        #
        self._nodeHandle = om.MObjectHandle()
        self._nodeClass = None
        self._flags = deepcopy(kwargs)

        # Store argument
        #
        arg = args[0]

        if isinstance(arg, (om.MObject, om.MObjectHandle)):

            self.nodeHandle = arg

        elif isinstance(arg, (string_types, om.MTypeId)):

            self.nodeClass = arg

        else:

            raise TypeError('AttributeParser() expects an MObject or MTypeId (%s given)!' % type(arg).__name__)

        # Store constructors
        #
        self._longName = kwargs['longName']
        self._shortName = kwargs.get('shortName', self._longName)

        if len(self._longName) == 0:

            raise TypeError('AttributeParser() expects a valid long name!')

        # Store short name
        #
        self._attributeType = kwargs['attributeType']

        if len(self._attributeType) == 0:

            raise TypeError('AttributeParser() expects a valid attribute type!')

    def __getitem__(self, item):
        """
        Overloaded method used to retrieve a keyword from the user arguments.

        :type item: str
        :rtype: object
        """

        return self._flags.get(item, None)

    @property
    def nodeHandle(self):
        """
        Getter method that returns the node handle for this instance.

        :rtype: om.MObjectHandle
        """

        return self._nodeHandle

    @nodeHandle.setter
    def nodeHandle(self, dependNode):
        """
        Setter method that updates the node handle for this instance.
        This allows for the creation of user defined attributes.

        :type dependNode: om.MObject
        :rtype: None
        """

        # Check if dependency node is valid
        #
        if dependNode.isNull():

            raise TypeError('nodeHandle.setter() expects a valid MObject!')

        self._nodeHandle = om.MObjectHandle(dependNode)

        # Update node class
        #
        self.nodeClass = om.MFnDependencyNode(dependNode).typeName

    @property
    def nodeClass(self):
        """
        Getter method that returns the node class for this instance.

        :rtype: om.MNodeClass
        """

        return self._nodeClass

    @nodeClass.setter
    def nodeClass(self, typeName):
        """
        Setter method that updates the node class for this instance.
        This allows for the creation of extension attributes.

        :type typeName: Union[str, om.MTypeId]
        :rtype: None
        """

        self._nodeClass = om.MNodeClass(typeName)

    @property
    def longName(self):
        """
        Getter method that returns the long name of this attribute.

        :rtype: str
        """

        return self._longName

    @property
    def shortName(self):
        """
        Getter method that returns the short name of this attribute.

        :rtype: str
        """

        return self._shortName

    @property
    def attributeType(self):
        """
        Getter method that returns the type name for this attribute.

        :rtype: str
        """

        return self._attributeType

    @property
    def args(self):
        """
        Getter method that returns the constructor for this parser.

        :rtype: tuple
        """

        if self._nodeHandle.isAlive():

            return (self._nodeHandle.object(),)

        elif self._nodeClass is not None:

            return (self._nodeClass,)

        else:

            return tuple()

    @property
    def flags(self):
        """
        Getter method used to retrieve the keyword arguments for this attribute.

        :rtype: dict
        """

        return self._flags

    @classmethod
    @abstractmethod
    def acceptsAttributeType(cls, typeName):
        """
        Abstract method used to determine if this parser accepts the given type name.

        :type typeName: str
        :rtype: bool
        """

        pass

    @classmethod
    @abstractmethod
    def functionSet(cls, *args):
        """
        Class method used to retrieve a function set for this parser.

        :rtype: Union[om.MFnNumericAttribute, om.MFnTypedAttribute, om.MFnCompoundAttribute, om.MFnUnitAttribute]
        """

        pass

    def constructors(self):
        """
        Returns the constructors for this attribute.
        The default constructors consist of a long and short name.

        :rtype: tuple[str, str]
        """

        return self.longName, self.shortName

    def createAttribute(self):
        """
        Method used to create an attribute of this type.
        There should be no need to overload this method.
        So long as you overload "functionSet" and "constructors" you're good to go~

        :rtype: om.MObject
        """

        # Check for redundancy
        #
        if self.hasAttribute():

            return self.attribute()

        # Create attribute
        #
        functionSet = self.functionSet()
        constructors = self.constructors()

        attribute = functionSet.create(*constructors)

        # Edit attribute properties
        #
        return self.editAttribute(attribute)

    def editAttribute(self, attribute):
        """
        Edits the supplied attribute based on the internal kwargs.

        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Initialize function set
        #
        fnAttribute = om.MFnAttribute(attribute)

        # Edit properties
        #
        fnAttribute.readable = self.flags.get('readable', True)
        fnAttribute.writable = self.flags.get('writable', True)
        fnAttribute.connectable = self.flags.get('connectable', True)
        fnAttribute.storable = self.flags.get('storable', True)
        fnAttribute.cached = self.flags.get('cached', True)
        fnAttribute.array = self.flags.get('array', False)
        fnAttribute.keyable = self.flags.get('keyable', False)
        fnAttribute.channelBox = self.flags.get('channelBox', False)
        fnAttribute.hidden = self.flags.get('hidden', False)
        fnAttribute.usedAsColor = self.flags.get('usedAsColor', False)
        fnAttribute.usedAsFilename = self.flags.get('usedAsFilename', False)
        fnAttribute.disconnectBehavior = self.flags.get('disconnectBehavior', 2)

        # Check if array was enabled
        # If array is not enabled when setting indexMatters a runtime error will be raised!
        #
        if fnAttribute.array:

            fnAttribute.indexMatters = self.flags.get('indexMatters', True)

        # Check if attribute has a category
        #
        category = self.flags.get('category', '')

        if len(category) > 0 and not fnAttribute.hasCategory(category):

            fnAttribute.addToCategory(category)

        return attribute

    def addAttribute(self):
        """
        Adds an attribute to either a dependency node or node class.
        If the attribute has a parent then it will be appended to the compound attribute.
        I've noticed that the maya crashes stabilize if you add the attribute before setting its parent?

        :rtype: om.MObject
        """

        # Check if attribute already exists
        #
        if self.hasAttribute():

            return self.attribute()

        # Create new attribute
        #
        log.info('Creating %s attribute...' % self.longName)
        attribute = self.createAttribute()

        # Determine operation
        #
        if self.nodeHandle.isAlive():

            # Add user attribute to node
            #
            fnDependNode = om.MFnDependencyNode(self.nodeHandle.object())
            fnDependNode.addAttribute(attribute)

            # Check if a parent was supplied
            #
            parent = self.flags.get('parent', None)

            if parent is not None:

                # Reclaim attribute in case pointer is no longer valid
                #
                parentAttribute = fnDependNode.attribute(parent)
                childAttribute = fnDependNode.attribute(self.longName)

                # Add child to compound attribute
                #
                om.MFnCompoundAttribute(parentAttribute).addChild(childAttribute)

        elif self.nodeClass is not None:

            # Add extension attribute to node class
            #
            self.nodeClass.addExtensionAttribute(attribute)

            # Check if a parent was supplied
            #
            parent = self.flags.get('parent', None)

            if parent is not None:

                # Reclaim attribute in case pointer is no longer valid
                #
                parentAttribute = self.nodeClass.attribute(parent)
                childAttribute = self.nodeClass.attribute(self.longName)

                # Add child to compound attribute
                #
                om.MFnCompoundAttribute(parentAttribute).addChild(childAttribute)

        else:

            raise TypeError('addAttribute() expects a valid dependency node!')

        return attribute

    def hasAttribute(self):
        """
        Checks if this attribute already exists.
        This operation first evaluates the object handle before inspecting the node class.

        :rtype: bool
        """

        # Check if object handle is alive
        #
        if self.nodeHandle.isAlive():

            return om.MFnDependencyNode(self.nodeHandle.object()).hasAttribute(self.longName)

        elif self.nodeClass is not None:

            return self.nodeClass.hasAttribute(self.longName)

        else:

            return False

    def attribute(self):
        """
        Returns the attribute associated with this parser.
        If the attribute does not exist then a null object is returned instead!

        :rtype: om.MObject
        """

        # Check if object handle is alive
        #
        if self.nodeHandle.isAlive():

            return om.MFnDependencyNode(self.nodeHandle.object()).attribute(self.longName)

        elif self.nodeClass is not None:

            return self.nodeClass.attribute(self.longName)

        else:

            return om.MObject.kNullObj


class NumericAttributeParser(AttributeParser):
    """
    Overload of AttributeParser used to evaluate numeric attributes.
    """

    __slots__ = ()
    __deserialize__ = re.compile(r'([\w]+[0-9]*\.?[0-9]*)')

    __datatypes__ = {
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

    def __init__(self, *args, **kwargs):
        """
        Overloaded method called after a new instance has been created.
        """

        # Call parent method
        #
        super(NumericAttributeParser, self).__init__(*args, **kwargs)

    @classmethod
    def acceptsAttributeType(cls, typeName):
        """
        Method used to determine if this parser accepts the given type name.

        :type typeName: str
        :rtype: bool
        """

        return cls.numericType(typeName) is not None

    @classmethod
    def functionSet(cls, *args):
        """
        Returns a function set that can interact with this attribute type.

        :rtype: om.MFnNumericAttribute
        """

        return om.MFnNumericAttribute(*args)

    @classmethod
    def numericType(cls, typeName):
        """
        Returns the numeric type for the given name.

        :rtype: int
        """

        return cls.__datatypes__.get(typeName, None)

    def constructors(self):
        """
        Returns the constructors for this attribute.

        :rtype: tuple[str, str, int]
        """

        return self.longName, self.shortName, self.numericType(self.attributeType)

    def createAttribute(self):
        """
        Method used to create an attribute of this type.
        There should be no need to overload this method.
        So long as you overload "functionSet" and "constructors" you're good to go~

        :rtype: om.MObject
        """

        # Check for redundancy
        #
        if self.hasAttribute():

            return self.attribute()

        # Check if this is a compound numeric attribute
        #
        children = self.flags.get('children', [])
        numChildren = len(children)

        if numChildren > 0:

            # Create child attributes
            #
            functionSet = self.functionSet()
            childAttributes = [None] * numChildren

            for (index, child) in enumerate(children):

                Parser = findCompatibleParser(child)
                childAttributes[index] = Parser(*self.args, **child).createAttribute()

            # Create and edit compound attribute
            #
            attribute = functionSet.create(self.longName, self.shortName, *childAttributes)
            return self.editAttribute(attribute)

        else:

            # Return parent method
            #
            return super(NumericAttributeParser, self).createAttribute()

    def editAttribute(self, attribute):
        """
        Method used to edit the supplied attribute to match the parsed arguments.

        :type attribute: om.MObject
        :rtype: None
        """

        # Call parent method
        #
        super(NumericAttributeParser, self).editAttribute(attribute)

        # Set default value
        #
        functionSet = self.functionSet(attribute)
        default = self.flags.get('default', None)

        if isinstance(default, (int, float)):

            functionSet.default = default

        # Set min value
        #
        minValue = self.flags.get('min', None)

        if isinstance(minValue, (int, float)):

            functionSet.setMin(minValue)

        # Set max value
        #
        maxValue = self.flags.get('max', None)

        if isinstance(maxValue, (int, float)):

            functionSet.setMax(maxValue)

        # Set soft min value
        #
        softMinValue = self.flags.get('softMin', None)

        if isinstance(softMinValue, (int, float)):

            functionSet.setSoftMin(softMinValue)

        # Set soft max value
        #
        softMaxValue = self.flags.get('softMax', None)

        if isinstance(softMaxValue, (int, float)):

            functionSet.setSoftMax(softMaxValue)

        return attribute


class UnitAttributeParser(AttributeParser):
    """
    Overload of AttributeParser used to evaluate unit attributes.
    """

    __slots__ = ()

    __unittypes__ = {
        'angle': om.MFnUnitAttribute.kAngle,
        'doubleAngle': om.MFnUnitAttribute.kAngle,
        'distance': om.MFnUnitAttribute.kDistance,
        'doubleLinear': om.MFnUnitAttribute.kDistance,
        'time': om.MFnUnitAttribute.kTime
    }

    def __init__(self, *args, **kwargs):
        """
        Overloaded method called after a new instance has been created.
        """

        # Call parent method
        #
        super(UnitAttributeParser, self).__init__(*args, **kwargs)

    @classmethod
    def acceptsAttributeType(cls, typeName):
        """
        Method used to determine if this parser accepts the given type name.

        :type typeName: str
        :rtype: bool
        """

        return cls.unitType(typeName) is not None

    @classmethod
    def functionSet(cls, *args):
        """
        Returns a function set that can interact with this attribute type.

        :rtype: om.MFnUnitAttribute
        """

        return om.MFnUnitAttribute(*args)

    @classmethod
    def unitType(cls, typeName):
        """
        Returns the unit type for the given name.

        :rtype: int
        """

        return cls.__unittypes__.get(typeName, None)

    def constructors(self):
        """
        Returns the constructors for this attribute.

        :rtype: tuple[str, str, int]
        """

        return self.longName, self.shortName, self.unitType(self.attributeType)

    def editAttribute(self, attribute):
        """
        Method used to edit the supplied attribute to match the parsed arguments.

        :type attribute: om.MObject
        :rtype: None
        """

        # Call parent method
        #
        super(UnitAttributeParser, self).editAttribute(attribute)

        # Set default value
        #
        functionSet = self.functionSet(attribute)
        default = self.flags.get('default', None)

        if isinstance(default, (int, float)):

            functionSet.default = default

        # Set min value
        #
        minValue = self.flags.get('min', None)

        if isinstance(minValue, (int, float)):

            functionSet.setMin(minValue)

        # Set max value
        #
        maxValue = self.flags.get('max', None)

        if isinstance(maxValue, (int, float)):

            functionSet.setMax(maxValue)

        # Set soft min value
        #
        softMinValue = self.flags.get('softMin', None)

        if isinstance(softMinValue, (int, float)):

            functionSet.setSoftMin(softMinValue)

        # Set soft max value
        #
        softMaxValue = self.flags.get('softMax', None)

        if isinstance(softMaxValue, (int, float)):

            functionSet.setSoftMax(softMaxValue)

        return attribute


class TypedAttributeParser(AttributeParser):
    """
    Overload of AttributeParser used to evaluate typed attributes.
    """

    __slots__ = ()

    __datatypes = {
        'string': om.MFnData.kString,
        'str': om.MFnData.kString,
        'unicode': om.MFnData.kString,
        'stringArray': om.MFnData.kStringArray,
        'nurbsCurve': om.MFnNumericData.kNurbsCurve,
        'nurbsSurface': om.MFnNumericData.kNurbsSurface,
        'mesh': om.MFnNumericData.kMesh,
        'lattice': om.MFnNumericData.kLattice
    }

    def __init__(self, *args, **kwargs):
        """
        Overloaded method called after a new instance has been created.
        """

        # Call parent method
        #
        super(TypedAttributeParser, self).__init__(*args, **kwargs)

    @classmethod
    def acceptsAttributeType(cls, typeName):
        """
        Method used to determine if this parser accepts the given type name.

        :type typeName: str
        :rtype: bool
        """

        return cls.dataType(typeName) is not None

    @classmethod
    def functionSet(cls, *args):
        """
        Returns a function set that can interact with this attribute type.

        :rtype: om.MFnTypedAttribute
        """

        return om.MFnTypedAttribute(*args)

    @classmethod
    def dataType(cls, typeName):
        """
        Returns the unit type for the given name.

        :rtype: int
        """

        return cls.__datatypes.get(typeName, None)

    def constructors(self):
        """
        Returns the constructors for this attribute.

        :rtype: tuple[str, str, int]
        """

        return self.longName, self.shortName, self.dataType(self.attributeType)


class EnumAttributeParser(AttributeParser):
    """
    Overload of AttributeParser used to evaluate enum attributes.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Overloaded method called after a new instance has been created.
        """

        # Call parent method
        #
        super(EnumAttributeParser, self).__init__(*args, **kwargs)

    @classmethod
    def acceptsAttributeType(cls, typeName):
        """
        Method used to determine if this parser accepts the given type name.

        :type typeName: str
        :rtype: bool
        """

        return typeName == 'enum'

    @classmethod
    def functionSet(cls, *args):
        """
        Returns a function set that can interact with this attribute type.

        :rtype: om.MFnEnumAttribute
        """

        return om.MFnEnumAttribute(*args)

    def editAttribute(self, attribute):
        """
        Method used to edit the supplied attribute to match this xml element.

        :type attribute: om.MObject
        :rtype: om.MObject
        """

        # Call parent method
        #
        super(EnumAttributeParser, self).editAttribute(attribute)

        # Get enum fields
        #
        functionSet = self.functionSet(attribute)
        fields = self.flags.get('fields', {})

        if isinstance(fields, string_types):

            fields = self.evaluateFields(fields)

        elif isinstance(fields, (list, tuple)):

            fields = self.enumerateFields(fields)

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
            if not self.hasFieldName(attribute, fieldName):

                functionSet.addField(fieldName, fieldValue)

            else:

                continue

        # Set default value
        #
        default = self.flags.get('default', None)

        if default is not None:

            functionSet.default = int(default)

        return attribute

    def getFieldValue(self, attribute, field):
        """
        Method used to retrieve the index for the given field name.
        Sadly there is no safe way to get a field value so we gotta use a try/catch...

        :type attribute: om.MObject
        :type field: str
        :rtype: int
        """

        try:

            return self.functionSet(attribute).fieldValue(field)

        except RuntimeError as exception:

            log.debug(exception)
            return None

    def hasFieldName(self, attribute, field):
        """
        Method used to evaluate if the given field name exists.

        :type attribute: om.MObject
        :type field: str
        :rtype: int
        """

        return self.getFieldValue(attribute, field) is not None

    @staticmethod
    def evaluateFields(string):
        """
        Returns a dictionary field name-values from the supplied string.
        This string must use the following format: "{fieldName}={fieldValue}:{fieldName}={fieldValue}"

        :type string: str
        :rtype: dict
        """

        # Split fields using delimiter
        #
        strings = string.split(':')
        fields = OrderedDict()

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

    @staticmethod
    def enumerateFields(items):
        """
        Returns a dictionary of field name-value pairs from the supplied string list.

        :type items: list[str]
        :rtype: dict
        """

        return OrderedDict([(index, item) for (index, item) in enumerate(items)])


class MatrixAttributeParser(AttributeParser):
    """
    Overload of AttributeParser used to evaluate matrix attributes.
    """

    __slots__ = ()

    __matrixtypes__ = {
        'matrix': om.MFnMatrixAttribute.kDouble,
        'doubleMatrix': om.MFnMatrixAttribute.kDouble,
        'fltMatrix': om.MFnMatrixAttribute.kFloat,
        'floatMatrix': om.MFnMatrixAttribute.kFloat
    }

    def __init__(self, *args, **kwargs):
        """
        Overloaded method called after a new instance has been created.
        """

        # Call parent method
        #
        super(MatrixAttributeParser, self).__init__(*args, **kwargs)

    @classmethod
    def acceptsAttributeType(cls, typeName):
        """
        Method used to determine if this parser accepts the given type name.

        :type typeName: str
        :rtype: bool
        """

        return cls.matrixType(typeName) is not None

    @classmethod
    def functionSet(cls, *args):
        """
        Returns a function set that can interact with this attribute type.

        :rtype: om.MFnMatrixAttribute
        """

        return om.MFnMatrixAttribute(*args)

    @classmethod
    def matrixType(cls, typeName):
        """
        Returns the matrix type for the given name.

        :rtype: int
        """

        return cls.__matrixtypes__.get(typeName, None)

    def constructors(self):
        """
        Returns the constructors for this attribute.

        :rtype: tuple[str, str, int]
        """

        return self.longName, self.shortName, self.matrixType(self.attributeType)


class MessageAttributeParser(AttributeParser):
    """
    Overload of AttributeParser used to evaluate message attributes.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Overloaded method called after a new instance has been created.
        """

        # Call parent method
        #
        super(MessageAttributeParser, self).__init__(*args, **kwargs)

    @classmethod
    def acceptsAttributeType(cls, typeName):
        """
        Method used to determine if this parser accepts the given type name.

        :type typeName: str
        :rtype: bool
        """

        return typeName == 'message'

    def functionSet(self, *args):
        """
        Class method used to retrieve a function set for this parser.

        :rtype: om.MFnMessageAttribute
        """

        return om.MFnMessageAttribute(*args)


class CompoundAttributeParser(AttributeParser):
    """
    Overload of AttributeParser used to evaluate compound attributes.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Overloaded method called after a new instance has been created.
        """

        # Call parent method
        #
        super(CompoundAttributeParser, self).__init__(*args, **kwargs)

    @classmethod
    def acceptsAttributeType(cls, typeName):
        """
        Method used to determine if this parser accepts the given type name.

        :type typeName: str
        :rtype: bool
        """

        return typeName == 'compound'

    @classmethod
    def functionSet(cls, *args):
        """
        Returns a function set that can interact with this attribute type.

        :rtype: om.MFnCompoundAttribute
        """

        return om.MFnCompoundAttribute(*args)

    def createAttribute(self, *args, **kwargs):
        """
        Method used to create an attribute based off this xml element.
        The child attributes created do not need to be put through the exploit mentioned in the docstring.

        :rtype: om.MObject
        """

        # Create attribute
        #
        attribute = super(CompoundAttributeParser, self).createAttribute()

        # Attach attribute to function set
        #
        functionSet = self.functionSet()
        functionSet.setObject(attribute)

        # Add child attributes if any
        #
        children = self.flags.get('children', [])

        for child in children:

            # Create child parser
            #
            Parser = findCompatibleParser(child)

            if Parser is None:

                continue

            # Initialize parser from arguments
            #
            parser = Parser(*self.args, **child)
            childAttribute = parser.createAttribute()

            # Add child attribute
            #
            functionSet.addChild(childAttribute)

        return attribute


def findCompatibleParser(attributeType):
    """
    Returns an attribute parser compatible with the given attribute type.

    :type attributeType: Union[str, dict]
    :rtype: type
    """

    # Check value type
    #
    if isinstance(attributeType, dict):

        attributeType = attributeType.get('attributeType', '')

    # Collect parsers
    #
    parsers = [x for x in AttributeParser.__subclasses__() if x.acceptsAttributeType(attributeType)]
    numParsers = len(parsers)

    if numParsers == 1:

        return parsers[0]

    else:

        log.error('findCompatibleParser() expects a valid attribute type (%s given)!' % attributeType)
        return None