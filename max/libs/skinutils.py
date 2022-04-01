import pymxs

from dcc.math import linearalgebra
from dcc.max.decorators import commandpaneloverride

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isNullOrEmpty(value):
    """
    Evaluates if the supplied value is null or empty.

    :type value: Any
    :rtype: bool
    """

    if hasattr(value, '__len__'):

        return len(value) == 0

    elif value is None:

        return True

    else:

        raise TypeError('isNullOrEmpty() expects a sequence (%s given)!' % type(value).__name__)


@commandpaneloverride.commandPanelOverride(mode='modify')
def iterSelection(skin):
    """
    Returns a generator that yields the selected vertex indices.
    This operation is not super efficient in max...

    :type skin: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Iterate through vertices
    #
    numVertices = pymxs.runtime.skinOps.getNumberVertices(skin)

    for i in range(1, numVertices + 1, 1):

        # Check if vertex is selected
        #
        if pymxs.runtime.skinOps.isVertexSelected(skin, i):

            yield i

        else:

            continue


@commandpaneloverride.commandPanelOverride(mode='modify')
def iterInfluences(skin):
    """
    Returns a generator that yields all the influence objects from this modifier.

    :rtype: iter
    """

    # Iterate through bones
    #
    numBones = pymxs.runtime.skinOps.getNumberBones(skin)

    for i in range(1, numBones + 1, 1):

        # Get bone properties
        #
        boneId = pymxs.runtime.skinOps.getBoneIDByListID(skin, i)
        boneName = pymxs.runtime.skinOps.getBoneName(skin, boneId, 0)

        # Get bone from name
        #
        nodes = pymxs.runtime.getNodeByName(boneName, ignoreCase=False, all=True)
        numNodes = nodes.count

        bone = None

        if numNodes == 0:

            raise RuntimeError('iterInfluences() cannot locate bone from name: %s' % boneName)

        elif numNodes == 1:

            bone = nodes[0]

        else:

            dependencies = pymxs.runtime.dependsOn(skin)
            bone = [x for x in nodes if x in dependencies][0]

        yield boneId, bone


@commandpaneloverride.commandPanelOverride(mode='modify')
def iterVertexWeights(skin, vertexIndices=None):
    """
    Returns a generator that yields weights for the supplied vertex indices.
    If no vertex indices are supplied then all weights are yielded instead.

    :type skin: pymxs.MXSWrapperBase
    :type vertexIndices: List[int]
    :rtype: iter
    """

    # Inspect arguments
    #
    if isNullOrEmpty(vertexIndices):

        numVertices = pymxs.runtime.skinOps.getNumberVertices(skin)
        vertexIndices = range(1, numVertices + 1, 1)

    # Iterate through arguments
    #
    for vertexIndex in vertexIndices:

        # Iterate through bones
        #
        numBones = pymxs.runtime.skinOps.getVertexWeightCount(skin, vertexIndex)

        vertexWeights = {}

        for i in range(1, numBones + 1, 1):

            boneId = pymxs.runtime.skinOps.getVertexWeightBoneID(skin, vertexIndex, i)
            boneWeight = pymxs.runtime.skinOps.getVertexWeight(skin, vertexIndex, i)

            vertexWeights[boneId] = boneWeight

        # Yield vertex weights
        #
        yield vertexIndex, vertexWeights


@commandpaneloverride.commandPanelOverride(mode='modify')
def setVertexWeights(skin, vertexWeights):
    """
    Assigns the supplied vertex weights to this modifier.

    :type skin: pymxs.MXSWrapperBase
    :type vertexWeights: Dict[int, Dict[int, float]]
    :rtype: None
    """

    # Define undo chunk
    #
    with pymxs.undo(True, 'Apply Weights'):

        # Bake selected vertices before applying weights
        # This enables undo support
        #
        pymxs.runtime.skinOps.bakeSelectedVerts(skin)

        # Iterate and replace vertex weights
        #
        for (vertexIndex, weights) in vertexWeights.items():

            weights = {key: value for (key, value) in weights.items() if not linearalgebra.isClose(0.0, value)}

            pymxs.runtime.skinOps.replaceVertexWeights(
                skin,
                vertexIndex,
                list(weights.keys()),
                list(weights.values())
            )

    # Force complete redraw
    # This prevents any zero weights from being returned to the same execution thread!
    #
    pymxs.runtime.completeRedraw()
