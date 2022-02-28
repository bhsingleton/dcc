import json

from dcc.json import psonparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def load(filePath):
    """
    Loads the json objects from the supplied file path.

    :type filePath: str
    :rtype: Any
    """

    with open(filePath, mode='r') as jsonFile:

        return json.load(jsonFile, cls=psonparser.PSONDecoder)


def loads(string, default=None, **kwargs):
    """
    Loads the json objects from the supplied string.
    Any keyword arguments will be passed to the class constructors.

    :type string: str
    :type default: Any
    :rtype: Any
    """

    # Assign keyword defaults
    #
    psonparser.PSONDecoder.__kwdefaults__ = kwargs

    # Try and load json string
    #
    try:

        return json.loads(string, cls=psonparser.PSONDecoder)

    except json.JSONDecodeError as exception:

        log.debug(exception)
        return default


def dump(filePath, obj):
    """
    Dumps the supplied object into the specified json file.

    :type filePath: str
    :type obj: Any
    :rtype: None
    """

    with open(filePath, mode='w') as jsonFile:

        json.dump(obj, jsonFile, cls=psonparser.PSONEncoder, sort_keys=True, indent=4)


def dumps(obj):
    """
    Dumps the supplied object into a json string.

    :type obj: Any
    :rtype: str
    """

    return json.dumps(obj, cls=psonparser.PSONEncoder, sort_keys=True, indent=4)
