import pymxs

from dcc.python import stringutils
from dcc.math import linearalgebra
from dcc.generators.inclusiverange import inclusiveRange
from dcc.max.decorators.commandpaneloverride import commandPanelOverride

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@commandPanelOverride(mode='modify', select=0)
def iterSelection(skin):
    """
    Returns a generator that yields the active vertex selection from the supplied skin.

    :type skin: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Iterate through vertices
    #
    numVertices = pymxs.runtime.skinOps.getNumberVertices(skin)

    for i in inclusiveRange(1, numVertices):

        # Check if vertex is selected
        #
        if pymxs.runtime.skinOps.isVertexSelected(skin, i):

            yield i

        else:

            continue


def getSelection(skin):
    """
    Returns the active vertex selection from the supplied skin.

    :type skin: pymxs.MXSWrapperBase
    :rtype: List[int]
    """

    return list(iterSelection(skin))


@commandPanelOverride(mode='modify', select=0)
def setSelection(skin, vertexIndices):
    """
    Updates the active vertex selection for the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type vertexIndices: List[int]
    :rtype: None
    """

    pymxs.runtime.skinOps.selectVertices(skin, vertexIndices)


@commandPanelOverride(mode='modify', select=0)
def influenceCount(skin):
    """
    Evaluates the number of influences currently in use by the supplied skin.

    :type skin: pymxs.MXSWrapperBase
    :rtype: int
    """

    return pymxs.runtime.skinOps.getNumberBones(skin)


@commandPanelOverride(mode='modify', select=0)
def iterInfluences(skin):
    """
    Returns a generator that yields the influence objects from the supplied skin.

    :rtype: iter
    """

    # Iterate through bones
    #
    numBones = pymxs.runtime.skinOps.getNumberBones(skin)

    for i in inclusiveRange(1, numBones, 1):

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


@commandPanelOverride(mode='modify', select=0)
def selectInfluence(skin, influenceId):
    """
    Updates the active influence selection inside the skin modifier's list box.

    :type skin: pymxs.MXSWrapperBase
    :type influenceId: int
    :rtype: None
    """

    pymxs.runtime.skinOps.selectBone(skin, influenceId)


@commandPanelOverride(mode='modify', select=0)
def iterVertexWeights(skin, vertexIndices=None):
    """
    Returns a generator that yields vertex weights from the specified vertex indices.
    If no vertex indices are supplied then all weights are yielded instead.

    :type skin: pymxs.MXSWrapperBase
    :type vertexIndices: List[int]
    :rtype: iter
    """

    # Inspect arguments
    #
    if stringutils.isNullOrEmpty(vertexIndices):

        numVertices = pymxs.runtime.skinOps.getNumberVertices(skin)
        vertexIndices = inclusiveRange(1, numVertices)

    # Iterate through arguments
    #
    for vertexIndex in vertexIndices:

        # Iterate through bones
        #
        numBones = pymxs.runtime.skinOps.getVertexWeightCount(skin, vertexIndex)

        vertexWeights = {}

        for i in inclusiveRange(1, numBones):

            boneId = pymxs.runtime.skinOps.getVertexWeightBoneID(skin, vertexIndex, i)
            boneWeight = pymxs.runtime.skinOps.getVertexWeight(skin, vertexIndex, i)

            vertexWeights[boneId] = boneWeight

        # Yield vertex weights
        #
        yield vertexIndex, vertexWeights


def getVertexWeights(skin, vertexIndices=None):
    """
    Returns the vertex weights from the specified vertex indices.
    If no vertex indices are supplied then all weights are yielded instead.

    :type skin: pymxs.MXSWrapperBase
    :type vertexIndices: List[int]
    :rtype: iter
    """

    return dict(iterVertexWeights(skin, vertexIndices=vertexIndices))


@commandPanelOverride(mode='modify', select=0)
def setVertexWeights(skin, vertexWeights):
    """
    Updates the vertex weights for the specified skin.

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


@commandPanelOverride(mode='modify', select=0)
def addInfluence(skin, influence):
    """
    Adds an influence to the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type influence: pymxs.MXSWrapperBase
    :rtype: None
    """

    pymxs.runtime.skinOps.addBone(skin, influence, 0)


@commandPanelOverride(mode='modify', select=0)
def removeInfluence(skin, influenceId):
    """
    Adds an influence to the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type influenceId: int
    :rtype: None
    """

    pymxs.runtime.skinOps.removeBone(skin, influenceId)


@commandPanelOverride(mode='modify', select=0)
def resetPreBindMatrices(skin):
    """
    Resets the pre-bind matrices on the associated joints.

    :rtype: None
    """

    skin.always_deforms = False
    skin.always_deforms = True


@commandPanelOverride(mode='modify', select=0, subObjectLevel=1)
def showColors(skin):
    """
    Enables the vertex color feedback for the supplied skin.

    :pymxs.MXSWrapperBase
    :rtype: None
    """

    # Modify display settings
    #
    skin.drawVertices = True
    skin.shadeWeights = True
    skin.colorAllWeights = False
    skin.draw_all_envelopes = False
    skin.draw_all_vertices = False
    skin.draw_all_gizmos = False
    skin.showNoEnvelopes = True
    skin.showHiddenVertices = False
    skin.crossSectionsAlwaysOnTop = True
    skin.envelopeAlwaysOnTop = True
