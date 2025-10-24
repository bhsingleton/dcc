import os
import json
import zlib

from . import psonparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def compress(string):
    """
    Compresses the supplied string.

    :type string: str
    :rtype: str
    """

    try:

        return zlib.compress(string.encode('utf-8')).decode()

    except zlib.error as exception:

        log.debug(exception)
        return string


def decompress(string):
    """
    Decompresses the supplied string.

    :type string: str
    :rtype: str
    """

    try:

        return zlib.decompress(string.encode('utf-8')).decode()

    except zlib.error as exception:

        log.debug(exception)
        return string


def load(filePath, **kwargs):
    """
    Loads the json objects from the supplied file path.
    Any keyword arguments will be passed to the class constructors.

    :type filePath: str
    :rtype: Any
    """

    # Check if json file exists
    #
    if not os.path.isfile(filePath):

        return kwargs.get('default', None)

    # Load json string from from file
    #
    with open(filePath, mode='r') as jsonFile:

        return loads(jsonFile.read(), **kwargs)


def loads(string, default=None, **kwargs):
    """
    Loads the json objects from the supplied string.
    Any keyword arguments will be passed to the class constructors.

    :type string: str
    :type default: Any
    :rtype: Any
    """

    # Check if string needs decompressing
    #
    isCompressed = kwargs.get('decompress', False)

    if isCompressed:

        string = decompress(string)

    # Try and load json string
    #
    cls = kwargs.pop('cls', psonparser.PSONDecoder)

    try:

        return json.loads(string, cls=cls, **kwargs)

    except json.JSONDecodeError as exception:

        log.debug(exception)
        return default


def dump(filePath, obj, **kwargs):
    """
    Dumps the supplied object into the specified json file.

    :type filePath: str
    :type obj: Any
    :rtype: None
    """

    cls = kwargs.pop('cls', psonparser.PSONEncoder)

    with open(filePath, mode='w') as jsonFile:

        json.dump(obj, jsonFile, cls=cls, **kwargs)


def dumps(obj, **kwargs):
    """
    Dumps the supplied object into a json string.

    :type obj: Any
    :rtype: str
    """

    # Serialize python object
    #
    cls = kwargs.pop('cls', psonparser.PSONEncoder)
    string = json.dumps(obj, cls=cls, **kwargs)

    # Check if string should be compressed
    #
    isCompressed = kwargs.get('compress', False)

    if isCompressed:

        return compress(string)

    else:

        return string
