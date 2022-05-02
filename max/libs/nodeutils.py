import pymxs

from collections import deque
from . import arrayutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


BASE_TYPES = {
    'GeometryClass':  pymxs.runtime.GeometryClass,
    'shape':  pymxs.runtime.shape,
    'light':  pymxs.runtime.light,
    'camera':  pymxs.runtime.camera,
    'helper':  pymxs.runtime.helper
}


def isAnimatable(obj):
    """
    Evaluates if the supplied object is derived from animatable.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isProperty(obj, 'numSubs')


def isValidScene(obj):
    """
    Evaluates if the supplied object is a valid scene object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isKindOf(obj, pymxs.runtime.Scene)


def baseObject(node):
    """
    Returns the base object for the given node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    if pymxs.runtime.isProperty(node, 'baseObject'):

        return node.baseObject

    else:

        return node


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


def iterTopLevelNodes():
    """
    Returns a generator that yields top-level nodes.
    Probably
    :rtype: iter
    """

    return iterChildren(pymxs.runtime.rootNode)


def dagPath(node):
    """
    Returns the dag path for the given object.

    :type node: pymxs.MXSWrapperBase
    :rtype: str
    """

    return '|'.join([x.name for x in trace(node)])


def getNodesByPattern(pattern, ignoreCase=False):
    """
    Returns a list of nodes based on the supplied pattern.

    :type pattern: str
    :type ignoreCase: bool
    :rtype: List[pymxs.MXSWrapperBase]
    """

    return list(iterNodesByPattern(pattern, ignoreCase=ignoreCase))


def iterParents(node):
    """
    Returns a generator that yields all parents from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: iter
    """

    parent = getattr(node, 'parent', None)

    while parent is not None:

        yield parent
        parent = getattr(parent, 'parent', None)


def getParents(node):
    """
    Returns a list of parents from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: iter
    """

    return list(iterParents(node))


def iterChildren(node):
    """
    Returns a generator that yields all children from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: iter
    """

    children = getattr(node, 'children', pymxs.runtime.Array())

    for i in range(children.count):

        yield children[i]


def getChildren(node):
    """
    Returns a list of children from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: iter
    """

    return list(iterChildren(node))


def trace(node):
    """
    Returns a generator that yields the nodes leading to the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: iter
    """

    parents = getParents(node)

    for parent in reversed(parents):

        yield parent

    yield node


def iterDescendants(node):
    """
    Returns a generator that yields all child descendants from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: iter
    """

    queue = deque(getChildren(node))

    while len(queue) > 0:

        child = queue.popleft()
        yield child

        queue.extend(getChildren(child))


def descendants(node):
    """
    Returns a list of descendants from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: iter
    """

    return list(iterDescendants(node))
