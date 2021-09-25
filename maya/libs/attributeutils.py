import os
import json
import jsonschema

from maya.api import OpenMaya as om
from collections import deque
from six import string_types

from . import attributeparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


NUMERIC_TYPES = {value: key for (key, value) in om.MFnNumericData.__dict__.items() if key.startswith('k') and isinstance(value, int)}
ATTR_TYPES = {value: key for (key, value) in om.MFnData.__dict__.items() if key.startswith('k') and isinstance(value, int)}
UNIT_TYPES = {value: key for (key, value) in om.MFnUnitAttribute.__dict__.items() if key.startswith('k') and isinstance(value, int)}


class AttributeTemplate(object):
    """
    Base class used to parse a json-based attribute template.
    """

    __slots__ = ('_filePath', '_attributes')

    def __init__(self, filePath):
        """
        Inherited method called after a new instance has been created.

        :type filePath: str
        :rtype: None
        """

        # Call parent method
        #
        super(AttributeTemplate, self).__init__()

        # Check if file path exists
        #
        if not os.path.isfile(filePath):

            raise TypeError('Unable to locate file template: %s' % filePath)

        # Declare class variables
        #
        self._filePath = filePath
        self._attributes = self.parse(filePath)

    @property
    def filePath(self):
        """
        Getter method that returns the file path for this template.

        :rtype: str
        """

        return self._filePath

    @property
    def attributes(self):
        """
        Getter method that returns the attribute definitions from this template.

        :rtype: list[dict]
        """

        return self._attributes

    @staticmethod
    def schemaPath():
        """
        Returns the attribute schema to validate json files.

        :rtype: str
        """

        return os.path.join(os.path.dirname(__file__), 'attributeschema.json')

    @classmethod
    def schema(cls):
        """
        Returns the schema data for validating json data.

        :rtype: dict
        """

        with open(cls.schemaPath(), 'r') as schemaFile:

            return json.load(schemaFile)

    @classmethod
    def parse(cls, filePath):
        """
        Reads the supplied json file.

        :rtype: list[dict]
        """

        try:

            # Validate json string
            #
            instance = None

            with open(filePath, 'r') as jsonFile:

                instance = json.load(jsonFile)
                jsonschema.validate(instance=instance, schema=cls.schema())

            # Return validated data
            #
            return instance

        except (ValueError, jsonschema.ValidationError) as exception:

            log.error(exception)
            return []

    @staticmethod
    def walk(children):
        """
        Walks through the json tree.
        This method will dynamically add a parent keyword to each item!

        :type children: list[dict]
        :rtype: iter
        """

        # Iterate through queue
        #
        queue = deque(children)

        while len(queue):

            # Pop item from queue
            #
            item = queue.popleft()
            children = item.get('children', [])

            for child in children:

                child['parent'] = item['longName']

            # Yield edited item
            #
            queue.extend(children)
            yield item

    def applyTemplate(self, dependNode):
        """
        Applies this attribute template to the supplied dependency node.

        :type dependNode: Union[str, om.MTypeId, om.MObject]
        :rtype: dict
        """

        # Iterate through attributes
        #
        attributes = {}

        for kwargs in self.walk(self.attributes):

            # Find a compatible parser
            #
            Parser = attributeparser.findCompatibleParser(kwargs)

            if Parser is None:

                continue

            # Initialize parser
            #
            parser = Parser(dependNode, **kwargs)

            if parser.hasAttribute():

                # Skip item and move onto next
                #
                log.info('Skipping %s attribute...' % parser.longName)
                attributes[parser.longName] = om.MObjectHandle(parser.attribute())

            else:

                # Add attribute to dependency node
                #
                attribute = parser.addAttribute()
                attributes[parser.longName] = om.MObjectHandle(attribute)

        return attributes


def addAttribute(dependNode, **kwargs):
    """
    Adds an attribute to the supplied node with the supplied parameters.
    Do not use this method with compound attributes!
    Create the attribute then add the children before committing to the node!

    :type dependNode: om.MObject
    :keyword longName: str
    :keyword shortName: str
    :keyword attributeType: str
    :rtype: om.MObject
    """

    # Find compatible parser
    #
    attributeType = kwargs.get('attributeType', '')
    Parser = attributeparser.findCompatibleParser(attributeType)

    if Parser is not None:

        return Parser(dependNode, **kwargs).addAttribute()

    else:

        raise TypeError('addAttribute() expects a valid attribute type (%s given)!' % attributeType)


def createAttribute(**kwargs):
    """
    Creates an attribute based on the supplied parameters.
    This method does not add an attribute to a node, tt only creates the attribute object!

    :keyword longName: str
    :keyword shortName: str
    :keyword attributeType: str
    :rtype: om.MObject
    """

    # Find compatible parser
    #
    attributeType = kwargs.get('attributeType', '')
    Parser = attributeparser.findCompatibleParser(attributeType)

    if Parser is not None:

        return Parser(**kwargs).createAttribute()

    else:

        raise TypeError('createAttribute() expects a valid attribute type (%s given)!' % attributeType)


def applyAttributeTemplate(dependNode, filePath):
    """
    Method used to apply an attribute template to the supplied node handle.

    :type dependNode: Union[str, om.MTypeId, om.MObject]
    :type filePath: str
    :rtype: dict
    """

    # Check if handle is valid
    #
    if not isinstance(dependNode, (string_types, om.MTypeId, om.MObject)):

        raise TypeError('Unable to apply template to dead node handle!')

    # Check if template file exists
    #
    if not os.path.exists(filePath):

        raise TypeError('Unable to locate template: %s' % filePath)

    # Apply template to node handle
    #
    return AttributeTemplate(filePath).applyTemplate(dependNode)


def getAttributeTypeName(attribute):
    """
    Returns the type name for the supplied attribute.
    This is the string that correlates with setAttr commands.

    :type attribute: om.MObject
    :rtype: str
    """

    # Check attribute type
    #
    if attribute.hasFn(om.MFn.kNumericAttribute):

        fnNumericAttribute = om.MFnNumericAttribute(attribute)
        dataType = NUMERIC_TYPES[fnNumericAttribute.numericType()][1:]  # Strip the 'k' prefix

        if dataType[0].isdigit():

            return '{letter}{name}{digit}'.format(
                letter=dataType[1].lower(),
                name=dataType[2:],
                digit=dataType[0]
            )

        else:

            return '{letter}{name}'.format(
                letter=dataType[0].lower(),
                name=dataType[1:]
            )

    elif attribute.hasFn(om.MFn.kTypedAttribute):

        fnTypedAttribute = om.MFnTypedAttribute(attribute)
        dataType = ATTR_TYPES[fnTypedAttribute.attrType()][1:]  # Strip the 'k' prefix

        return '{letter}{name}'.format(
            letter=dataType[0].lower(),
            name=dataType[1:]
        )

    elif attribute.hasFn(om.MFn.kUnitAttribute):

        fnUnitAttribute = om.MFnUnitAttribute(attribute)
        dataType = UNIT_TYPES[fnUnitAttribute.unitType()][1:]  # Strip the 'k' prefix

        return '{letter}{name}'.format(
            letter=dataType[0].lower(),
            name=dataType[1:]
        )

    else:

        return '{letter}{name}'.format(
            letter=attribute.apiTypeStr[1].lower(),
            name=attribute.apiTypeStr[2:-9]  # Strip the 'Attribute' suffix
        )
