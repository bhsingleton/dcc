from ..vendor.six import string_types
from ..vendor.six.moves import collections_abc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isArray(obj):
    """
    Evaluates if the supplied object is an array.

    :type obj: Any
    :rtype: bool
    """

    return isinstance(obj, collections_abc.Sequence) and not isinstance(obj, string_types)


def isArrayLike(obj):
    """
    Evaluates if the supplied object is like an array.
    This is useful for C++ array wrappers that aren't derived from the abstract sequence class.

    :type obj: Any
    :rtype: bool
    """

    return (hasattr(obj, '__getitem__') and hasattr(obj, '__len__')) and not isinstance(obj, string_types)


def isIterator(obj):
    """
    Evaluates if the supplied object is an iterator.

    :type obj: Any
    :rtype: bool
    """

    return isinstance(obj, collections_abc.Iterator) and not isinstance(obj, string_types)


def isIteratorLike(obj):
    """
    Evaluates if the supplied object is like an iterator.

    :type obj: Any
    :rtype: bool
    """

    return (hasattr(obj, '__iter__') and hasattr(obj, '__next__')) and not isinstance(obj, string_types)


def isHashMap(obj):
    """
    Evaluates if the supplied object is a mapped object.

    :type obj: Any
    :rtype: bool
    """

    return isinstance(obj, collections_abc.Mapping)
