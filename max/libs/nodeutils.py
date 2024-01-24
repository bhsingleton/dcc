import pymxs

from collections import deque

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


def isValidNode(obj):
    """
    Evaluates if the supplied object is a valid scene node.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isValidNode(obj) and not pymxs.runtime.isDeleted(obj)


def doesNodeExist(*names, ignoreCase=False):
    """
    Evaluates if a node with the specified name exists.

    :type names: Union[str, List[str]]
    :type ignoreCase: bool
    :rtype: bool
    """

    return all(pymxs.runtime.getNodeByName(name, ignoreCase=ignoreCase, all=True).count > 0 for name in names)


def isValidBaseObject(obj):
    """
    Evaluates if the supplied object is a valid base object.
    Unlike a node, base objects do not have names or transforms.
    Be aware that the MXS "isKindOf" method will evaluate a sub-anim object's value rather than the object itself!

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isKindOf(obj, pymxs.runtime.Node) and not pymxs.runtime.isKindOf(obj, pymxs.runtime.SubAnim)


def isValidScene(obj):
    """
    Evaluates if the supplied object is a valid scene object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return (pymxs.runtime.isKindOf(obj, pymxs.runtime.Scene) and pymxs.runtime.isValidObj(obj)) and not pymxs.runtime.isDeleted(obj)


def baseObject(node):
    """
    Returns the base object for the given node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    return getattr(node, 'baseObject', node)


def iterNodesByPattern(*patterns, ignoreCase=False):
    """
    Returns a generator that yields nodes based on the supplied pattern.

    :type patterns: Union[str, Tuple[str]]
    :type ignoreCase: bool
    :rtype: iter
    """

    for obj in pymxs.runtime.objects:

        if any([pymxs.runtime.matchPattern(obj.name, pattern=pattern, ignoreCase=ignoreCase) for pattern in patterns]):

            yield obj


def getNodesByPattern(pattern, ignoreCase=False):
    """
    Returns a list of nodes based on the supplied pattern.

    :type pattern: str
    :type ignoreCase: bool
    :rtype: List[pymxs.MXSWrapperBase]
    """

    return list(iterNodesByPattern(pattern, ignoreCase=ignoreCase))


def iterTopLevelNodes():
    """
    Returns a generator that yields top-level nodes.
    Probably
    :rtype: iter
    """

    return iterChildren(pymxs.runtime.rootNode)


def iterSelectionSets():
    """
    Returns a generator that yields selection set name-nodes pairs.

    :rtype: iter
    """

    # Iterate through selection sets
    #
    numSelectionSets = pymxs.runtime.selectionSets.count

    for i in range(numSelectionSets):

        # Check if selection set still exists
        # Deleted sets can persist between sessions!
        #
        selectionSet = pymxs.runtime.selectionSets[i]

        if pymxs.runtime.isDeleted(selectionSet):

            continue

        # Yield name and nodes from selection set
        #
        name = str(selectionSet.name)
        nodes = tuple([selectionSet[j] for j in range(selectionSet.count)])

        yield name, nodes


def isUniqueName(name):
    """
    Evaluates if the supplied name is unique.

    :type name: str
    :rtype: bool
    """

    return pymxs.runtime.getNodeByName(name, exact=True, ignoreCase=False, all=True).count <= 1


def getAnimHandle(obj):
    """
    Returns the handle for the given animatable.
    This method exists to circumvent a bug in 3ds Max 2019 where pymxs used to return a float rather than an int.

    :type obj: pymxs.MXSWrapperBase
    :rtype: int
    """

    if pymxs.runtime.isValidObj(obj):

        return int(pymxs.runtime.getHandleByAnim(obj))

    else:

        return None


def getPartialPathTo(node):
    """
    Returns the shortest path that can safely be used for name lookups.

    :type node: pymxs.MXSWrapperBase
    :rtype: str
    """

    # Check if node is valid
    #
    if not pymxs.runtime.isValidNode(node):

        return None

    # Check if node name is unique
    #
    nodeName = getattr(node, 'name', '')

    if isUniqueName(nodeName):

        return '${nodeName}'.format(nodeName=nodeName)

    else:

        return getFullPathTo(node)


def getFullPathTo(node):
    """
    Returns the full path for the given object.

    :type node: pymxs.MXSWrapperBase
    :rtype: str
    """

    # Check if node is valid
    #
    if pymxs.runtime.isValidNode(node):

        return '${path}'.format(path='/'.join([x.name for x in trace(node)]))

    else:

        return None


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

    if not pymxs.runtime.isValidNode(node):

        return iter([])

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
