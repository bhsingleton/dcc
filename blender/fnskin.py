from . import fnnode
from ..abstract import afnskin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSkin(afnskin.AFnSkin, fnnode.FnNode):
    """
    Overload of `AFnSkin` that implements the skin interface for Blender.
    """

    # region Methods
    @classmethod
    def create(cls, mesh):
        """
        Creates a skin and assigns it to the supplied shape.

        :type mesh: pymxs.MXSWrapperBase
        :rtype: FnSkin
        """

        return cls()

    def transform(self):
        """
        Returns the transform node associated with the skin.

        :rtype: Any
        """

        return

    def shape(self):
        """
        Returns the shape node associated with the skin.

        :rtype: Any
        """

        return

    def intermediateObject(self):
        """
        Returns the intermediate object associated with the skin.

        :rtype: Any
        """

        return

    def select(self, replace=True):
        """
        Selects the node associated with this function set.

        :type replace: bool
        :rtype: None
        """

        pass

    def selectModifier(self):
        """
        Selects this modifier from the modify panel.

        :rtype: None
        """

        pass

    def isSelected(self):
        """
        Evaluates if this node is selected.

        :rtype: bool
        """

        return False

    def isPartiallySelected(self):
        """
        Evaluates if this node is partially selected.
        Useful for things like deformers or modifiers.

        :rtype: bool
        """

        return False

    def iterVertices(self):
        """
        Returns a generator that yields vertex indices.

        :rtype: Iterator[int]
        """

        return iter([])

    def iterSelection(self):
        """
        Returns a generator that yields the selected vertex elements.

        :rtype: Iterator[int]
        """

        return iter([])

    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: List[int]
        :rtype: None
        """

        pass

    def iterSoftSelection(self):
        """
        Returns a generator that yields selected vertex-weight pairs.

        :rtype Iterator[Dict[int, float]]
        """

        return iter([])

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
        Returns a generator that yields the influence id-objects pairs from this skin.

        :rtype: Iterator[Tuple[int, Any]]
        """

        return iter([])

    def addInfluence(self, *influences):
        """
        Adds an influence to this skin.

        :type influences: Union[Any, List[Any]]
        :rtype: None
        """

        pass

    def removeInfluence(self, *influenceIds):
        """
        Removes an influence from this skin by id.

        :type influenceIds: Union[int, List[int]]
        :rtype: None
        """

        pass

    def numInfluences(self):
        """
        Returns the number of influences in use by this skin.

        :rtype: int
        """

        return 0

    def maxInfluences(self):
        """
        Returns the max number of influences for this skin.

        :rtype: int
        """

        return 0

    def setMaxInfluences(self, count):
        """
        Updates the max number of influences for this skin.

        :type count: int
        :rtype: None
        """

        pass

    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        pass

    def iterVertexWeights(self, *indices):
        """
        Returns a generator that yields vertex-weights pairs from this skin.
        If no vertex indices are supplied then all weights are yielded instead.

        :type indices: Union[int, List[int]]
        :rtype: Iterator[Tuple[int, Dict[int, float]]]
        """

        return iter([])

    def applyVertexWeights(self, vertexWeights):
        """
        Assigns the supplied vertex weights to this skin.

        :type vertexWeights: Dict[int, Dict[int, float]]
        :rtype: None
        """

        pass

    def resetPreBindMatrices(self):
        """
        Resets the pre-bind matrices on the associated joints.

        :rtype: None
        """

        pass

    def resetIntermediateObject(self):
        """
        Resets the control points on the associated intermediate object.

        :rtype: None
        """

        pass

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields texture instances.

        :rtype: iter
        """

        return iter([])
    # endregion
