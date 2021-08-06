from abc import ABCMeta, abstractmethod
from six import with_metaclass
from copy import deepcopy

from . import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnSkin(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC skinning.
    """

    __slots__ = ()

    @abstractmethod
    def shape(self):
        """
        Returns the shape node associated with the deformer.

        :rtype: Any
        """

        pass

    @abstractmethod
    def iterControlPoints(self, *args):
        """
        Returns a generator that yields control points.

        :rtype: iter
        """

        pass

    def controlPoints(self, *args):
        """
        Returns the control points from the intermediate object.

        :rtype: list
        """

        return list(self.iterControlPoints(*args))

    @abstractmethod
    def numControlPoints(self):
        """
        Evaluates the number of control points from this deformer.

        :rtype: int
        """

        pass

    @abstractmethod
    def iterInfluences(self):
        """
        Returns a generator that yields all of the influence object from this deformer.

        :rtype: iter
        """

        pass

    def influences(self):
        """
        Returns all of the influence objects from this deformer.

        :rtype: dict[int:Any]
        """

        return dict(self.iterInfluences())

    @property
    @abstractmethod
    def maxInfluences(self):
        """
        Getter method that returns the max number of influences for this deformer.

        :rtype: int
        """

        pass

    @abstractmethod
    def iterWeights(self, *args):
        """
        Returns a generator that yields skin weights.
        If no vertex indices are supplied then all of the skin weights should be yielded.

        :rtype: iter
        """

        pass

    def weights(self, *args):
        """
        Returns a dictionary with skin weights.
        Each key represents a vertex index for each set of vertex weights.

        :rtype: dict[int:dict[int:float]]
        """

        return dict(self.iterWeights(*args))

    def setWeights(self, vertexIndices, target, source, amount, falloff=None):
        """
        Sets the supplied target ID to the specified amount while preserving normalization.

        :type vertexIndices: list[int]
        :type target: int
        :type source: list[int]
        :type amount: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        pass

    def scaleWeights(self, vertexIndices, target, source, percent, falloff=None):
        """
        Scales the supplied target ID to the specified amount while preserving normalization.

        :type vertexIndices: list
        :type target: int
        :type source: list[int]
        :type percent: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        pass

    def incrementWeights(self, vertexIndices, target, source, increment, falloff=None):
        """
        Increments the supplied target ID to the specified amount while preserving normalization.

        :type vertexIndices: list
        :type target: int
        :type source: list[int]
        :type increment: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        pass

    def normalizeWeights(self, vertexWeights):

        pass

    def pruneWeights(self, vertexWeights):

        pass

    def applyWeights(self, vertices):

        pass
