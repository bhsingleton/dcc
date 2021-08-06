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

        try:

            # Locate skin cluster
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

        except TypeError as exception:

            log.error(exception)
            return

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

    def iterControlPoints(self, *args):
        """
        Returns the control points from the intermediate object.

        :rtype: list
        """

        # Evaluate arguments
        #
        vertexIndices = args
        numVertexIndices = len(vertexIndices)

        if numVertexIndices == 1:

            vertexIndices = range(self.numControlPoints())

        # Initialize vertex iterator
        #
        intermediateObject = self.intermediateObject()
        iterVertices = om.MItMeshVertex(intermediateObject)

        for vertexIndex in vertexIndices:

            iterVertices.setIndex(vertexIndex)
            point = iterVertices.position()

            yield point.x, point.y, point.z

    def numControlPoints(self):
        """
        Evaluates the number of control points for this deformer.

        :rtype: int
        """

        intermediateObject = self.intermediateObject()
        fnMesh = om.MFnMesh(intermediateObject)

        return fnMesh.numVertices

    def iterInfluences(self):
        """
        Returns a generator that yields all of the influence object from this deformer.

        :rtype: iter
        """

        # Iterate through matrix elements
        #
        fnDependNode = om.MFnDependencyNode(self.object())

        plug = fnDependNode.findPlug('matrix')  # type: om.MPlug
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

    @property
    def maxInfluences(self):
        """
        Getter method that returns the max number of influences for this deformer.

        :rtype: int
        """

        fnDependNode = om.MFnDependencyNode(self.object())
        return fnDependNode.findPlug('maxInfluences').asFloat()

    def iterWeights(self, *args):
        """
        Returns a generator that yields skin weights.
        If no vertex indices are supplied then all of the skin weights should be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        vertexIndices = args
        numArgs = len(vertexIndices)

        if numArgs == 0:

            vertexIndices = range(self.numControlPoints())

        # Iterate through vertices
        #
        fnDependNode = om.MFnDependencyNode(self.object())
        weightListPlug = fnDependNode.findPlug('weightList')  # type: om.MPlug

        for vertexIndex in vertexIndices:

            # Go to plug element
            #
            weightListPlug.selectAncestorLogicalIndex(vertexIndex)

            # Access child element
            #
            weightsPlug = weightListPlug.child(0)  # type: om.MPlug
            numElements = weightsPlug.evaluateNumElements()

            vertexWeights = {}

            for physicalIndex in range(numElements):

                element = weightsPlug.elementByPhysicalIndex(physicalIndex)
                vertexWeights[element.logicalIndex()] = element.asFloat()

            yield vertexIndex, vertexWeights
