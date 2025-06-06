import pymxs

from .libs import modifierutils, skinutils
from . import fnnode
from ..abstract import afnskin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSkin(afnskin.AFnSkin, fnnode.FnNode):
    """
    Overload of `AFnSkin` that outlines function set behaviour for skin weighting in 3ds Max.
    This class also inherits from FnNode but be aware not all functions will be compatible.
    Because of the UI dependency in 3ds Max we have to actively make sure we're in the modify panel.
    """

    # region Dunderscores
    __slots__ = ('_node', '_baseObject')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare class variables
        #
        self._node = None
        self._baseObject = None

        # Call parent method
        #
        super(FnSkin, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    @classmethod
    def create(cls, mesh):
        """
        Creates a skin and assigns it to the supplied shape.

        :type mesh: fnmesh.FnMesh
        :rtype: FnSkin
        """

        skin = pymxs.runtime.Skin()
        pymxs.runtime.addModifier(mesh, skin)

        return cls(skin)

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Locate skin modifier from object
        #
        obj = self.getMXSWrapper(obj)
        skinModifier = modifierutils.getModifierByClass(obj, pymxs.runtime.Skin)

        super(FnSkin, self).setObject(skinModifier)

        # Store reference to base object
        #
        node = modifierutils.getNodeFromModifier(skinModifier)

        self._node = pymxs.runtime.getHandleByAnim(node)
        self._baseObject = pymxs.runtime.getHandleByAnim(node.baseObject)
        self._influences.clear()

    def transform(self):
        """
        Returns the transform node associated with the skin.

        :rtype: Any
        """

        return pymxs.runtime.getAnimByHandle(self._node)

    def shape(self):
        """
        Returns the shape node associated with the skin.

        :rtype: Any
        """

        return self.transform()  # They're the same thing in 3ds Max

    def intermediateObject(self):
        """
        Returns the intermediate object associated with the skin.

        :rtype: Any
        """

        return pymxs.runtime.getAnimByHandle(self._baseObject)

    def select(self, replace=True):
        """
        Selects the node associated with this function set.

        :type replace: bool
        :rtype: None
        """

        self.scene.setActiveSelection([self.shape()], replace=replace)
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

        return self.isSelected() or self.shape() in self.scene.getActiveSelection()

    def iterVertices(self):
        """
        Returns a generator that yields vertex indices.

        :rtype: Iterator[int]
        """

        return range(1, self.numControlPoints() + 1, 1)

    def iterSelection(self):
        """
        Returns a generator that yields the selected vertex elements.

        :rtype: Iterator[int]
        """

        return skinutils.iterSelection(self.object())

    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: List[int]
        :rtype: None
        """

        pymxs.runtime.skinOps.selectVertices(self.object(), vertices)

    def iterSoftSelection(self):
        """
        Returns a generator that yields selected vertex-weight pairs.

        :rtype Iterator[Dict[int, float]]
        """

        for vertexIndex in self.iterSelection():

            yield vertexIndex, 1.0

    def showColors(self):
        """
        Enables color feedback for the associated shape.

        :rtype: None
        """

        skinutils.showColors(self.object())

    def hideColors(self):
        """
        Disable color feedback for the associated shape.

        :rtype: None
        """

        pymxs.runtime.subObjectLevel = 0

    def iterInfluences(self):
        """
        Returns a generator that yields the influence id-objects pairs from this skin.

        :rtype: Iterator[Tuple[int, Any]]
        """

        return skinutils.iterInfluences(self.object())

    def addInfluence(self, *influences):
        """
        Adds an influence to this skin.

        :type influences: Union[Any, List[Any]]
        :rtype: None
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

    def numInfluences(self):
        """
        Returns the number of influences in use by this skin.

        :rtype: int
        """

        return skinutils.influenceCount(self.object())

    def maxInfluences(self):
        """
        Returns the max number of influences for this skin.

        :rtype: int
        """

        return self.object().bone_limit

    def setMaxInfluences(self, count):
        """
        Updates the max number of influences for this skin.

        :type count: int
        :rtype: None
        """

        self.object().bone_limit = count

    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        skinutils.selectInfluence(self.object(), influenceId)

    def iterVertexWeights(self, *indices):
        """
        Returns a generator that yields vertex-weights pairs from this skin.
        If no vertex indices are supplied then all weights are yielded instead.

        :type indices: Union[int, List[int]]
        :rtype: Iterator[Tuple[int, Dict[int, float]]]
        """

        return skinutils.iterVertexWeights(self.object(), vertexIndices=indices)

    def applyVertexWeights(self, vertexWeights):
        """
        Assigns the supplied vertex weights to this skin.

        :type vertexWeights: Dict[int, Dict[int, float]]
        :rtype: None
        """

        skinutils.setVertexWeights(self.object(), vertexWeights)

    def resetPreBindMatrices(self):
        """
        Resets the pre-bind matrices on the associated joints.

        :rtype: None
        """

        skinutils.resetMeshBindMatrix(self.object())
        skinutils.resetBoneBindMatrices(self.object())

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

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields texture instances.

        :rtype: iter
        """

        return iter(pymxs.runtime.getClassInstances(pymxs.runtime.Skin))
    # endregion
