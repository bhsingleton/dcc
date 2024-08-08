from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.maya.libs import dagutils, plugutils, plugmutators
from dcc.maya.decorators import undo

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


def lockTransform(node):
    """
    Locks the transforms attributes on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Check if a shape was supplied
    #
    node = dagutils.getMObject(node)

    if node.hasFn(om.MFn.kShape):

        node = dagutils.getParent(node)

    # Lock transform attributes
    #
    for attribute in ('translate', 'rotate', 'scale'):

        plug = plugutils.findPlug(node, attribute)

        for childPlug in plugutils.iterChildren(plug):

            childPlug.isLocked = True

    # Disable inherits transform
    #
    plug = plugutils.findPlug(node, 'inheritsTransform')
    plugmutators.setValue(plug, False)


def clearIntermediateObjects(node):
    """
    Removes any intermediate objects from the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Check if a shape was supplied
    #
    node = dagutils.getMObject(node)

    if node.hasFn(om.MFn.kShape):

        node = dagutils.getParent(node)

    # Iterate through intermediate objects
    #
    intermediateObjects = list(dagutils.iterIntermediateObjects(node))

    for intermediateObject in intermediateObjects:

        log.info(f'Removing intermediate object: {dagutils.getNodeName(intermediateObject)}')
        dagutils.deleteNode(intermediateObject)


def iterInfluences(skinCluster):
    """
    Returns a generator that yields all the influence objects from the supplied skin cluster.

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
    Returns a generator that yields the weights for the specified vertex.
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
    Returns a generator that yields the vertex weights from the supplied skin cluster.
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

    # Check if influence is valid
    #
    dagPath = dagutils.getMDagPath(influence)

    if not dagPath.isValid():

        return False

    # Inspect world-matrix plug for connection
    #
    instanceNumber = dagPath.instanceNumber()

    plug = plugutils.findPlug(dagPath.node(), f'worldMatrix[{instanceNumber}]')
    otherPlugs = plug.destinations()

    return any([otherPlug.node() == skinCluster for otherPlug in otherPlugs])


def getInfluenceId(skinCluster, influence):
    """
    Returns the influence ID for the given influence object.

    :type skinCluster: om.MObject
    :type influence: om.MObject
    :rtype: int
    """

    # Check if influence is valid
    #
    dagPath = dagutils.getMDagPath(influence)

    if not dagPath.isValid():

        return None

    # Inspect world matrix plug connections
    #
    instanceNumber = dagPath.instanceNumber()
    plug = plugutils.findPlug(dagPath.node(), f'worldMatrix[{instanceNumber}]')

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

    plug = plugutils.findPlug(skinCluster, f'matrix[{influenceId}]')
    otherPlug = plug.source()  # type: om.MPlug

    if not otherPlug.isNull:

        return otherPlug.node()

    else:

        log.warning(f'Unable to locate influence at ID: {influenceId}')
        return None


@undo.Undo(name='Add Influence')
def addInfluence(skinCluster, influence, index=None):
    """
    Adds the supplied influence object to the specified skin cluster.

    :type skinCluster: om.MObject
    :type influence: om.MObject
    :type index: int
    :rtype: int
    """

    # Check if influence has already been added
    #
    if hasInfluence(skinCluster, influence):

        return getInfluenceId(skinCluster, influence)

    # Get first available index
    #
    fnSkinCluster = om.MFnDependencyNode(skinCluster)
    skinClusterName = fnSkinCluster.absoluteName()

    plug = fnSkinCluster.findPlug('matrix', False)

    if index is None:

        index = plugutils.getNextAvailableConnection(plug)

    # Connect joint to skin cluster
    #
    dagPath = dagutils.getMDagPath(influence)
    fnInfluence = om.MFnDagNode(dagPath)
    influenceName = fnInfluence.fullPathName()
    instanceNumber = dagPath.instanceNumber()

    mc.connectAttr(f'{influenceName}.worldMatrix[{instanceNumber}]', f'{skinClusterName}.matrix[{index}]')
    mc.connectAttr(f'{influenceName}.objectColorRGB', f'{skinClusterName}.influenceColor[{index}]')

    # Check if ".lockInfluenceWeights" attribute exists
    #
    if not mc.attributeQuery('lockInfluenceWeights', exists=True, node=influenceName):

        # Add attribute to joint
        # NOTE: These settings were pulled from an ascii file
        #
        mc.addAttr(
            influenceName,
            cachedInternally=True,
            shortName='liw',
            longName='lockInfluenceWeights',
            min=0,
            max=1,
            attributeType='bool'
        )

    # Connect custom attribute
    #
    mc.connectAttr(f'{influenceName}.lockInfluenceWeights', f'{skinClusterName}.lockWeights[{index}]')

    # Set pre-bind matrix
    #
    matrixList = mc.getAttr(f'{influenceName}.worldInverseMatrix[{instanceNumber}]')
    mc.setAttr(f'{skinClusterName}.bindPreMatrix[{index}]', matrixList, type='matrix')


@undo.Undo(name='Remove Influence')
def removeInfluence(skinCluster, influenceId):
    """
    Removes the specified influence.

    :type skinCluster: om.MObject
    :type influenceId: int
    :rtype: bool
    """

    # Get associated influence object
    #
    influence = getInfluence(skinCluster, influenceId)

    if influence is None:

        return False

    # Get influence name and instance number
    #
    fnSkinCluster = om.MFnDependencyNode(skinCluster)
    skinClusterName = fnSkinCluster.absoluteName()

    influencePath = dagutils.getMDagPath(influence)
    influenceName = influencePath.fullPathName()
    instanceNumber = influencePath.instanceNumber()

    # Disconnect `matrix` attribute
    #
    source = f'{influenceName}.worldMatrix[{instanceNumber}]'
    destination = f'{skinClusterName}.matrix[{influenceId}]'

    if mc.isConnected(source, destination):

        mc.disconnectAttr(source, destination)

    # Disconnect `influenceColor` attribute
    #
    source = f'{influenceName}.objectColorRGB'
    destination = f'{skinClusterName}.influenceColor[{influenceId}]'

    if mc.isConnected(source, destination):

        mc.disconnectAttr(source, destination)

    # Disconnect `lockWeights` attribute
    #
    source = f'{influenceName}.lockInfluenceWeights'
    destination = f'{skinClusterName}.lockWeights[{influenceId}]'

    if mc.isConnected(source, destination):

        mc.disconnectAttr(source, destination)

    # Delete `lockInfluenceWeights` attribute
    #
    if mc.attributeQuery('lockInfluenceWeights', node=influenceName, exists=True):

        mc.deleteAttr(f'{influenceName}.lockInfluenceWeights')

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


def setWeights(skinCluster, vertexIndex, weights, plug=None, modifier=None):
    """
    Updates the weights for the specified vertex.
    The plug keyword is used for optimization purposes when updating a list of vertices.

    :type skinCluster: om.MObject
    :type vertexIndex: int
    :type weights: Dict[int, float]
    :type plug: om.MPlug
    :type modifier: Union[om.MDGModifier, None]
    :rtype: None
    """

    # Check if plug was supplied
    #
    fnDependNode = om.MFnDependencyNode(skinCluster)

    if plug is None:

        plug = plugutils.findPlug(skinCluster, 'weightList[%s].weights' % vertexIndex)

    # Check if a dag modifier was supplied
    #
    if modifier is None:

        modifier = om.MDGModifier()

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
            plugmutators.setFloat(element, weight, modifier=modifier)

    # Cache and execute modifier
    #
    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()


@undo.Undo(name='Set Skin Weights')
def setWeightList(skinCluster, weightList, modifier=None):
    """
    Updates the weights for all the specified vertices.

    :type skinCluster: om.MObject
    :type weightList: Dict[int, Dict[int, float]]
    :type modifier: Union[om.MDGModifier, None]
    :rtype: None
    """

    # Disable normalize weights
    #
    normalizePlug = plugutils.findPlug(skinCluster, 'normalizeWeights')  # type: om.MPlug
    normalizePlug.setBool(False)

    # Iterate through vertices
    #
    weightListPlug = plugutils.findPlug(skinCluster, 'weightList')  # type: om.MPlug

    for (vertexIndex, weights) in weightList.items():

        # Get pre-existing influences
        #
        element = weightListPlug.elementByLogicalIndex(vertexIndex)
        weightsPlug = element.child(0)  # type: om.MPlug

        setWeights(skinCluster, vertexIndex, weights, plug=weightsPlug, modifier=modifier)

    # Re-enable normalize weights
    #
    normalizePlug.setBool(True)


def getPreBindMatrix(skinCluster, influenceId):
    """
    Returns the pre-bind matrix for the specified influence ID.

    :type skinCluster: om.MMObject
    :type influenceId: int
    :rtype: om.MMatrix
    """

    plug = plugutils.findPlug(skinCluster, 'bindPreMatrix')
    element = plug.elementByLogicalIndex(influenceId)

    return plugmutators.getValue(element)


@undo.Undo(name='Reset Pre-Bind Matrices')
def resetPreBindMatrices(skinCluster, modifier=None):
    """
    Resets the pre-bind matrices on the associated joints.

    :type skinCluster: om.MObject
    :type modifier: Union[om.MDGModifier, None]
    :rtype: None
    """

    # Check if a modifier was supplied
    #
    if modifier is None:

        modifier = om.MDGModifier()

    # Iterate through matrix elements
    #
    plug = plugutils.findPlug(skinCluster, 'bindPreMatrix')
    numElements = plug.evaluateNumElements()

    for i in range(numElements):

        # Get inverse matrix of influence
        #
        element = plug.elementByPhysicalIndex(i)
        index = element.logicalIndex()

        # Check if influence still exists
        #
        influence = getInfluence(skinCluster, index)

        if influence is None:

            continue

        # Get world inverse matrix from influence
        #
        dagPath = om.MDagPath.getAPathTo(influence)
        worldInverseMatrixPlug = plugutils.findPlug(influence, 'worldInverseMatrix[%s]' % dagPath.instanceNumber())
        worldInverseMatrix = plugmutators.getMatrix(worldInverseMatrixPlug)

        plugmutators.setMatrix(element, worldInverseMatrix, modifier=modifier)

    # Cache and execute modifier
    #
    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()


@undo.Undo(name='Reset Intermediate Object')
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
