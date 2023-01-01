from dataclasses import dataclass, field, replace
from . import vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class BezierPoint:
    """
    Data class for bezier-curve points.
    """

    # region Fields
    inTangent: vector.Vector = field(default_factory=vector.Vector)  # Local Space
    point: vector.Vector = field(default_factory=vector.Vector)  # Parent Space
    outTangent: vector.Vector = field(default_factory=vector.Vector)  # Local Space
    # endregion

    # region Dunderscores
    def __mul__(self, other):
        """
        Private method that implements the multiplication operator.

        :type other: Union[int, float, Vector]
        :rtype: Union[float, Vector]
        """

        self.point * other
        return self

    def __imul__(self, other):
        """
        Private method that implements the in-place multiplication operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        self.point *= other
        return self
    # endregion

    # region Methods
    def copy(self):
        """
        Returns a copy of this bezier point.

        :rtype: Vector
        """

        return replace(self)
    # endregion
