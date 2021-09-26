import maya.cmds as mc
import maya.api.OpenMaya as om

from dcc.abstract import afnskin
from dcc.maya import fnnode
from dcc.maya.libs import dagutils, skinutils
from dcc.maya.decorators import undo

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

    def isPartiallySelected(self):
        """
        Evaluates if this node is partially selected.
        Useful for things like deformers or modifiers.

        :rtype: bool
        """

        return self.isSelected() or self.shape() in self.getActiveSelection()

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

        return skinutils.iterInfluences(self.object())

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

        skinutils.selectInfluence(self.object(), influenceId)

    def addInfluence(self, influence):
        """
        Adds an influence to this deformer.

        :type influence: om.MObject
        :rtype: bool
        """

        index = skinutils.addInfluence(self.object(), influence)
        self.influences()[index] = influence

    def removeInfluence(self, influenceId):
        """
        Removes an influence from this deformer.

        :type influenceId: int
        :rtype: bool
        """

        skinutils.removeInfluence(self.object(), influenceId)
        del self.influences()[influenceId]

    def iterVertexWeights(self, *args):
        """
        Returns a generator that yields weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are yielded instead.

        :rtype: iter
        """

        return skinutils.iterWeightList(self.object(), vertexIndices=args)

    @undo.undo(name='Apply Vertex Weights')
    def applyVertexWeights(self, vertices):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertices: dict[int:dict[int:float]]
        :rtype: None
        """

        skinutils.setWeightList(self.object(), vertices)

    @undo.undo(name='Reset Pre-Bind Matrices')
    def resetPreBindMatrices(self):
        """
        Resets the pre-bind matrices on the associated joints.

        :rtype: None
        """

        skinutils.resetPreBindMatrices(self.object())

    @undo.undo(name='Reset Intermediate Object')
    def resetIntermediateObject(self):
        """
        Resets the control points on the associated intermediate object.

        :rtype: None
        """

        skinutils.resetIntermediateObject(self.object())
