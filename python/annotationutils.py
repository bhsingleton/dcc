import re
import sys

try:

    from typing import *

except ImportError:

    pass

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__type__ = re.compile(r'(?:(?::type\s)|(?::key\s))([a-zA-Z0-9]+)(?:\:\s)([a-zA-Z._]+[\[a-zA-Z,\s\]]*)\n')
__rtype__ = re.compile(r'(?::rtype:\s)([a-zA-Z._]+[\[a-zA-Z,\s\]]*)\n')
__index__ = re.compile(r'([a-zA-Z._]+)(?:\[([a-zA-Z._,\s]+)\])?')


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


def getPython2TypeFromString(string, __globals=None, __locals=None):
    """
    Returns the python2x type from the given string.

    :type string: str
    :type __globals: dict
    :type __locals: dict
    :rtype: type
    """

    # Check if globals were supplied
    #
    if __globals is None:

        __globals = globals()

    # Check if locals were supplied
    #
    if __locals is None:

        __locals = locals()

    # Check if type uses indexer
    #
    name, index = __index__.findall(string)[0]

    if name in ('Any', 'Callable'):

        return object

    elif name in ('Union', 'Sequence', 'List', 'Dict'):

        return tuple(getPython2TypeFromString(x) for x in index)

    else:

        return eval(name, __globals=__globals, __locals=__locals)


def getPython3TypeFromString(string, __globals=None, __locals=None):
    """
    Returns the python3x type from the given string.

    :type string: str
    :type __globals: dict
    :type __locals: dict
    :rtype: type
    """

    # Check if globals were supplied
    #
    if __globals is None:

        __globals = globals()

    # Check if locals were supplied
    #
    if __locals is None:

        __locals = locals()

    # Check if type uses indexer
    #
    return eval(string, __globals=__globals, __locals=__locals)


def getTypeFromString(string, __globals=None, __locals=None):
    """
    Returns the type from the given string.

    :type string: str
    :type __globals: dict
    :type __locals: dict
    :rtype: type
    """

    if sys.version_info.major == 2:

        return getPython2TypeFromString(string, __globals=__globals, __locals=__locals)

    else:

        return getPython3TypeFromString(string, __globals=__globals, __locals=__locals)


def getAnnotations(func):
    """
    Returns a dictionary of annotations by parsing the supplied function's docstring.
    For optimization purposes this dictionary will cached inside the function.

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

    __globals = func.__globals__

    if numTypes > 0:

        annotations.update({key: getTypeFromString(value, __globals=__globals) for (key, value) in types})

    # Parse docstring return
    #
    rtype = __rtype__.findall(func.__doc__)
    hasRType = len(rtype) == 1

    if hasRType:

        annotations['return'] = getTypeFromString(rtype[0], __globals=__globals)

    return annotations
