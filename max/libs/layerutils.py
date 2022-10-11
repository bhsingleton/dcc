import pymxs

from collections import deque
from dcc.python import stringutils
from dcc.generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def defaultLayer():
    """
    Returns the default layer.

    :rtype: pymxs.MXSWrapperBase
    """

    return pymxs.runtime.LayerManager.getLayerFromName('0').layerAsRefTarg


def isValidLayer(layer):
    """
    Evaluates if the supplied object is a valid layer.

    :type layer: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isKindOf(layer, pymxs.runtime.Base_Layer)


def resetCurrentLayer():
    """
    Resets the current layer back to the default layer.

    :rtype: None
    """

    defaultLayer().current = True


def iterTopLevelLayers():
    """
    Returns a generator that yields top-level layers.

    :rtype: iter
    """

    layerCount = pymxs.runtime.LayerManager.count

    for i in range(layerCount):

        layer = pymxs.runtime.LayerManager.getLayer(i)  # These are zero based???
        parent = layer.getParent()

        if parent is None:

            yield layer.layerAsRefTarg

        else:

            continue


def iterChildLayers(layer):
    """
    Returns a generator that yields children from the supplied layer.

    :type layer: pymxs.MXSWrapperBase
    :rtype: iter
    """

    childCount = layer.getNumChildren()

    for i in inclusiveRange(1, childCount, 1):  # But these are 1 based???

        child = layer.getChild(i)

        if child is not None:

            yield child.layerAsRefTarg

        else:

            continue


def iterParentLayers(layer):
    """
    Returns a generator that yields the parents for the layer.

    :type layer: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Check if layer is valid
    #
    if layer is None:

        return iter([])

    # Iterate through parents
    #
    parent = layer.getParent()

    while parent is not None:

        yield parent.layerAsRefTarg
        parent = parent.getParent()


def traceLayer(layer):
    """
    Returns a generator that yields the parents leading to the supplied layer.

    :type layer: pymxs.MXSWrapperBase
    :rtype: iter
    """

    if layer is not None:

        yield from reversed(list(iterParentLayers(layer)))
        yield layer

    else:

        return iter([])


def walk(*args, **kwargs):
    """
    Returns a generator that yields all descendants from the supplied layers.

    :key ignore: list[pymxs.MXSWrapperBase]
    :rtype: iter
    """

    # Initialize layer queue
    #
    queue = None
    numArgs = len(args)

    if numArgs > 0:

        queue = deque(args)

    else:

        queue = deque(list(iterTopLevelLayers()))

    # Iterate through queue
    #
    ignore = kwargs.get('ignore', [])

    while len(queue) > 0:

        layer = queue.popleft()

        if layer not in ignore:

            yield layer
            queue.extend(list(iterChildLayers(layer)))

        else:

            continue


def iterNodesFromLayers(*layers):
    """
    Returns a generator that yields nodes from the supplied layers.

    :rtype: iter
    """

    # Iterate through layers
    #
    for layer in layers:

        success, nodes = layer.nodes(pymxs.byref(None))

        if success and not stringutils.isNullOrEmpty(nodes):

            numNodes = len(nodes)

            for i in range(numNodes):

                yield nodes[i]

        else:

            continue


def iterLayersFromNodes(*nodes):
    """
    Returns a generator that yields layers from the supplied nodes.

    :rtype: iter
    """

    # Iterate through nodes
    #
    handles = {}

    for node in nodes:

        # Check if layer is valid
        #
        layerInterface = getattr(node, 'layer', None)

        if layerInterface is None:

            continue

        # Check if layer has already been yielded
        #
        layer = layerInterface.layerAsRefTarg
        handle = int(pymxs.runtime.getHandleByAnim(layer))

        wasYielded = handles.get(handle, False)

        if not wasYielded:

            handles[handle] = True
            yield layer

        else:

            continue
