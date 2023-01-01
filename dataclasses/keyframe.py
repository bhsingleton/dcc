from dataclasses import dataclass, field, replace
from . import vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Keyframe:
    """
    Data class for animation curve handles.
    """

    # region Fields
    value: float = 0.0
    frame: float = 0.0
    inTangent: vector.Vector = field(default_factory=vector.Vector)
    outTangent: vector.Vector = field(default_factory=vector.Vector)
    # endregion

    # region Methods
    def copy(self):
        """
        Returns a copy of this keyframe.

        :rtype: Vector
        """

        return replace(self)
    # endregion
