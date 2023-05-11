from dataclasses import dataclass, field, replace
from typing import Union
from . import adc, vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Keyframe(adc.ADC):
    """
    Overload of `ADC` that interfaces with animation curve data.
    """

    # region Fields
    time: float = 0.0
    value: float = 0.0
    inTangent: vector.Vector = field(default_factory=vector.Vector)
    inTangentType: Union[int, str] = 0
    outTangent: vector.Vector = field(default_factory=vector.Vector)
    outTangentType: Union[int, str] = 0
    # endregion

    # region Dunderscores
    def __neg__(self):
        """
        Private method that implements the inversion operator.

        :rtype: Vector
        """

        keyframe = self.copy()
        keyframe.value = -self.value
        keyframe.inTangent.y = -self.inTangent.y
        keyframe.outTangent.y = -self.outTangent.y

        return keyframe
    # endregion
