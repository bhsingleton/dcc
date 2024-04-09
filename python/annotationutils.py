import re
import inspect

from typing import Any, Union, List, Tuple, Dict
from six import string_types, integer_types
from six.moves import collections_abc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__type__ = re.compile(r'(?:(?::type\s)|(?::key\s))([a-zA-Z0-9_]+)(?:\:\s)([a-zA-Z._]+[\[a-zA-Z_.,\s\]]*)\n')
__rtype__ = re.compile(r'(?:\:rtype:\s)([a-zA-Z._]+[\[a-zA-Z_.,\s\]]*)\n')
__index__ = re.compile(r'([a-zA-Z._]+)(?:\[([a-zA-Z_.,\s]+)\])?')


NoneType = type(None)


def isParameterizedAlias(obj):
    """
    Evaluates if the supplied type represents a parameterized alias.

    :type obj: Any
    :rtype: bool
    """

    return hasattr(obj, '__origin__') and hasattr(obj, '__args__')


def decomposeAlias(alias):
    """
    Breaks apart the supplied alias into its origin and parameter components.

    :type alias: Any
    :rtype: type, tuple
    """

    if isParameterizedAlias(alias):

        return alias.__origin__, alias.__args__

    elif inspect.isclass(alias):

        return alias, tuple()

    else:

        return type(alias), tuple()


def isArray(T):
    """
    Evaluates if the supplied type is an array.

    :type T: Any
    :rtype: bool
    """

    if inspect.isclass(T):

        return issubclass(T, collections_abc.Sequence) and not issubclass(T, string_types)

    else:

        return isArray(type(T))


def isBuiltinType(T):
    """
    Evaluates if the supplied type is JSON compatible.

    :type T: Any
    :rtype: bool
    """

    if isParameterizedAlias(T):

        origin, parameters = decomposeAlias(T)
        return isBuiltinType(origin) and all([isBuiltinType(x) for x in parameters])

    elif inspect.isclass(T):

        return issubclass(T, (bool, *integer_types, float, *string_types, collections_abc.MutableSequence, collections_abc.MutableMapping, NoneType))

    else:

        return isBuiltinType(type(T))


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

    except (NameError, TypeError):

        log.error('Unable to parse type from string: %s' % string)
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


def getReturnType(func):
    """
    Returns the return type for the given function.

    :type func: function
    :rtype: type
    """

    typeHints = getAnnotations(func)
    return typeHints.get('return', None)
