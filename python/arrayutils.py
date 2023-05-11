from six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isArrayLike(obj):
    """
    Evaluates if the supplied object is like an array.

    :type obj: Any
    :rtype: bool
    """

    return (hasattr(obj, '__getitem__') and hasattr(obj, '__len__')) and not isinstance(obj, string_types)
