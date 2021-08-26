import maya.cmds as mc
import maya.api.OpenMaya as om

from . import fnnode
from .decorators.undo import undo
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

    def iterControlPoints(self, *args):
        """
        Returns a generator that yields all control points.
        Overloading for performance concerns.

        :rtype: iter
        """

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = list(self.range(self.numControlPoints()))

        # Create component
        #
        fnComponent = om.MFnSingleIndexedComponent()
        component = fnComponent.create(om.MFn.kMeshVertComponent)

        fnComponent.addElements(args)

        # Initialize iterator
        #
        intermediateObject = self.intermediateObject()
        dagPath = om.MDagPath.getAPathTo(intermediateObject)

        iterVertices = om.MItMeshVertex(dagPath, component)

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

    def componentSelection(self):
        """
        Returns the component selection for the associated shape.

        :rtype: om.MObject
        """

        # Collect components
        #
        shape = self.shape()

        components = [component for (dagPath, component) in self.iterActiveComponentSelection() if dagPath.node() == shape]
        numComponents = len(components)

        if numComponents == 1:

            return components[0]

        else:

            return om.MObject.kNullObj

    def iterSelection(self, includeWeight=False):
        """
        Returns the selected vertex elements.

        :type includeWeight: bool
        :rtype: list[int]
        """

        # Inspect component selection
        #
        component = self.componentSelection()

        if not component.hasFn(om.MFn.kMeshVertComponent):

            return

        # Iterate through component
        #
        fnComponent = om.MFnSingleIndexedComponent(component)

        for i in range(fnComponent.elementCount):

            yield fnComponent.element(i)

    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: list[int]
        :rtype: None
        """

        # Get dag path to object
        #
        dagPath = om.MDagPath.getAPathTo(self.shape())

        # Create mesh component
        #
        fnComponent = om.MFnSingleIndexedComponent()
        component = fnComponent.create(om.MFn.kMeshVertComponent)

        fnComponent.addElements(vertices)

        # Update selection list
        #
        selection = om.MSelectionList()
        selection.add((dagPath, component))

        om.MGlobal.setActiveSelectionList(selection)

    def iterSoftSelection(self):
        """
        Returns a generator that yields selected vertex and soft value pairs.

        :rtype iter
        """

        # Inspect component selection
        #
        component = self.componentSelection()

        if not component.hasFn(om.MFn.kMeshVertComponent):

            return

        # Iterate through component
        #
        fnComponent = om.MFnSingleIndexedComponent(component)

        for i in range(fnComponent.elementCount):

            element = fnComponent.element(i)
            hasWeight = fnComponent.hasWeights(i)

            if hasWeight:

                yield element, fnComponent.weight(i)

            else:

                yield element, 1.0

    def getConnectedVertices(self, *args):
        """
        Returns a list of vertices connected to the supplied verts.

        :rtype: list[int]
        """

        # Get dag path to intermediate object
        #
        intermediateObject = self.intermediateObject()
        dagPath = om.MDagPath.getAPathTo(intermediateObject)

        # Create mesh vertex component
        #
        fnComponent = om.MFnSingleIndexedComponent()
        component = fnComponent.create(om.MFn.kMeshVertComponent)

        fnComponent.addElements(args)

        # Initialize mesh vertex iterator
        #
        iterVertices = om.MItMeshVertex(dagPath, component)
        connectedVertices = set()

        while not iterVertices.isDone():

            connectedVertices.update(set(iterVertices.getConnectedVertices()))
            iterVertices.next()

        return list(connectedVertices)

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

    def iterWeights(self, *args):
        """
        Returns a generator that yields weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are yielded instead.

        :rtype: iter
        """

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = self.range(self.numControlPoints())

        # Iterate through arguments
        #
        fnDependNode = om.MFnDependencyNode(self.object())
        weightListPlug = fnDependNode.findPlug('weightList', False)  # type: om.MPlug

        for arg in args:

            # Go to weight list element
            #
            weightListPlug.selectAncestorLogicalIndex(arg)

            # Iterate through weight elements
            #
            weightsPlug = weightListPlug.child(0)  # type: om.MPlug
            numElements = weightsPlug.numElements()

            vertexWeights = {}

            for physicalIndex in range(numElements):

                element = weightsPlug.elementByPhysicalIndex(physicalIndex)

                influenceId = element.logicalIndex()
                influenceWeight = element.asFloat()

                vertexWeights[influenceId] = influenceWeight

            # Yield vertex weights
            #
            yield arg, vertexWeights

    @undo
    def applyWeights(self, vertices):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertices: dict[int:dict[int:float]]
        :rtype: None
        """

        # Disable normalize weights
        #
        fnDependNode = om.MFnDependencyNode(self.object())

        normalizePlug = fnDependNode.findPlug('normalizeWeights', False)  # type: om.MPlug
        normalizePlug.setBool(False)

        # Iterate through vertices
        #
        weightListPlug = fnDependNode.findPlug('weightList', False)  # type: om.MPlug

        for (vertexIndex, vertexWeights) in vertices.items():

            # Get pre-existing influences
            #
            weightListPlug.selectAncestorLogicalIndex(vertexIndex)

            weightsPlug = weightListPlug.child(0)  # type: om.MPlug
            influenceIds = weightsPlug.getExistingArrayAttributeIndices()

            # Remove unused influences
            #
            diff = list(set(influenceIds) - set(vertexWeights.keys()))

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
            for (influenceId, weight) in vertexWeights.items():

                element = weightsPlug.elementByLogicalIndex(influenceId)  # type: om.MPlug
                element.setFloat(weight)

        # Enable normalize weights and close undo chunk
        #
        normalizePlug.setBool(True)
