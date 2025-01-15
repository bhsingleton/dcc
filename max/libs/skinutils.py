import pymxs

from ..libs import controllerutils, transformutils, meshutils
from ..decorators import modifypaneloverride
from ...python import stringutils
from ...math import floatmath
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
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


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
def setSelection(skin, vertexIndices):
    """
    Updates the active vertex selection for the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type vertexIndices: List[int]
    :rtype: None
    """

    pymxs.runtime.skinOps.selectVertices(skin, vertexIndices)


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
def influenceCount(skin):
    """
    Evaluates the number of influences currently in use by the supplied skin.

    :type skin: pymxs.MXSWrapperBase
    :rtype: int
    """

    return pymxs.runtime.skinOps.getNumberBones(skin)


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
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


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
def selectInfluence(skin, influenceId):
    """
    Updates the active influence selection inside the skin modifier's list box.

    :type skin: pymxs.MXSWrapperBase
    :type influenceId: int
    :rtype: None
    """

    pymxs.runtime.skinOps.selectBone(skin, influenceId)


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
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


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
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

            weights = {key: value for (key, value) in weights.items() if not floatmath.isClose(0.0, value)}

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


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
def addInfluence(skin, influence):
    """
    Adds an influence to the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type influence: pymxs.MXSWrapperBase
    :rtype: None
    """

    pymxs.runtime.skinOps.addBone(skin, influence, 0)


@modifypaneloverride.ModifyPanelOverride(currentObject=0)
def removeInfluence(skin, influenceId):
    """
    Adds an influence to the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type influenceId: int
    :rtype: None
    """

    pymxs.runtime.skinOps.removeBone(skin, influenceId)


def resetSkin(skin):
    """
    Resets the associated mesh's transform matrix.

    :type skin: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Check if mesh has been frozen
    #
    node = pymxs.runtime.refs.dependentNodes(skin, firstOnly=True)

    if controllerutils.isFrozen(node):

        log.info('Un-freezing "%s" mesh!' % node.name)
        transformutils.unfreezeTransform(node)

    # Check if reset is required
    #
    meshBindMatrix = pymxs.runtime.skinutils.getMeshBindTM(node)
    objectMatrix = pymxs.runtime.copy(node.objectTransform) * transformutils.getWorldInverseMatrix(node)

    identityMatrix = pymxs.runtime.Matrix3(1)

    if transformutils.isClose(identityMatrix, meshBindMatrix) and transformutils.isClose(identityMatrix, objectMatrix):

        return

    # Bake transforms into mesh vertices
    #
    baseObject = getattr(node, 'baseObject', node)

    verts = [point * (objectMatrix * meshBindMatrix) for point in meshutils.iterVertices(baseObject)]
    numVerts = len(verts)

    log.info('Baking object-transform on "%s" node into base-object!' % node.name)
    meshutils.setVertices(baseObject, list(inclusiveRange(1, numVerts, 1)), verts)

    # Ensure mesh has no parent
    #
    if node.parent is not None:

        node.parent = None

    # Reset transform matrices
    #
    transformutils.resetTransform(node)
    transformutils.resetObjectTransform(node)
    resetMeshBindMatrix(skin)


def resetMeshBindMatrix(skin):
    """
    Resets the pre-bind matrix on the associated mesh.

    :type skin: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Reset mesh pre-bind matrix
    #
    node = pymxs.runtime.refs.dependentNodes(skin, firstOnly=True)
    worldMatrix = transformutils.getWorldMatrix(node)

    log.info('Resetting mesh-bind matrix on "%s" node!' % node.name)
    pymxs.runtime.skinutils.setMeshBindTM(node, worldMatrix)


def resetBoneBindMatrices(skin):
    """
    Resets the pre-bind matrices on the associated joints.

    :type skin: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Reset influence pre-bind matrices
    #
    node = pymxs.runtime.refs.dependentNodes(skin, firstOnly=True)
    log.info('Resetting bone-bind matrices on "%s" node!' % node.name)

    for (influenceId, influence) in iterInfluences(skin):

        worldMatrix = transformutils.getWorldMatrix(influence)
        pymxs.runtime.skinutils.setBoneBindTM(node, influence, worldMatrix)


def bakeBindPose(skin):
    """
    Bakes the current bind-pose into the skin modifier.

    :type skin: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Ensure mesh has no transforms
    #
    resetSkin(skin)

    # Bake current pose into base object
    #
    node = pymxs.runtime.refs.dependentNodes(skin, firstOnly=True)
    baseObject = getattr(node, 'baseObject', node)

    verts = [pymxs.runtime.Point3(*point) for point in meshutils.iterVertices(node)]
    numVerts = len(verts)

    log.info('Baking "%s" mesh changes into base-object!' % node.name)
    meshutils.setVertices(baseObject, list(inclusiveRange(1, numVerts, 1)), verts)

    # Reset bone-bind matrices
    #
    resetBoneBindMatrices(skin)


@modifypaneloverride.ModifyPanelOverride(currentObject=0, subObjectLevel=1)
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
