import pymxs

from collections import deque

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
    :rtype: List[pymxs.runtime.Node]
    """

    return list(iterNodesByPattern(pattern, ignoreCase=ignoreCase))


def iterParents(node):
    """
    Returns a generator that yields all parents from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: iter
    """

    parent = node.parent

    while parent is not None:

        yield parent
        parent = parent.parent


def parents(node):
    """
    Returns a list of parents from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: iter
    """

    return list(iterParents(node))


def iterChildren(node):
    """
    Returns a generator that yields all children from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: iter
    """

    numChildren = node.children.count

    for i in range(numChildren):

        yield node.children[i]


def children(node):
    """
    Returns a list of children from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: iter
    """

    return list(iterChildren(node))


def iterDescendants(node):
    """
    Returns a generator that yields all child descendants from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: iter
    """

    queue = deque(children(node))

    while len(queue) > 0:

        child = queue.popleft()
        yield child

        queue.extend(children(child))


def descendants(node):
    """
    Returns a list of descendants from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: iter
    """

    return list(iterDescendants(node))
