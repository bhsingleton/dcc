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

    :rtype: pymxs.runtime.LayerProperties
    """

    return pymxs.runtime.LayerManager.getLayerFromName('0')


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

            yield layer

        else:

            continue


def iterChildLayers(layer):
    """
    Returns a generator that yields children from the supplied layer.

    :type layer: pymxs.runtime.LayerProperties
    :rtype: iter
    """

    childCount = layer.getNumChildren()

    for i in inclusiveRange(1, childCount):  # But these are 1 based???

        yield layer.getChild(i)


def walk(*args, **kwargs):
    """
    Returns a generator that yields all descendants from the supplied layers.

    :key ignore: list[pymxs.runtime.LayerProperties]
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

    yielded = {}

    for node in nodes:

        layer = node.layer
        wasYielded = yielded.get(layer.name, False)

        if not wasYielded:

            yielded[layer.name] = True
            yield layer

        else:

            continue
