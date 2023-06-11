from six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isArrayLike(obj):
    """
    Evaluates if the supplied object is like an array.
    This is useful for C++ array wrappers that aren't derived from the abstract sequence class.

    :type obj: Any
    :rtype: bool
    """

    return (hasattr(obj, '__getitem__') and hasattr(obj, '__len__')) and not isinstance(obj, string_types)


def isIterable(obj):
    """
    Evaluates if the supplied object is iterable.

    :type obj: Any
    :rtype: bool
    """

    return hasattr(obj, '__iter__') and hasattr(obj, '__next__')
