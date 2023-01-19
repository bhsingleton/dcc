from dataclasses import dataclass, field
from . import adc, vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Plane(adc.ADC):
    """
    Overload of `ADC` that interfaces with plane data.
    """

    # region Fields
    origin: vector.Vector = field(default_factory=(lambda: vector.Vector.zero))
    normal: vector.Vector = field(default_factory=(lambda: vector.Vector.xAxis))
    # endregion

    # region Methods
    def project(self, point):
        """
        Projects the supplied point onto this plane.

        :type point: vector.Vector
        :rtype: vector.Vector
        """

        vec = point - self.origin
        dot = vec * self.normal
        proj = point - (self.origin + (self.normal * dot))

        return self.origin + proj
    # endregion
