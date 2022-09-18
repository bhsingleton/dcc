import maya.cmds as mc
import maya.api.OpenMaya as om

from . import dagutils, plugutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def iterNodesFromLayers(*layers):
    """
    Returns a generator that yields nodes from the supplied layers.

    :rtype: iter
    """

    # Iterate through layers
    #
    for layer in layers:

        # Find ".drawInfo" plug and evaluate connections
        #
        layer = dagutils.getMObject(layer)
        plug = plugutils.findPlug(layer, 'drawInfo')

        otherPlugs = plug.connectedTo(False, True)

        for otherPlug in otherPlugs:

            yield otherPlug.node()


def iterLayersFromNodes(*nodes):
    """
    Returns a generator that yields layers from the supplied nodes.

    :rtype: iter
    """

    # Iterate through nodes
    #
    yielded = {}

    for node in nodes:

        # Find ".drawOverride" plug and evaluate connections
        #
        node = dagutils.getMObject(node)
        plug = plugutils.findPlug(node, 'drawOverride')

        otherPlugs = plug.connectedTo(True, False)
        numOtherPlugs = len(otherPlugs)

        if numOtherPlugs == 0:

            continue

        # Check if layer has already been yielded
        #
        layer = otherPlugs[0].node()
        handle = om.MObjectHandle(layer).hashCode()

        wasYielded = yielded.get(handle, False)

        if not wasYielded:

            yielded[handle] = True
            yield layer

        else:

            continue


def getLayerFromNode(node):
    """
    Returns the layer associated with the given node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MObject
    """

    layers = list(iterLayersFromNodes(node))
    numLayers = len(layers)

    if numLayers == 1:

        return layers[0]

    else:

        return None


def addNodesToLayer(layer, nodes):
    """
    Adds the supplied nodes to the specified layer.

    :type layer: Union[str, om.MObject, om.MDagPath]
    :type nodes: Sequence[Union[str, om.MObject, om.MDagPath]]
    :rtype: None
    """

    layer = dagutils.getMObject(layer)

    for node in nodes:

        node = dagutils.getMObject(node)
        source = plugutils.findPlug(layer, 'drawInfo')
        destination = plugutils.findPlug(node, 'drawOverride')

        plugutils.connectPlugs(source, destination, force=True)


def removeNodesFromLayer(layer, nodes):
    """
    Removes the supplied nodes from the specified layer.

    :type layer: Union[str, om.MObject, om.MDagPath]
    :type nodes: Sequence[Union[str, om.MObject, om.MDagPath]]
    :rtype: None
    """

    layer = dagutils.getMObject(layer)

    for node in nodes:

        node = dagutils.getMObject(node)
        source = plugutils.findPlug(layer, 'drawInfo')
        destination = plugutils.findPlug(node, 'drawOverride')

        plugutils.disconnectPlugs(source, destination)
