from maya import cmds as mc
from maya.api import OpenMaya as om
from . import fnnode, fnmesh
from .libs import dagutils, plugutils, plugmutators, skinutils
from .decorators import undo
from ..abstract import afnskin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSkin(fnnode.FnNode, afnskin.AFnSkin):
    """
    Overload of `AFnSkin` that outlines function set behaviour for skin weighting in Maya.
    This class also inherits from FnNode since skin clusters are node objects.
    """

    # region Dunderscores
    __slots__ = ('_transform', '_shape', '_intermediateObject')
    __color_set_name__ = 'paintWeightsColorSet1'
    __color_ramp__ = '1,0,0,1,1,1,0.5,0,0.8,1,1,1,0,0.6,1,0,1,0,0.4,1,0,0,1,0,1'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare class variables
        #
        self._transform = om.MObjectHandle()
        self._shape = om.MObjectHandle()
        self._intermediateObject = om.MObjectHandle()

        # Call parent method
        #
        super(FnSkin, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    @classmethod
    def create(cls, mesh):
        """
        Creates a skin and assigns it to the supplied shape.

        :type mesh: om.MObject
        :rtype: FnSkin
        """

        skinutils.clearIntermediateObjects(mesh)
        skinutils.lockTransform(mesh)

        meshName = dagutils.getMDagPath(mesh).fullPathName()
        skinName = mc.deformer(meshName, type='skinCluster')[0]

        return cls(skinName)

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
        self._influences.clear()

    def transform(self):
        """
        Returns the transform node associated with this skin.

        :rtype: om.MObject
        """

        return self._transform.object()

    def shape(self):
        """
        Returns the shape node associated with this skin.

        :rtype: om.MObject
        """

        return self._shape.object()

    def intermediateObject(self):
        """
        Returns the intermediate object associated with this skin.

        :rtype: om.MObject
        """

        return self._intermediateObject.object()

    def iterVertices(self):
        """
        Returns a generator that yields vertex indices.

        :rtype: Iterator[int]
        """

        return range(self.numControlPoints())

    def component(self):
        """
        Returns the component selection for the associated shape.

        :rtype: om.MObject
        """

        # Collect components
        #
        shape = self.shape()

        components = [component for (dagPath, component) in dagutils.iterActiveComponentSelection() if dagPath.node() == shape]
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

        return self.isSelected() or self.shape() in self.scene.getActiveSelection()

    def iterSelection(self):
        """
        Returns a generator that yields the selected vertex elements.

        :rtype: Iterator[int]
        """

        # Inspect component selection
        #
        component = self.component()

        if not component.hasFn(om.MFn.kMeshVertComponent):

            return iter([])

        # Iterate through component
        #
        fnComponent = om.MFnSingleIndexedComponent(component)

        for i in range(fnComponent.elementCount):

            yield fnComponent.element(i)

    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: List[int]
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
        Returns a generator that yields selected vertex-weight pairs.

        :rtype Iterator[Dict[int, float]]
        """

        # Inspect component selection
        #
        component = self.component()

        if not component.hasFn(om.MFn.kMeshVertComponent):

            return iter([])

        # Iterate through component
        #
        fnComponent = om.MFnSingleIndexedComponent(component)

        for i in range(fnComponent.elementCount):

            # Check if element has weights
            #
            if fnComponent.hasWeights:

                yield fnComponent.element(i), fnComponent.weight(i).influence

            else:

                yield fnComponent.element(i), 1.0

    @classmethod
    def isPluginLoaded(cls):
        """
        Evaluates if the plugin for color display is loaded.

        :rtype: bool
        """

        return mc.pluginInfo('TransferPaintWeightsCmd', query=True, loaded=True)

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

            log.debug(f'showColors() expects a mesh ({shape.apiTypeStr} given)!')
            return

        # Check if intermediate object has required colour set
        # If not, then go ahead and create colour set!
        #
        intermediateObject = self.intermediateObject()

        fnIntermediateObject = om.MFnMesh(intermediateObject)
        colorSetNames = fnIntermediateObject.getColorSetNames()

        if self.__color_set_name__ not in colorSetNames:

            fnIntermediateObject.createColorSet(self.__color_set_name__, False)
            fnIntermediateObject.setCurrentColorSetName(self.__color_set_name__)

        # Set shape attributes
        #
        fnShape = om.MFnMesh(shape)
        shapePathName = fnShape.fullPathName()

        mc.setAttr(f'{shapePathName}.displayImmediate', 0)
        mc.setAttr(f'{shapePathName}.displayVertices', 0)
        mc.setAttr(f'{shapePathName}.displayEdges', 0)
        mc.setAttr(f'{shapePathName}.displayBorders', 0)
        mc.setAttr(f'{shapePathName}.displayCenter', 0)
        mc.setAttr(f'{shapePathName}.displayTriangles', 0)
        mc.setAttr(f'{shapePathName}.displayUVs', 0)
        mc.setAttr(f'{shapePathName}.displayNonPlanar', 0)
        mc.setAttr(f'{shapePathName}.displayInvisibleFaces', 0)
        mc.setAttr(f'{shapePathName}.displayColors', 1)
        mc.setAttr(f'{shapePathName}.displayColorChannel', 'None', type='string')
        mc.setAttr(f'{shapePathName}.vertexColorSource', 1)
        mc.setAttr(f'{shapePathName}.materialBlend', 0)
        mc.setAttr(f'{shapePathName}.displayNormal', 0)
        mc.setAttr(f'{shapePathName}.displayTangent', 0)
        mc.setAttr(f'{shapePathName}.currentColorSet', '', type='string')

    def hideColors(self):
        """
        Disable color feedback for the associated mesh.

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

            log.debug('hideColors() expects a mesh ({shape.apiTypeStr} given)!')
            return

        # Reset shape attributes
        #
        fnShape = om.MFnMesh(shape)
        shapePathName = fnShape.fullPathName()

        mc.setAttr(f'{shapePathName}.displayColors', 0)
        mc.setAttr(f'{shapePathName}.displayColorChannel', 'Ambient+Diffuse', type='string')
        mc.setAttr(f'{shapePathName}.vertexColorSource', 1)

        # Delete color set
        #
        intermediateObject = self.intermediateObject()
        fnIntermediateObject = om.MFnMesh(intermediateObject)

        intermediatePathName = fnShape.fullPathName()
        colorSetNames = fnIntermediateObject.getColorSetNames()

        if self.__color_set_name__ in colorSetNames:

            mc.setAttr(f'{intermediatePathName}.currentColorSet', '', type='string')
            fnIntermediateObject.deleteColorSet(self.__color_set_name__)

    def refreshColors(self):
        """
        Forces the vertex colour display to redraw.

        :rtype: None
        """

        # Check if plugin is loaded
        #
        if not self.isPluginLoaded():

            log.debug('invalidateColors() requires the "TransferPaintWeightsCmd" plugin!')
            return

        # Check if this instance belongs to a mesh
        #
        intermediateObject = self.intermediateObject()

        if not intermediateObject.hasFn(om.MFn.kMesh):

            log.debug(f'invalidateColors() expects a mesh ({intermediateObject.apiTypeStr} given)!')
            return

        # Check if colour set is active
        #
        fnMesh = om.MFnMesh(intermediateObject)
        meshName = fnMesh.fullPathName()
        currentColorSet = fnMesh.currentColorSetName()

        skinClusterName = f'{self.namespace()}:{self.name()}'

        if currentColorSet == self.__color_set_name__:

            mc.transferPaintWeights(skinClusterName, meshName, colorRamp=self.__color_ramp__)

    def iterInfluences(self):
        """
        Returns a generator that yields the influence id-objects pairs from this skin.

        :rtype: Iterator[Tuple[int, Any]]
        """

        return skinutils.iterInfluences(self.object())

    def numInfluences(self):
        """
        Returns the number of influences in use by this skin.

        :rtype: int
        """

        matrixPlug = plugutils.findPlug(self.object(), 'matrix')
        return matrixPlug.numConnectedElements()

    def maxInfluences(self):
        """
        Returns the max number of influences for this skin.

        :rtype: int
        """

        maxInfluencesPlug = plugutils.findPlug(self.object(), 'maxInfluences')
        return plugmutators.getValue(maxInfluencesPlug)

    def setMaxInfluences(self, count):
        """
        Updates the max number of influences for this skin.

        :type count: int
        :rtype: None
        """

        maintainMaxInfluencesPlug = plugutils.findPlug(self.object(), 'maintainMaxInfluences')
        plugmutators.setValue(maintainMaxInfluencesPlug, True)

        maxInfluencesPlug = plugutils.findPlug(self.object(), 'maxInfluences')
        plugmutators.setValue(maxInfluencesPlug, count)

    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        skinutils.selectInfluence(self.object(), influenceId)

    def addInfluence(self, *influences):
        """
        Adds an influence to this skin.

        :type influences: Union[Any, List[Any]]
        :rtype: bool
        """

        node = fnnode.FnNode()

        for influence in influences:

            success = node.trySetObject(influence)

            if success:

                skinutils.addInfluence(self.object(), node.object())

            else:

                log.warning(f'Unable to locate influence: {influence}')
                continue

    def removeInfluence(self, *influenceIds):
        """
        Removes an influence from this skin by id.

        :type influenceIds: Union[int, List[int]]
        :rtype: None
        """

        for influenceId in influenceIds:

            skinutils.removeInfluence(self.object(), influenceId)

    def iterVertexWeights(self, *args):
        """
        Returns a generator that yields vertex-weights pairs from this skin.
        If no vertex indices are supplied then all weights are yielded instead.

        :rtype: Iterator[Tuple[int, Dict[int, float]]]
        """

        return skinutils.iterWeightList(self.object(), vertexIndices=args)

    @undo.Undo(name='Apply Vertex Weights')
    def applyVertexWeights(self, vertexWeights):
        """
        Assigns the supplied vertex weights to this skin.

        :type vertexWeights: Dict[int, Dict[int, float]]
        :rtype: None
        """

        skinutils.setWeightList(self.object(), vertexWeights)

    @undo.Undo(name='Reset Pre-Bind Matrices')
    def resetPreBindMatrices(self):
        """
        Resets the pre-bind matrices on the associated joints.

        :rtype: None
        """

        skinutils.resetPreBindMatrices(self.object())

    @undo.Undo(name='Reset Intermediate Object')
    def resetIntermediateObject(self):
        """
        Resets the control points on the associated intermediate object.

        :rtype: None
        """

        skinutils.resetIntermediateObject(self.object())

    @classmethod
    def iterInstances(cls, apiType=om.MFn.kSkinClusterFilter):
        """
        Returns a generator that yields skin cluster instances.

        :rtype: iter
        """

        return super(FnSkin, cls).iterInstances(apiType=apiType)
    # endregion
