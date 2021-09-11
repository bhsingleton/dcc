import pymxs

from . import fnnode
from .libs import modifierutils
from .decorators import commandpaneloverride
from ..abstract import afnskin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSkin(afnskin.AFnSkin, fnnode.FnNode):
    """
    Overload of AFnSkin that outlines function set behaviour for skin weighting in 3ds Max.
    This class also inherits from FnNode but be aware not all functions will be compatible.
    Because of the UI dependency in 3ds Max we have to actively make sure we're in the modify panel.
    """

    __slots__ = ('_shape', '_intermediateObject')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Declare class variables
        #
        self._shape = None
        self._intermediateObject = None

        # Call parent method
        #
        super(FnSkin, self).__init__(*args, **kwargs)

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Locate skin modifier from object
        #
        obj = self.getMXSWrapper(obj)
        skinModifier = modifierutils.findModifierByType(obj, pymxs.runtime.skin)

        super(FnSkin, self).setObject(skinModifier)

        # Store reference to shape node
        #
        shape = modifierutils.getNodeFromModifier(skinModifier)

        self._shape = pymxs.runtime.getHandleByAnim(shape)
        self._intermediateObject = pymxs.runtime.getHandleByAnim(shape.baseObject)

    def shape(self):
        """
        Returns the shape node associated with the deformer.

        :rtype: Any
        """

        return pymxs.runtime.getAnimByHandle(self._shape)

    def intermediateObject(self):
        """
        Returns the intermediate object associated with the deformer.

        :rtype: Any
        """

        return pymxs.runtime.getAnimByHandle(self._intermediateObject)

    def select(self, replace=True):
        """
        Selects the node associated with this function set.

        :type replace: bool
        :rtype: None
        """

        self.setActiveSelection([self.shape()], replace=replace)

    def isSelected(self):
        """
        Evaluates if this node is selected.

        :rtype: bool
        """

        return self.shape() in self.getActiveSelection()

    def iterVertices(self):
        """
        Returns a generator that yields all vertex indices.

        :rtype: iter
        """

        return range(1, self.numControlPoints() + 1, 1)

    def controlPoint(self, vertexIndex):
        """
        Returns a generator that yields control points.

        :type vertexIndex: int
        :rtype: list[float, float, float]
        """

        point = pymxs.runtime.polyOp.getVert(self.intermediateObject(), vertexIndex)
        return point.x, point.y, point.z

    def numControlPoints(self):
        """
        Evaluates the number of control points from the associated shape.

        :rtype: int
        """

        return pymxs.runtime.polyOp.getNumVerts(self.intermediateObject())

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def iterSelection(self):
        """
        Returns the selected vertex elements.
        This operation is not super efficient in max...

        :rtype: list[int]
        """

        # Iterate through vertices
        #
        skinModifier = self.object()

        for i in range(1, self.numControlPoints() + 1, 1):

            # Check if vertex is selected
            #
            if pymxs.runtime.skinOps.isVertexSelected(skinModifier, i):

                yield i

            else:

                continue

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: list[int]
        :rtype: None
        """

        pymxs.runtime.skinOps.selectVertices(self.object(), vertices)

    def iterSoftSelection(self):
        """
        Returns a generator that yields selected vertex and soft value pairs.

        :rtype iter
        """

        for vertexIndex in self.iterSelection():

            yield vertexIndex, 1.0

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def showColors(self):
        """
        Enables color feedback for the associated shape.

        :rtype: None
        """

        # Enter envelope mode
        #
        pymxs.runtime.subObjectLevel = 1

        # Modify display settings
        #
        skinModifier = self.object()
        skinModifier.drawVertices = True
        skinModifier.shadeWeights = True
        skinModifier.colorAllWeights = False
        skinModifier.draw_all_envelopes = False
        skinModifier.draw_all_vertices = False
        skinModifier.draw_all_gizmos = False
        skinModifier.showNoEnvelopes = True
        skinModifier.showHiddenVertices = False
        skinModifier.crossSectionsAlwaysOnTop = True
        skinModifier.envelopeAlwaysOnTop = True

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def hideColors(self):
        """
        Disable color feedback for the associated shape.

        :rtype: None
        """

        # Exit envelop mode
        #
        pymxs.runtime.subObjectLevel = 0

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def iterInfluences(self):
        """
        Returns a generator that yields all of the influence object from this deformer.

        :rtype: iter
        """

        # Iterate through bones
        #
        skinModifier = self.object()
        numBones = pymxs.runtime.skinOps.getNumberBones(skinModifier)

        for i in range(1, numBones + 1, 1):

            # Get bone properties
            #
            boneId = pymxs.runtime.skinOps.getBoneIDByListID(skinModifier, i)
            boneName = pymxs.runtime.skinOps.getBoneName(skinModifier, boneId, 0)

            # Get bone from name
            #
            nodes = pymxs.runtime.getNodeByName(boneName, exact=True, all=True)
            numNodes = nodes.count

            bone = None

            if numNodes == 0:

                raise RuntimeError('iterInfluences() cannot locate bone from name: %s' % boneName)

            elif numNodes == 1:

                bone = nodes[0]

            else:

                dependencies = pymxs.runtime.dependsOn(skinModifier)
                bone = [x for x in nodes if x in dependencies][0]

            yield boneId, bone

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def addInfluence(self, influence):
        """
        Adds an influence to this deformer.

        :type influence: pymxs.MXSWrapperBase
        :rtype: bool
        """

        pymxs.runtime.skinOps.addBone(self.object(), influence, 0)

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def removeInfluence(self, influenceId):
        """
        Removes an influence from this deformer.

        :type influenceId: int
        :rtype: bool
        """

        pymxs.runtime.skinOps.removeBone(self.object(), influenceId)

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def numInfluences(self):
        """
        Returns the number of influences being use by this deformer.

        :rtype: int
        """

        return pymxs.runtime.skinOps.getNumberBones(self.object())

    def maxInfluences(self):
        """
        Getter method that returns the max number of influences for this deformer.

        :rtype: int
        """

        return self.object().bone_limit

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        pymxs.runtime.skinOps.selectBone(self.object(), influenceId)

    @commandpaneloverride.commandPanelOverride(mode='modify')
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

            args = range(1, self.numControlPoints() + 1, 1)

        # Iterate through arguments
        #
        for arg in args:

            # Iterate through bones
            #
            skinModifier = self.object()
            numBones = pymxs.runtime.skinOps.getVertexWeightCount(skinModifier, arg)

            vertexWeights = {}

            for i in range(1, numBones + 1, 1):

                boneId = pymxs.runtime.skinOps.getVertexWeightBoneID(skinModifier, arg, i)
                boneWeight = pymxs.runtime.skinOps.getVertexWeight(skinModifier, arg, i)

                vertexWeights[boneId] = boneWeight

            # Yield vertex weights
            #
            yield arg, vertexWeights

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def applyVertexWeights(self, vertexWeights):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertexWeights: dict[int:dict[int:float]]
        :rtype: None
        """

        # Define undo chunk
        #
        with pymxs.undo(True, 'Apply Weights'):

            # Bake selected vertices before applying weights
            # This allows for undo support
            #
            skinModifier = self.object()
            pymxs.runtime.skinOps.bakeSelectedVerts(skinModifier)

            # Iterate and replace vertex weights
            #
            for (vertexIndex, weights) in vertexWeights.items():

                weights = self.removeZeroWeights(weights)

                pymxs.runtime.skinOps.replaceVertexWeights(
                    skinModifier,
                    vertexIndex,
                    list(weights.keys()),
                    list(weights.values())
                )

        # Force redraw
        # This prevents any zero weights being returned in the same execution thread!
        #
        pymxs.runtime.completeRedraw()
