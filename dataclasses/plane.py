from dataclasses import dataclass, field, replace
from . import vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Plane:
    """
    Data class for planes.
    """

    # region Fields
    origin: vector.Vector = field(default_factory=(lambda: vector.Vector.origin))
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
