import maya.cmds as mc
import maya.api.OpenMaya as om

from . import fnnode
from .libs import dagutils, plugutils
from .decorators import undo
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
    __loaded__ = mc.pluginInfo('TransferPaintWeightsCmd', query=True, loaded=True)
    __colorsetname__ = 'paintWeightsColorSet1'
    __colorramp__ = '1,0,0,1,1,1,0.5,0,0.8,1,1,1,0,0.6,1,0,1,0,0.4,1,0,0,1,0,1'

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

        # Call parent method
        #
        skinCluster = dagutils.findDeformerByType(obj, om.MFn.kSkinClusterFilter)
        super(FnSkin, self).setObject(skinCluster)

        # Store references to skin cluster components
        #
        transform, shape, intermediateObject = dagutils.decomposeDeformer(skinCluster)

        self._transform = om.MObjectHandle(transform)
        self._shape = om.MObjectHandle(shape)
        self._intermediateObject = om.MObjectHandle(intermediateObject)

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

            args = list(range(self.numControlPoints()))

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

            if fnComponent.hasWeights:

                yield element, fnComponent.weight(i)

            else:

                yield element, 1.0

    @classmethod
    def isPluginLoaded(cls):
        """
        Evaluates if the plugin for color display is loaded.

        :rtype: bool
        """

        return cls.__loaded__

    def showColors(self):
        """
        Enables color feedback for the associated shape.

        :rtype: None
        """

        # Check if plugin is loaded
        #
        if not self.isPluginLoaded():

            log.debug('showColors() requires the TransferPaintWeightsCmd.mll plugin!')
            return

        # Check if this instance supports vertex colours
        #
        shape = self.shape()

        if not shape.hasFn(om.MFn.kMesh):

            log.debug('showColors() expects a mesh (%s given)!' % shape.apiTypeStr)
            return

        # Check if intermediate object has colour set
        #
        intermediateObject = self.intermediateObject()

        fnMesh = om.MFnMesh(intermediateObject)
        colorSetNames = fnMesh.getColorSetNames()

        if self.__colorsetname__ not in colorSetNames:

            fnMesh.createColorSet(self.__colorsetname__, False)
            fnMesh.setCurrentColorSetName(self.__colorsetname__)

        # Set shape attributes
        #
        fnMesh.setObject(shape)
        fullPathName = fnMesh.fullPathName()

        mc.setAttr('%s.displayImmediate' % fullPathName, 0)
        mc.setAttr('%s.displayVertices' % fullPathName, 0)
        mc.setAttr('%s.displayEdges' % fullPathName, 0)
        mc.setAttr('%s.displayBorders' % fullPathName, 0)
        mc.setAttr('%s.displayCenter' % fullPathName, 0)
        mc.setAttr('%s.displayTriangles' % fullPathName, 0)
        mc.setAttr('%s.displayUVs' % fullPathName, 0)
        mc.setAttr('%s.displayNonPlanar' % fullPathName, 0)
        mc.setAttr('%s.displayInvisibleFaces' % fullPathName, 0)
        mc.setAttr('%s.displayColors' % fullPathName, 1)
        mc.setAttr('%s.vertexColorSource' % fullPathName, 1)
        mc.setAttr('%s.materialBlend' % fullPathName, 0)
        mc.setAttr('%s.displayNormal' % fullPathName, 0)
        mc.setAttr('%s.displayTangent' % fullPathName, 0)
        mc.setAttr('%s.currentColorSet' % fullPathName, '', type='string')

    def hideColors(self):
        """
        Disable color feedback for the associated shape.

        :rtype: None
        """

        # Check if plugin is loaded
        #
        if not self.isPluginLoaded():

            log.debug('hideColors() requires the TransferPaintWeightsCmd.mll plugin!')
            return

        # Check if this instance supports vertex colours
        #
        shape = self.shape()

        if not shape.hasFn(om.MFn.kMesh):

            log.debug('hideColors() expects a mesh (%s given)!' % shape.apiTypeStr)
            return

        # Reset shape attributes
        #
        fnMesh = om.MFnMesh(shape)
        fullPathName = fnMesh.fullPathName()

        mc.setAttr('%s.displayColors' % fullPathName, 0)
        mc.setAttr('%s.vertexColorSource' % fullPathName, 1)

        # Delete color set
        #
        intermediateObject = self.intermediateObject()

        fnMesh.setObject(intermediateObject)
        colorSetNames = fnMesh.getColorSetNames()

        if self.__colorsetname__ in colorSetNames:

            fnMesh.deleteColorSet(self.__colorsetname__)

    def invalidateColors(self):
        """
        Forces the vertex colour display to redraw.

        :rtype: None
        """

        # Check if plugin is loaded
        #
        if not self.isPluginLoaded():

            log.debug('invalidateColors() requires the TransferPaintWeightsCmd.mll plugin!')
            return

        # Check if this instance belongs to a mesh
        #
        intermediateObject = self.intermediateObject()

        if not intermediateObject.hasFn(om.MFn.kMesh):

            log.debug('invalidateColors() expects a mesh (%s given)!' % intermediateObject.apiTypeStr)
            return

        # Check if colour set is active
        #
        fnMesh = om.MFnMesh(intermediateObject)

        if fnMesh.currentColorSetName() == self.__colorsetname__:

            mc.dgdirty('%s.paintTrans' % self.name())

            mc.transferPaintWeights(
                '%s.paintWeights' % self.name(),
                fnMesh.fullPathName(),
                colorRamp=self.__colorramp__
            )

    def iterInfluences(self):
        """
        Returns a generator that yields all of the influence objects from this skin.

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
        Returns the number of influences being use by this skin.

        :rtype: int
        """

        return om.MFnDependencyNode(self.object()).findPlug('matrix', False).numConnectedElements()

    def maxInfluences(self):
        """
        Getter method that returns the max number of influences for this skin.

        :rtype: int
        """

        return om.MFnDependencyNode(self.object()).findPlug('maxInfluences', False).asFloat()

    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        # Get source plug
        #
        influences = self.influences()
        influence = influences[influenceId]

        source = plugutils.findPlug(influence, 'message')

        # Get destination plug
        #
        deformer = self.object()
        destination = plugutils.findPlug(deformer, 'paintTrans')

        # Connect plugs
        #
        plugutils.connectPlugs(source, destination, force=True)

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
        index = plugutils.getNextAvailableConnection(plug)

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

    def iterVertexWeights(self, *args):
        """
        Returns a generator that yields weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are yielded instead.

        :rtype: iter
        """

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = range(self.numControlPoints())

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

    def applyVertexWeights(self, vertices):
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

        # Start undo chunk
        #
        with undo.Undo(name='Apply Vertex Weights') as chunk:

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
                        '{nodeName}.weightList[{vertexIndex}].weights[{influenceId}]'.format(
                            nodeName=fnDependNode.absoluteName(),
                            vertexIndex=vertexIndex,
                            influenceId=influenceId
                        )
                    )

                # Iterate through new weights
                #
                for (influenceId, weight) in vertexWeights.items():

                    # Check for zero weights
                    # Be sure to remove these if encountered!
                    #
                    if self.isClose(0.0, weight):

                        mc.removeMultiInstance(
                            '{nodeName}.weightList[{vertexIndex}].weights[{influenceId}]'.format(
                                nodeName=fnDependNode.absoluteName(),
                                vertexIndex=vertexIndex,
                                influenceId=influenceId
                            )
                        )

                    else:

                        element = weightsPlug.elementByLogicalIndex(influenceId)  # type: om.MPlug
                        element.setFloat(weight)

        # Enable normalize weights
        #
        normalizePlug.setBool(True)

    @undo.undo(name='Reset Pre-Bind Matrices')
    def resetPreBindMatrices(self):
        """
        Resets the pre-bind matrices on the associated joints.

        :rtype: None
        """

        # Iterate through matrix elements
        #
        skinCluster = self.object()
        fnDependNode = om.MFnDependencyNode(skinCluster)

        plug = fnDependNode.findPlug('bindPreMatrix')
        numElements = plug.evaluateNumElements()

        for i in range(numElements):

            # Get inverse matrix of influence
            #
            element = plug.elementByPhysicalIndex(i)
            index = element.logicalIndex()

            attributeName = element.name()

            # Check if influence still exists
            #
            influence = self._influences[index]

            if influence is None:
                continue

            # Get inverse matrix from influence-
            #
            matrixList = mc.getAttr('%s.worldInverseMatrix[0]' % influence.fullPathName())
            mc.setAttr(attributeName, matrixList, type='matrix')

    @undo.undo(name='Reset Intermediate Object')
    def resetIntermediateObject(self):
        """
        Resets the control points on the associated intermediate object.

        :rtype: None
        """

        # Store deformed points
        #
        shape = om.MDagPath.getAPathTo(self.shape())
        iterVertex = om.MItMeshVertex(shape)

        points = []

        while not iterVertex.isDone():

            point = iterVertex.position()
            points.append([point.x, point.y, point.z])

            iterVertex.next()

        # Reset influences
        #
        self.resetPreBindMatrices()

        # Apply deformed values to intermediate object
        #
        intermediateObject = om.MDagPath.getAPathTo(self.intermediateObject())
        iterVertex = om.MItMeshVertex(intermediateObject)

        while not iterVertex.isDone():

            point = points[iterVertex.index()]
            iterVertex.setPosition(om.MPoint(point))

            iterVertex.next()
