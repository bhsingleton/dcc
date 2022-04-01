import re

from typing import *  # Used for eval operations!

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__type__ = re.compile(r'(?:(?::type\s)|(?::key\s))([a-zA-Z0-9_]+)(?:\:\s)([a-zA-Z._]+[\[a-zA-Z_.,\s\]]*)\n')
__rtype__ = re.compile(r'(?:\:rtype:\s)([a-zA-Z._]+[\[a-zA-Z_.,\s\]]*)\n')
__index__ = re.compile(r'([a-zA-Z._]+)(?:\[([a-zA-Z_.,\s]+)\])?')


def isNullOrEmpty(value):
    """
    Evaluates if the supplied value is null or empty.

    :type value: Any
    :rtype: bool
    """

    if hasattr(value, '__len__'):

        return len(value) == 0

    elif value is None:

        return True

    else:

        raise TypeError('isNullOrEmpty() expects a sequence (%s given)!' % type(value).__name__)


def getTypeFromString(string, __globals__=None, __locals__=None):
    """
    Returns the type from the given string.

    :type string: str
    :type __globals__: dict
    :type __locals__: dict
    :rtype: type
    """

    # Check if globals were supplied
    #
    if __globals__ is None:

        __globals__ = globals()

    # Check if locals were supplied
    #
    if __locals__ is None:

        __locals__ = locals()

    # Check if type uses indexer
    #
    try:

        return eval(string, __globals__, __locals__)

    except TypeError:

        log.error('getTypeFromString() error while parsing string: %s' % string)
        return object


def getAnnotations(func):
    """
    Returns a dictionary of annotations by parsing the supplied function's docstring.
    For optimization purposes this dictionary will be cached inside the function.

    :type func: method
    :rtype: dict
    """

    # Check if annotations have already been parsed
    # Be sure to check if there is an actual docstring
    #
    annotations = func.__annotations__
    numAnnotations = len(annotations)

    if numAnnotations > 0 or func.__doc__ is None:

        return func.__annotations__

    # Parse docstring types
    #
    types = __type__.findall(func.__doc__)
    numTypes = len(types)

    __locals__ = func.__globals__

    if numTypes > 0:

        annotations.update({key: getTypeFromString(value, __locals__=__locals__) for (key, value) in types})

    # Parse docstring return
    #
    returnType = __rtype__.findall(func.__doc__)
    hasReturnType = len(returnType) == 1

    if hasReturnType:

        annotations['return'] = getTypeFromString(returnType[0], __locals__=__locals__)

    return annotations
