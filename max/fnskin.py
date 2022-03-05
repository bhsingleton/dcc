import pymxs

from dcc import fnnode
from dcc.abstract import afnskin
from dcc.max.libs import modifierutils, skinutils
from dcc.max.decorators import commandpaneloverride

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
        self.selectModifier()

    def selectModifier(self):
        """
        Selects this modifier from the modify panel.

        :rtype: None
        """

        # Check if modify panel is open
        #
        if self.isModifyPanelOpen():

            pymxs.runtime.modPanel.setCurrentObject(self.object(), node=self.shape())

    @staticmethod
    def isModifyPanelOpen():
        """
        Evaluates if the modify panel is open.

        :rtype: bool
        """

        return pymxs.runtime.getCommandPanelTaskMode() == pymxs.runtime.Name('modify')

    def isSelected(self):
        """
        Evaluates if this node is selected.

        :rtype: bool
        """

        if self.isModifyPanelOpen():

            return pymxs.runtime.modPanel.getCurrentObject() == self.object()

        else:

            return False

    def isPartiallySelected(self):
        """
        Evaluates if this node is partially selected.
        Useful for things like deformers or modifiers.

        :rtype: bool
        """

        return self.isSelected() or self.shape() in self.getActiveSelection()

    def iterVertices(self):
        """
        Returns a generator that yields all vertex indices.

        :rtype: iter
        """

        return range(1, self.numControlPoints() + 1, 1)

    def iterSelection(self):
        """
        Returns a generator that yields the selected vertex indices.

        :rtype: iter
        """

        return skinutils.iterSelection(self.object())

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: List[int]
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

    def iterInfluences(self):
        """
        Returns a generator that yields all the influence objects from this deformer.

        :rtype: iter
        """

        return skinutils.iterInfluences(self.object())

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

    def iterVertexWeights(self, *args):
        """
        Returns a generator that yields weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are yielded instead.

        :rtype: iter
        """

        return skinutils.iterVertexWeights(self.object(), vertexIndices=args)

    def applyVertexWeights(self, vertexWeights):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertexWeights: Dict[int, Dict[int, float]]
        :rtype: None
        """

        skinutils.setVertexWeights(self.object(), vertexWeights)

    @commandpaneloverride.commandPanelOverride(mode='modify')
    def resetPreBindMatrices(self):
        """
        Resets the pre-bind matrices on the associated joints.

        :rtype: None
        """

        # Toggle always deforms
        #
        skinModifier = self.object()
        skinModifier.always_deforms = False
        skinModifier.always_deforms = True

    def resetIntermediateObject(self):
        """
        Resets the control points on the associated intermediate object.

        :rtype: None
        """

        # Store deformed points
        #
        shape = self.shape()

        numPoints = pymxs.runtime.polyOp.getNumVerts(shape)
        points = [None] * numPoints

        for i in range(numPoints):

            point = pymxs.runtime.polyOp.getVert(shape, i + 1)
            points[i] = point.x, point.y, point.z

        # Reset influences
        #
        self.resetPreBindMatrices()

        # Apply deformed values to intermediate object
        #
        intermediateObject = self.intermediateObject()

        for i in range(numPoints):

            pymxs.runtime.polyOp.setVert(intermediateObject, i + 1, points[i])
