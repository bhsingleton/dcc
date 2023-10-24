from dataclasses import dataclass, field
from . import adc, vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class BezierPoint(adc.ADC):
    """
    Overload of `ADC` that interfaces with bezier-curve point data.
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
        :rtype: BezierPoint
        """

        self.point * other
        return self

    def __imul__(self, other):
        """
        Private method that implements the in-place multiplication operator.

        :type other: Union[int, float, Vector]
        :rtype: BezierPoint
        """

        self.point *= other
        return self
    # endregion
