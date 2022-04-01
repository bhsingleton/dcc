import json

from dcc.json import psonparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def load(filePath, **kwargs):
    """
    Loads the json objects from the supplied file path.
    Any keyword arguments will be passed to the class constructors.

    :type filePath: str
    :rtype: Any
    """

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

    # Try and load json string
    #
    try:

        return json.loads(string, cls=psonparser.PSONDecoder, **kwargs)

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

    with open(filePath, mode='w') as jsonFile:

        json.dump(obj, jsonFile, cls=psonparser.PSONEncoder, **kwargs)


def dumps(obj, **kwargs):
    """
    Dumps the supplied object into a json string.

    :type obj: Any
    :rtype: str
    """

    return json.dumps(obj, cls=psonparser.PSONEncoder, **kwargs)
