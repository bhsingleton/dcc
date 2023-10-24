from dataclasses import dataclass, field
from . import vector, adc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class BoundingBox(adc.ADC):
    """
    Overload of `ADC` that interfaces with bounding box data.
    """

    # region Fields
    min: vector.Vector = field(default_factory=lambda: vector.Vector.zero)
    max: vector.Vector = field(default_factory=lambda: vector.Vector.zero)
    # endregion

    # region Dunderscores
    def __contains__(self, point):
        """
        Private method that implements the `in` operator.

        :type point: vector.Vector
        :rtype: bool
        """

        return self.contains(point)
    # endregion

    # region Methods
    def width(self):
        """
        Returns the width of this bounding box.

        :rtype: float
        """

        return abs((self.max - self.min).x)

    def height(self):
        """
        Returns the height of this bounding box.

        :rtype: float
        """

        return abs((self.max - self.min).y)

    def depth(self):
        """
        Returns the depth of this bounding box.

        :rtype: float
        """

        return abs((self.max - self.min).z)

    def center(self):
        """
        Returns the center of this bounding box.

        :rtype: vector.Vector
        """

        return (self.min * 0.5) + (self.max * 0.5)

    def contains(self, point):
        """
        Evaluates if the supplied point is inside this bounding box.

        :type point: vector.Vector
        :rtype: bool
        """

        return self.min <= point <= self.max

    def expand(self, *points):
        """
        Expands the bounding-box to account for the supplied points.

        :type points: Union[vector.Vector, List[vector.Vector]]
        :rtype: self
        """

        # Iterate through points
        #
        isEmpty = (self.min.length() == 0.0) and (self.max.length() == 0.0)

        for point in points:

            # Check if bounding-box is empty
            #
            if isEmpty:

                self.min = point.copy()
                self.max = point.copy()
                isEmpty = False

                continue

            # Iterate through axes
            #
            for axis in range(3):

                # Evaluate axis
                #
                if point[axis] > self.max[axis]:

                    self.max[axis] = point[axis]

                elif point[axis] < self.min[axis]:

                    self.min[axis] = point[axis]

                else:

                    continue

        return self
    # endregion
