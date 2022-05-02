import maya.cmds as mc
import maya.api.OpenMaya as om

from dcc.python import stringutils
from dcc.maya.libs import dagutils, plugutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


ZERO_TOLERANCE = 1e-3


def numControlPoints(skinCluster):
    """
    Evaluates the number of control points this skin cluster affects.

    :type skinCluster: om.MObject
    :rtype: int
    """

    return om.MFnDependencyNode(skinCluster).findPlug('weightList', False).numElements()


def iterInfluences(skinCluster):
    """
    Returns a generator that yields all of the influence objects from the supplied skin cluster.

    :type skinCluster: om.MObject
    :rtype: iter
    """

    # Iterate through matrix elements
    #
    fnDependNode = om.MFnDependencyNode(skinCluster)

    plug = fnDependNode.findPlug('matrix', False)  # type: om.MPlug
    numElements = plug.evaluateNumElements()

    for i in range(numElements):

        # Get element by index
        #
        element = plug.elementByPhysicalIndex(i)
        index = element.logicalIndex()

        if not element.isConnected:

            log.debug('No connected joint found on %s.matrix[%s]!' % (fnDependNode.name(), index))
            continue

        # Get connected plug
        #
        otherPlug = element.source()
        otherNode = otherPlug.node()

        if not otherNode.isNull():

            yield index, otherNode

        else:

            log.debug('Null object found on %s.matrix[%s]!' % (fnDependNode.name(), index))
            continue


def iterWeights(skinCluster, vertexIndex, plug=None):
    """
    Return a generator that yields all of the weights for the specified vertex.
    The plug keyword is used for optimization purposes when yielding a list of vertices.

    :type skinCluster: om.MObject
    :type vertexIndex: int
    :type plug: om.MPlug
    :rtype: iter
    """

    # Check if plug was supplied
    #
    if plug is None:

        plug = plugutils.findPlug(skinCluster, 'weightList[%s].weights' % vertexIndex)

    # Iterate through plug elements
    #
    numElements = plug.numElements()

    for physicalIndex in range(numElements):

        element = plug.elementByPhysicalIndex(physicalIndex)
        influenceId = element.logicalIndex()
        influenceWeight = element.asFloat()

        yield influenceId, influenceWeight


def iterWeightList(skinCluster, vertexIndices=None):
    """
    Returns a generator that yields all the vertex weights from the supplied skin cluster.
    An optional list of vertex indices can be supplied to limit the generator.

    :type skinCluster: om.MObject
    :type vertexIndices: Union[List[int], tuple[int]]
    :rtype: iter
    """

    # Check number of vertices
    #
    if stringutils.isNullOrEmpty(vertexIndices):

        vertexIndices = list(range(numControlPoints(skinCluster)))

    # Iterate through arguments
    #
    weightListPlug = plugutils.findPlug(skinCluster, 'weightList')

    for vertexIndex in vertexIndices:

        # Go to weight list element
        #
        element = weightListPlug.elementByLogicalIndex(vertexIndex)

        # Yield vertex weights
        #
        weightsPlug = element.child(0)  # type: om.MPlug
        weights = dict(iterWeights(skinCluster, vertexIndex, plug=weightsPlug))

        yield vertexIndex, weights


def hasInfluence(skinCluster, influence):
    """
    Evaluates if the skin cluster has the supplied influence object.

    :type skinCluster: om.MObject
    :type influence: om.MObject
    :rtype: bool
    """

    # Get instance number of influence
    #
    dagPath = om.MDagPath.getAPathTo(influence)  # type: om.MDagPath
    instanceNumber = dagPath.instanceNumber()

    # Inspect world matrix plug connections
    #
    plug = plugutils.findPlug(influence, 'worldMatrix[%s]' % instanceNumber)
    otherPlugs = plug.destinations()

    return any([otherPlug.node() == skinCluster for otherPlug in otherPlugs])


def getInfluenceId(skinCluster, influence):
    """
    Returns the influence ID for the given influence object.

    :type skinCluster: om.MObject
    :type influence: om.MObject
    :rtype: int
    """

    # Get instance number of influence
    #
    dagPath = om.MDagPath.getAPathTo(influence)  # type: om.MDagPath
    instanceNumber = dagPath.instanceNumber()

    # Inspect world matrix plug connections
    #
    plug = plugutils.findPlug(influence, 'worldMatrix[%s]' % instanceNumber)
    otherPlugs = plug.destinations()

    for otherPlug in otherPlugs:

        otherNode = otherPlug.node()

        if otherNode == skinCluster:

            return otherPlug.logicalIndex()

        else:

            continue

    return None


def getInfluence(skinCluster, influenceId):
    """
    Returns the influence object at the specified index.

    :type skinCluster: om.MObject
    :type influenceId: int
    :rtype: om.MObject
    """

    plug = plugutils.findPlug(skinCluster, 'matrix[%s]' % influenceId)
    otherPlug = plug.source()  # type: om.MPlug

    if not otherPlug.isNull:

        return otherPlug.node()

    else:

        log.warning('Unable to locate influence at ID: %s' % influenceId)
        return None


def addInfluence(skinCluster, influence):
    """
    Adds the supplied influence object to the specified skin cluster.

    :type skinCluster: om.MObject
    :type influence: om.MObject
    :rtype: int
    """

    # Check if influence has already been added
    #
    index = getInfluenceId(skinCluster, influence)

    if index is not None:

        return index

    # Get first available index
    #
    fnDependNode = om.MFnDependencyNode(skinCluster)
    fnDagNode = om.MFnDagNode(influence)

    plug = fnDagNode.findPlug('matrix', False)
    index = plugutils.getNextAvailableConnection(plug)

    # Connect joint to skin cluster
    #
    fullPathName = fnDagNode.fullPathName()

    mc.connectAttr('%s.worldMatrix[0]' % fullPathName, '%s.matrix[%s]' % (fnDependNode.name(), index))
    mc.connectAttr('%s.objectColorRGB' % fullPathName, '%s.influenceColor[%s]' % (fnDependNode.name(), index))

    # Check if ".lockInfluenceWeights" attribute exists
    #
    if not mc.attributeQuery('lockInfluenceWeights', exists=True, node=fullPathName):

        # Add attribute to joint
        # NOTE: These settings were pulled from an ascii file
        #
        mc.addAttr(
            fullPathName,
            cachedInternally=True,
            shortName='liw',
            longName='lockInfluenceWeights',
            min=0,
            max=1,
            attributeType='bool'
        )

    # Connect custom attribute
    #
    mc.connectAttr('%s.lockInfluenceWeights' % fullPathName, '%s.lockWeights[%s]' % (fnDependNode.name(), index))

    # Set pre-bind matrix
    #
    matrixList = mc.getAttr('%s.worldInverseMatrix[0]' % fullPathName)
    mc.setAttr('%s.bindPreMatrix[%s]' % (fnDependNode.name(), index), matrixList, type='matrix')


def removeInfluence(skinCluster, influenceId):
    """
    Removes the specified influence.

    :type skinCluster: om.MObject
    :type influenceId: int
    :rtype: bool
    """

    # Get influence object
    #
    influence = getInfluence(skinCluster, influenceId)

    if influence is None:

        return False

    # Disconnect joint from skin cluster
    #
    fnDependNode = om.MFnDependencyNode(skinCluster)
    fnDagNode = om.MFnDagNode(influence)

    fullPathName = fnDagNode.fullPathName()

    mc.disconnectAttr('%s.worldMatrix[0]' % fullPathName, '%s.matrix[%s]' % (fnDependNode.name(), influenceId))
    mc.disconnectAttr('%s.objectColorRGB' % fullPathName, '%s.influenceColor[%s]' % (fnDependNode.name(), influenceId))
    mc.disconnectAttr('%s.lockInfluenceWeights' % fullPathName, '%s.lockWeights[%s]' % (fnDependNode.name(), influenceId))
    mc.deleteAttr('%s.lockInfluenceWeights' % fullPathName)

    return True


def selectInfluence(skinCluster, influenceId):
    """
    Selects the specified influence.

    :type skinCluster: om.MObject
    :type influenceId: int
    :rtype: None
    """

    # Get influence object
    #
    influence = getInfluence(skinCluster, influenceId)

    if influence is None:

        log.warning('Unable to select influence ID: %s' % influenceId)
        return

    # Connect plugs
    #
    source = plugutils.findPlug(influence, 'message')
    destination = plugutils.findPlug(skinCluster, 'paintTrans')

    plugutils.connectPlugs(source, destination, force=True)


def setWeights(skinCluster, vertexIndex, weights, plug=None):
    """
    Updates the weights for the specified vertex.
    The plug keyword is used for optimization purposes when updating a list of vertices.

    :type skinCluster: om.MObject
    :type vertexIndex: int
    :type weights: Dict[int, float]
    :type plug: om.MPlug
    :rtype: None
    """

    # Check if plug was supplied
    #
    fnDependNode = om.MFnDependencyNode(skinCluster)

    if plug is None:

        plug = plugutils.findPlug(skinCluster, 'weightList[%s].weights' % vertexIndex)

    # Remove unused influences
    #
    influenceIds = plug.getExistingArrayAttributeIndices()
    diff = list(set(influenceIds) - set(weights.keys()))

    for influenceId in diff:

        mc.removeMultiInstance(
            '{nodeName}.weightList[{vertexIndex}].weights[{influenceId}]'.format(
                nodeName=fnDependNode.absoluteName(),
                vertexIndex=vertexIndex,
                influenceId=influenceId
            )
        )

    # Iterate through new weights
    #
    for (influenceId, weight) in weights.items():

        # Check for zero weights
        # Be sure to remove these when encountered!
        #
        if weight <= ZERO_TOLERANCE:

            mc.removeMultiInstance(
                '{nodeName}.weightList[{vertexIndex}].weights[{influenceId}]'.format(
                    nodeName=fnDependNode.absoluteName(),
                    vertexIndex=vertexIndex,
                    influenceId=influenceId
                )
            )

        else:

            element = plug.elementByLogicalIndex(influenceId)  # type: om.MPlug
            element.setFloat(weight)


def setWeightList(skinCluster, weightList):
    """
    Updates the weights for all the specified vertices.

    :type skinCluster: om.MObject
    :type weightList: Dict[int, Dict[int, float]]
    :rtype: None
    """

    # Disable normalize weights
    #
    fnDependNode = om.MFnDependencyNode(skinCluster)

    normalizePlug = plugutils.findPlug('normalizeWeights')  # type: om.MPlug
    normalizePlug.setBool(False)

    # Iterate through vertices
    #
    weightListPlug = fnDependNode.findPlug('weightList', False)  # type: om.MPlug

    for (vertexIndex, weights) in weightList.items():

        # Get pre-existing influences
        #
        element = weightListPlug.elementByLogicalIndex(vertexIndex)
        weightsPlug = element.child(0)  # type: om.MPlug

        setWeights(skinCluster, vertexIndex, weights, plug=weightsPlug)

    # Re-enable normalize weights
    #
    normalizePlug.setBool(True)


def resetPreBindMatrices(skinCluster):
    """
    Resets the pre-bind matrices on the associated joints.

    :rtype: None
    """

    # Iterate through matrix elements
    #
    fnDependNode = om.MFnDependencyNode(skinCluster)

    plug = fnDependNode.findPlug('bindPreMatrix', False)
    numElements = plug.evaluateNumElements()

    for i in range(numElements):

        # Get inverse matrix of influence
        #
        element = plug.elementByPhysicalIndex(i)
        index = element.logicalIndex()

        attributeName = element.name()

        # Check if influence still exists
        #
        influence = getInfluence(skinCluster, index)

        if influence is None:

            continue

        # Get inverse matrix from influence-
        #
        fnDagNode = om.MFnDagNode(influence)

        matrixList = mc.getAttr('%s.worldInverseMatrix[0]' % fnDagNode.fullPathName())
        mc.setAttr(attributeName, matrixList, type='matrix')


def resetIntermediateObject(skinCluster):
    """
    Resets the control points on the associated intermediate object.

    :rtype: None
    """

    # Store deformed points
    #
    transform, shape, intermediateObject = dagutils.decomposeDeformer(skinCluster)

    shape = om.MDagPath.getAPathTo(shape)
    iterVertex = om.MItMeshVertex(shape)

    points = []

    while not iterVertex.isDone():

        point = iterVertex.position()
        points.append([point.x, point.y, point.z])

        iterVertex.next()

    # Reset influences
    #
    resetPreBindMatrices(skinCluster)

    # Apply deformed values to intermediate object
    #
    intermediateObject = om.MDagPath.getAPathTo(intermediateObject)
    iterVertex = om.MItMeshVertex(intermediateObject)

    while not iterVertex.isDone():

        point = points[iterVertex.index()]
        iterVertex.setPosition(om.MPoint(point))

        iterVertex.next()
