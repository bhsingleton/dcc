import pymxs

from ..libs import controllerutils, propertyutils, transformutils, meshutils
from ..decorators import modifypaneloverride
from ...python import stringutils
from ...math import floatmath
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
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


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
def setSelection(skin, vertexIndices):
    """
    Updates the active vertex selection for the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type vertexIndices: List[int]
    :rtype: None
    """

    pymxs.runtime.skinOps.selectVertices(skin, vertexIndices)


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
def influenceCount(skin):
    """
    Evaluates the number of influences currently in use by the supplied skin.

    :type skin: pymxs.MXSWrapperBase
    :rtype: int
    """

    return pymxs.runtime.skinOps.getNumberBones(skin)


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
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

            dependencies = pymxs.runtime.refs.dependsOn(skin)
            bone = [node for node in nodes if node in dependencies][0]

        yield boneId, bone


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
def selectInfluence(skin, influenceId):
    """
    Updates the active influence selection inside the skin modifier's list box.

    :type skin: pymxs.MXSWrapperBase
    :type influenceId: int
    :rtype: None
    """

    pymxs.runtime.skinOps.selectBone(skin, influenceId)


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
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


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
def setVertexWeights(skin, vertexWeights):
    """
    Updates the vertex weights for the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type vertexWeights: Dict[int, Dict[int, float]]
    :rtype: None
    """

    # Check if force update is required
    #
    requiresRefresh = pymxs.runtime.skinOps.getNumberVertices(skin) == 0

    if requiresRefresh:

        refreshSkin(skin)

    # Define undo chunk
    #
    with pymxs.undo(True, 'Apply Weights'):

        # Bake selected vertices before applying weights
        # This enables undo support
        #
        pymxs.runtime.skinOps.bakeSelectedVerts(skin)

        # Iterate and replace vertex weights
        #
        for (vertexIndex, influenceWeights) in vertexWeights.items():

            influenceWeights = {key: value for (key, value) in influenceWeights.items() if not floatmath.isClose(0.0, value)}

            pymxs.runtime.skinOps.replaceVertexWeights(
                skin,
                vertexIndex,
                list(influenceWeights.keys()),
                list(influenceWeights.values())
            )

    # Force complete redraw
    # This prevents any zero weights from being returned to the same execution thread!
    #
    pymxs.runtime.completeRedraw()


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
def addInfluence(skin, influence, forceUpdate=False):
    """
    Adds an influence to the specified skin.

    :type skin: pymxs.MXSWrapperBase
    :type influence: pymxs.MXSWrapperBase
    :type forceUpdate: bool
    :rtype: None
    """

    pymxs.runtime.skinOps.addBone(skin, influence, int(forceUpdate))


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
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


@modifypaneloverride.ModifyPanelOverride(objectLevel=0, subObjectLevel=1)
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


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
def refreshSkin(skin):
    """
    Forces the associated node's modifier stack to update.
    This function helps circumvent the bug where the skin modifier will report zero vertices during heavy batch operations!

    :type skin: pymxs.MXSWrapperBase
    :rtype: None
    """

    node = pymxs.runtime.refs.dependentNodes(skin, firstOnly=True)

    if node is not None:

        pymxs.runtime.classOf(node)


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
def copySkin(sourceSkin, targetMesh, influences=None):
    """
    Copies the skin modifier from the source mesh to the target mesh.
    If the vertex counts are identical then the weights will be transferred in order!

    :type sourceSkin: pymxs.runtime.Skin
    :type targetMesh: pymxs.runtime.Node
    :param influences: An additional list of influences to add to the new skin modifier.
    :type influences: Union[List[pymxs.runtime.Node], None]
    :return: The new skin modifier along with a copy of the source influences and remap binder.
    :rtype: Tuple[pymxs.runtime.Skin, Dict[int, pymxs.runtime.Node], Dict[int, int]]
    """

    # Copy source influences and append any extra influences
    #
    sourceInfluences = dict(iterInfluences(sourceSkin))

    if not stringutils.isNullOrEmpty(influences):

        reversedSourceInfluences = {influence.name: influenceId for (influenceId, influence) in sourceInfluences.items()}
        missingInfluences = [influence for influence in influences if reversedSourceInfluences.get(influence.name, None) is None]
        nextAvailableId = max(sourceInfluences.keys()) + 1

        for (influenceId, influence) in enumerate(missingInfluences, start=nextAvailableId):

            sourceInfluences[influenceId] = influence

    # Copy source weights if the vertex counts match
    #
    sourceVertexWeights = {}

    sourceCount = pymxs.runtime.skinOps.getNumberVertices(sourceSkin)
    targetCount = meshutils.vertexCount(targetMesh)

    if sourceCount == targetCount:

        sourceVertexWeights = dict(iterVertexWeights(sourceSkin))

    # Add skin modifier to target mesh
    #
    targetSkin = pymxs.runtime.Skin()
    pymxs.runtime.addModifier(targetMesh, targetSkin)

    refreshSkin(targetSkin)

    # Copy properties and add influences
    #
    propertyutils.copyProperties(sourceSkin, targetSkin)
    sourceInfluenceMap = {}

    for (physicalId, (influenceId, influence)) in enumerate(sourceInfluences.items(), start=1):

        addInfluence(targetSkin, influence)
        sourceInfluenceMap[influenceId] = physicalId

    # Check if vertex weights can be copied
    #
    if sourceCount == targetCount:

        targetVertexWeights = {vertexIndex: {sourceInfluenceMap[influenceId]: influenceWeight for (influenceId, influenceWeight) in influenceWeights.items()} for (vertexIndex, influenceWeights) in sourceVertexWeights.items()}
        setVertexWeights(targetSkin, targetVertexWeights)

    return targetSkin, sourceInfluences, sourceInfluenceMap


@modifypaneloverride.ModifyPanelOverride(objectLevel=0)
def reallocateInfluenceWeights(skin, sourceInfluences, targetInfluence, vertexIndices=None):
    """
    Reallocates any influences from the source list to the target influence.

    :type skin: pymxs.MXSWrapperBase
    :type sourceInfluences: List[int]
    :type targetInfluence: int
    :type vertexIndices: Union[List[int], None]
    :rtype: Dict[int, Dict[int, float]]
    """

    # Iterate through vertex weights
    #
    vertexWeights = dict(iterVertexWeights(skin, vertexIndices=vertexIndices))
    sourceInfluenceMap = dict.fromkeys(sourceInfluences, True)

    reallocatedWeights = {}

    for (vertexIndex, influenceWeights) in vertexWeights.items():

        # Iterate through influence weights
        #
        pendingWeights = dict(influenceWeights)

        for (influenceId, influenceWeight) in influenceWeights.items():

            # Check if influence is in source list
            #
            hasSourceInfluence = sourceInfluenceMap.get(influenceId, False)

            if hasSourceInfluence:

                pendingWeights[targetInfluence] = pendingWeights.get(targetInfluence, 0.0) + influenceWeight
                del pendingWeights[influenceId]

        reallocatedWeights[vertexIndex] = pendingWeights

    # Update vertex weights
    #
    setVertexWeights(skin, reallocatedWeights)

    return reallocatedWeights
