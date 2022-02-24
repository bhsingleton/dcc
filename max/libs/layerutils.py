import pymxs

from collections import deque

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def resetCurrentLayer():
    """
    Resets the current layer back to the default layer.

    :rtype: None
    """

    pymxs.runtime.LayerManager.getLayerFromName('0').current = True


def iterTopLevelLayers():
    """
    Returns a generator that yields top-level layers.

    :rtype: iter
    """

    layerCount = pymxs.runtime.LayerManager.count

    for i in range(1, layerCount + 1, 1):

        layer = pymxs.runtime.LayerManager.getLayer(i)
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

    for i in range(1, childCount + 1, 1):

        yield layer.getChild(i)


def walk(*args, **kwargs):
    """
    Returns a generator that yields all descendants from the supplied layers.

    :keyword ignore: list[pymxs.runtime.LayerProperties]
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

        nodes = pymxs.runtime.Array()
        success = layer.nodes(nodes)

        if success:

            for i in range(nodes.count):

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
