import pymxs

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def iterNodesByPattern(pattern, ignoreCase=False):
    """
    Returns a generator that yields nodes based on the supplied pattern.

    :type pattern: str
    :type ignoreCase: bool
    :rtype: iter
    """

    for obj in pymxs.runtime.objects:

        if pymxs.runtime.matchPattern(obj.name, pattern=pattern, ignoreCase=ignoreCase):

            yield obj


def getNodesByPattern(pattern, ignoreCase=False):
    """
    Returns a list of nodes based on the supplied pattern.

    :type pattern: str
    :type ignoreCase: bool
    :rtype: list[pymxs.runtime.Node]
    """

    return list(iterNodesByPattern(pattern, ignoreCase=ignoreCase))