import sys
import os

from six import string_types

from xml.dom import minidom
from xml.etree import ElementTree, cElementTree

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Target(object):
    """
    Base class used for intercepting xml related hooks.
    """

    __slots__ = ('size', 'depth', 'builder')

    def __init__(self, size=0):
        """
        Private method called after a new instance has been created.

        :type size: int
        :rtype: None
        """

        # Call parent method
        #
        super(Target, self).__init__()

        # Define public variables
        #
        self.size = size
        self.depth = 0
        self.builder = ElementTree.TreeBuilder()

    def start(self, tag, attribute):
        """
        Called for each new tag.

        :type tag: str
        :type attribute: dict
        :rtype: None
        """

        # Increment depth
        #
        tagSize = sys.getsizeof(tag, 1)
        attributeSize = sum(sys.getsizeof(key) + sys.getsizeof(val) for (key, val) in attribute.items())

        self.depth += (tagSize + attributeSize)

        # Define new tag in builder
        #
        log.debug('Processing %s: %s tags.' % (tag, attribute))
        self.builder.start(tag, attribute)

    def end(self, tag):
        """
        Called after a tag has been evaluated.

        :type tag: str
        :rtype: None
        """

        # Close tag in builder
        #
        log.debug('Successfully parsed %s tag.' % tag)
        self.builder.end(tag)

    def data(self, data):
        """
        Nothing to see here.

        :type data: str
        :rtype: None
        """

        # Check for whitespace
        #
        if data.isspace():

            self.builder.data('')

        else:

            log.debug('Parsing %s data.' % data)

            self.depth += sys.getsizeof(data, 1)
            self.builder.data(data)

    def close(self):
        """
        Called after the parser has finished reading the file.

        :rtype: int
        """

        return self.builder.close()


def parse(value):
    """
    Convenience method used to parse the supplied xml value.

    :param value: Supports either a file path or xml string.
    :type value: str
    :rtype: ElementTree.ElementTree
    """

    # Check value type
    #
    if not isinstance(value, string_types):

        raise TypeError('Unable to parse %s value!' % value)

    # Check if this a file path
    #
    if os.path.exists(value):

        # Get file size for xml interceptor
        #
        size = os.stat(value).st_size
        target = Target(size=size)

        # Parse value using class interceptor
        #
        parser = ElementTree.XMLParser(target=target, encoding='utf-8')
        tree = ElementTree.parse(value, parser=parser)

        return tree

    elif len(value) > 0:

        # Get variable size for xml interceptor
        #
        size = sys.getsizeof(value)
        target = Target(size=size)

        # Parse value using class interceptor
        #
        parser = ElementTree.XMLParser(target=target, encoding='utf-8')
        tree = ElementTree.XML(value, parser=parser)

        return tree

    else:

        raise TypeError('Unable to parse supplied string value!')


def cParse(value):
    """
    C-oriented method used to parse the supplied xml value.

    :param value: Supports either a file path or xml string.
    :type value: str
    :rtype: cElementTree.ElementTree
    """

    # Check value type
    #
    if not isinstance(value, string_types):

        raise TypeError('Unable to parse %s value!' % value)

    # Check if this a file path
    #
    if os.path.exists(value):

        # Get file size for xml interceptor
        #
        size = os.stat(value).st_size
        target = Target(size=size)

        # Parse value using class interceptor
        #
        parser = cElementTree.XMLParser(target=target, encoding='utf-8')
        tree = cElementTree.parse(value, parser=parser)

        return tree

    elif len(value) > 0:

        return cElementTree.fromstring(value)

    else:

        raise TypeError('Unable to parse supplied string value!')


def prettify(element, encoding='utf-8', indent='\t'):
    """
    Convenience method for converting xml strings into a readable format.

    :type element: xml.eTree.ElementTree.Element
    :type encoding: basestring
    :type indent: basestring
    :rtype: basestring
    """

    # Check value type
    #
    if isinstance(element, ElementTree.Element):

        xmlString = uglify(element, encoding=encoding)
        parsedString = minidom.parseString(xmlString)

        return parsedString.toprettyxml(indent=indent, newl='\r', encoding=encoding)

    else:

        log.warning('Unable to prettify %s!' % element)
        return ''


def uglify(element, encoding='utf-8'):
    """
    Convenience method for converting xml elements to an un-formatted string.

    :type element: xml.eTree.ElementTree.Element
    :type encoding: basestring
    :rtype: basestring
    """

    # Check value type
    #
    if isinstance(element, ElementTree.Element):

        return ElementTree.tostring(element, encoding)

    else:

        log.warning('Unable to uglify %s!' % element)
        return ''
