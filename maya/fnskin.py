import maya.cmds as mc
import maya.api.OpenMaya as om

from . import fnnode
from ..abstract import afnskin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSkin(afnskin.AFnSkin, fnnode.FnNode):
    """
    Overload of AFnSkin that outlines function set behaviour for skin weighting in Maya.
    This class also inherits from FnNode since skin clusters are node objects.
    """

    __slots__ = ('_transform', '_shape', '_intermediateObject')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Declare class variables
        #
        self._transform = om.MObjectHandle()
        self._shape = om.MObjectHandle()
        self._intermediateObject = om.MObjectHandle()

        # Call parent method
        #
        super(FnSkin, self).__init__(*args, **kwargs)

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, om.MObject, om.MDagPath]
        :rtype: None
        """

        # Locate skin cluster from object
        #
        obj = self.getMObject(obj)
        skinCluster = self.findSkinCluster(obj)

        super(FnSkin, self).setObject(skinCluster)

        # Store references to skin cluster components
        #
        transform, shape, intermediateObject = self.decomposeSkinCluster(skinCluster)

        self._transform = om.MObjectHandle(transform)
        self._shape = om.MObjectHandle(shape)
        self._intermediateObject = om.MObjectHandle(intermediateObject)

    @classmethod
    def findSkinCluster(cls, obj):
        """
        Finds the skin cluster from the given object.

        :type obj: om.MObject
        :rtype: om.MObject
        """

        # Check for null object
        #
        if obj.isNull():

            return

        # Check object type
        #
        if obj.hasFn(om.MFn.kSkinClusterFilter):

            return obj

        elif obj.hasFn(om.MFn.kTransform):

            # Evaluate the shapes derived from this transform
            #
            fnNode = fnnode.FnNode(obj)

            shapes = fnNode.shapes()
            numShapes = len(shapes)

            if numShapes == 0:

                return None

            elif numShapes == 1:

                return cls.findSkinCluster(shapes[0])

            else:

                raise TypeError('findSkinCluster() expects 1 shape node (%s given)!' % numShapes)

        elif obj.hasFn(om.MFn.kMesh):

            # Evaluate if this is an intermediate object
            #
            fnNode = fnnode.FnNode(obj)
            skinClusters = None

            if fnNode.isIntermediateObject:

                skinClusters = fnNode.dependents(om.MFn.kSkinClusterFilter)

            else:

                skinClusters = fnNode.dependsOn(om.MFn.kSkinClusterFilter)

            # Evaluate found skin clusters
            #
            numSkinClusters = len(skinClusters)

            if numSkinClusters == 0:

                return None

            elif numSkinClusters == 1:

                return skinClusters[0]

            else:

                raise TypeError('findSkinCluster() expects 1 skin cluster (%s given)!' % numSkinClusters)

        else:

            raise TypeError('findSkinCluster() expects a transform or shape (%s given)!' % obj.apiTypeStr)

    @classmethod
    def decomposeSkinCluster(cls, skinCluster):
        """
        Returns the transform, shape and intermediate object components that make up a skin cluster.

        :type skinCluster: om.MObject
        :rtype: om.MObject, om.MObject, om.MObject
        """

        # Locate shape nodes downstream
        #
        fnNode = fnnode.FnNode(skinCluster)
        transform, shape, intermediateObject = None, None, None

        shapes = fnNode.dependents(om.MFn.kShape)
        numShapes = len(shapes)

        if numShapes == 1:

            shape = shapes[0]

        else:

            raise TypeError('decomposeSkinCluster() expects 1 shape node (%s found)!' % numShapes)

        # Locate transform from shape node
        #
        transform = om.MFnDagNode(shape).parent(0)

        # Locate intermediate objects upstream
        #
        intermediateObjects = fnNode.dependsOn(om.MFn.kShape)
        numIntermediateObjects = len(intermediateObjects)

        if numIntermediateObjects == 1:

            intermediateObject = intermediateObjects[0]

        else:

            raise TypeError('decomposeSkinCluster() expects 1 intermediate object (%s found)!' % numIntermediateObjects)

        return transform, shape, intermediateObject

    def transform(self):
        """
        Returns the transform component of this deformer.

        :rtype: om.MObject
        """

        return self._transform.object()

    def shape(self):
        """
        Returns the shape component of this deformer.

        :rtype: om.MObject
        """

        return self._shape.object()

    def intermediateObject(self):
        """
        Returns the intermediate object of this deformer.

        :rtype: om.MObject
        """

        return self._intermediateObject.object()

    def iterVertices(self):
        """
        Returns a generator that yields all vertex indices.

        :rtype: iter
        """

        return range(self.numControlPoints())

    def controlPoint(self, vertexIndex):
        """
        Returns the control points from the intermediate object.

        :type vertexIndex: int
        :rtype: list[float, float, float]
        """

        intermediateObject = self.intermediateObject()

        fnMesh = om.MFnMesh(intermediateObject)
        point = fnMesh.getPoint(vertexIndex)

        return point.x, point.y, point.z

    def iterControlPoints(self):
        """
        Returns a generator that yields all control points.
        Overloading for performance concerns.

        :rtype: iter
        """

        intermediateObject = self.intermediateObject()
        iterVertices = om.MItMeshVertex(intermediateObject)

        while not iterVertices.isDone():

            point = iterVertices.position()
            yield point.x, point.y, point.z

            iterVertices.next()

    def numControlPoints(self):
        """
        Evaluates the number of control points for this deformer.

        :rtype: int
        """

        intermediateObject = self.intermediateObject()
        fnMesh = om.MFnMesh(intermediateObject)

        return fnMesh.numVertices

    def iterSelection(self):
        """
        Returns the selected vertex elements.

        :rtype: list[int]
        """

        # Inspect active selection
        #
        selection = om.MGlobal.getActiveSelectionList()  # type: om.MSelectionList
        selectionCount = selection.length()

        shape = self.shape()
        fnComponent = om.MFnSingleIndexedComponent()

        for i in range(selectionCount):

            # Check if this is self
            #
            dagPath, component = selection.getComponent(i)

            if dagPath.node() != shape or not component.hasFn(om.MFn.kMeshVertComponent):

                continue

            # Yield component elements
            #
            fnComponent.setObject(component)

            for j in range(fnComponent.elementCount):

                yield fnComponent.element(j)

            break

    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: list[int]
        :rtype: None
        """

        pass

    def showColors(self):
        """
        Enables color feedback for the associated shape.

        :rtype: None
        """

        pass

    def hideColors(self):
        """
        Disable color feedback for the associated shape.

        :rtype: None
        """

        pass

    def iterInfluences(self):
        """
        Returns a generator that yields all of the influence object from this deformer.

        :rtype: iter
        """

        # Iterate through matrix elements
        #
        fnDependNode = om.MFnDependencyNode(self.object())

        plug = fnDependNode.findPlug('matrix', False)  # type: om.MPlug
        numElements = plug.evaluateNumElements()

        for i in range(numElements):

            # Get element by index
            #
            element = plug.elementByPhysicalIndex(i)
            index = element.logicalIndex()

            if not element.isConnected:

                log.debug('No connected joint found on .matrix[%s]!' % index)
                continue

            # Get connected plug
            #
            otherPlug = element.source()
            otherNode = otherPlug.node()

            if not otherNode.isNull():

                yield index, otherNode

            else:

                log.debug('Null object found on .matrix[%s]!' % index)
                continue

    def numInfluences(self):
        """
        Returns the number of influences being use by this deformer.

        :rtype: int
        """

        return om.MFnDependencyNode(self.object()).findPlug('matrix', False).numConnectedElements()

    def maxInfluences(self):
        """
        Getter method that returns the max number of influences for this deformer.

        :rtype: int
        """

        return om.MFnDependencyNode(self.object()).findPlug('maxInfluences', False).asFloat()

    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        pass

    def addInfluence(self, influence):
        """
        Adds an influence to this deformer.

        :type influence: om.MObject
        :rtype: bool
        """

        # Check if influence is already in system
        #
        influences = self.influences()

        if influence in influences:

            return

        # Get first available index
        #
        fnDagNode = om.MFnDagNode(influence)

        plug = fnDagNode.findPlug('matrix', False)
        index = self.getNextAvailableElement(plug)

        # Connect joint to skin cluster
        #
        fullPathName = fnDagNode.fullPathName()

        mc.connectAttr('%s.worldMatrix[0]' % fullPathName, '%s.matrix[%s]' % (self.name(), index))
        mc.connectAttr('%s.objectColorRGB' % fullPathName, '%s.influenceColor[%s]' % (self.name(), index))

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

        else:

            log.debug('%s joint already has required attribute.' % fnDagNode.partialPathName())

        # Connect custom attribute
        #
        mc.connectAttr('%s.lockInfluenceWeights' % fullPathName, '%s.lockWeights[%s]' % (self.name(), index))

        # Set pre-bind matrix
        #
        matrixList = mc.getAttr('%s.worldInverseMatrix[0]' % fullPathName)
        mc.setAttr('%s.bindPreMatrix[%s]' % (self.name(), index), matrixList, type='matrix')

        # Add joint to influence list
        #
        influences[index] = influence

    def removeInfluence(self, influenceId):
        """
        Removes an influence from this deformer.

        :type influenceId: int
        :rtype: bool
        """

        # Check value type
        #
        if not isinstance(influenceId, int):

            raise TypeError('removeInfluence() expects an int (%s given)!' % type(influenceId).__name__)

        # Check if influence ID is defined
        #
        influences = self.influences()
        influence = influences[influenceId]

        if influence is None:

            log.warning('No influence could be found at ID: %s' % influenceId)
            return

        # Disconnect joint from skin cluster
        #
        fullPathName = influence.fullPathName()

        mc.disconnectAttr('%s.worldMatrix[0]' % fullPathName, '%s.matrix[%s]' % (self.name(), influenceId))
        mc.disconnectAttr('%s.objectColorRGB' % fullPathName, '%s.influenceColor[%s]' % (self.name(), influenceId))
        mc.disconnectAttr('%s.lockInfluenceWeights' % fullPathName, '%s.lockWeights[%s]' % (self.name(), influenceId))

        mc.deleteAttr('%s.lockInfluenceWeights' % fullPathName)

        # Remove joint from influence list
        #
        del influences[influenceId]

    def iterWeights(self, vertexIndex):
        """
        Returns a generator that yields skin weights.
        If no vertex indices are supplied then all of the skin weights should be yielded.

        :type vertexIndex: int
        :rtype: iter
        """

        # Get weight list plug
        #
        fnDependNode = om.MFnDependencyNode(self.object())

        weightListPlug = fnDependNode.findPlug('weightList', False)  # type: om.MPlug
        weightListPlug.selectAncestorLogicalIndex(vertexIndex)

        # Iterate through weight elements
        #
        weightsPlug = weightListPlug.child(0)  # type: om.MPlug
        numElements = weightsPlug.numElements()

        for physicalIndex in range(numElements):

            element = weightsPlug.elementByPhysicalIndex(physicalIndex)

            influenceId = element.logicalIndex()
            influenceWeight = element.asFloat()

            yield influenceId, influenceWeight

    def applyWeights(self, vertexIndex, weights):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertexIndex: int
        :type weights: dict[int:float]
        :rtype: None
        """

        # Initialize function set
        #
        fnDependNode = om.MFnDependencyNode(self.object())

        # Disable normalize weights
        #
        normalizePlug = fnDependNode.findPlug('normalizeWeights', False)  # type: om.MPlug
        normalizePlug.setBool(False)

        # Get weight list plug
        #
        weightListPlug = fnDependNode.findPlug('weightList', False)  # type: om.MPlug
        weightListPlug.selectAncestorLogicalIndex(vertexIndex)

        # Get pre-existing influences
        #
        weightsPlug = weightListPlug.child(0)  # type: om.MPlug
        influenceIds = weightsPlug.getExistingArrayAttributeIndices()

        # Remove unused influences
        #
        diff = list(set(influenceIds) - set(weights.keys()))

        for influenceId in diff:

            mc.removeMultiInstance(
                '{nodeName}.weightList[vertexIndex].weights[{influenceId}]'.format(
                    nodeName=fnDependNode.absoluteName(),
                    vertexIndex=vertexIndex,
                    influenceId=influenceId
                )
            )

        # Assign new weights
        #
        for (influenceId, weight) in weights.items():

            element = weightsPlug.elementByLogicalIndex(influenceId)  # type: om.MPlug
            element.setFloat(weight)

        # Enable normalize weights
        #
        normalizePlug.setBool(True)
