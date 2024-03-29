import math
import colorsys

from dataclasses import dataclass, fields, replace
from . import adc
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Colour(adc.ADC):
    """
    Data class for RGB colours.
    """

    # region Fields
    r: float = 0
    g: float = 0
    b: float = 0
    a: float = 1.0
    # endregion

    # region Dunderscores
    def __post_init__(self):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Validate vector
        #
        if all(isinstance(x, (int, float)) for x in self):

            return

        # Check if sequence was passed to constructor
        #
        args = self.x

        if hasattr(args, '__getitem__') and hasattr(args, '__len__'):

            # Un-package items into vector
            #
            for (i, item) in enumerate(args):

                self[i] = item

        else:

            raise TypeError(f'__post_init__() expects either an int or float ({type(args).__name__} given)!')

    def __eq__(self, other):
        """
        Private method that implements the equal operator.

        :type other: Colour
        :rtype: bool
        """

        return self.isEquivalent(other)

    def __ne__(self, other):
        """
        Private method that implements the not equal operator.

        :type other: Colour
        :rtype: bool
        """

        return not self.isEquivalent(other)

    def __neg__(self):
        """
        Private method that implements the inversion operator.

        :rtype: Colour
        """

        return self.inverse()

    def __iter__(self):
        """
        Private method that returns a generator that yields data field values.

        :rtype: Iterator[float]
        """

        return iter((self.r, self.g, self.b, self.a))

    def __len__(self):
        """
        Private method that returns the number of fields belonging to this class.

        :rtype: int
        """

        return 4
    # endregion

    # region Properties
    @classproperty
    def red(cls):
        """
        Getter method that returns the x-axis vector.

        :rtype: Vector
        """

        return Colour(1.0, 0.0, 0.0)

    @classproperty
    def green(cls):
        """
        Getter method that returns the y-axis vector.

        :rtype: Vector
        """

        return Colour(0.0, 1.0, 0.0)

    @classproperty
    def blue(cls):
        """
        Getter method that returns the z-axis vector.

        :rtype: Vector
        """

        return Colour(0.0, 0.0, 1.0)

    @classproperty
    def black(cls):
        """
        Getter method that returns the origin vector.

        :rtype: Vector
        """

        return Colour(0.0, 0.0, 0.0)

    @classproperty
    def white(cls):
        """
        Getter method that returns a one vector.

        :rtype: Vector
        """

        return Colour(1.0, 1.0, 1.0)
    # endregion

    # region Methods
    def darker(self, amount=0.25):
        """
        Returns a darker colour.

        :type amount: float
        :rtype: Color
        """

        hue, lightness, saturation = colorsys.rgb_to_hls(self.r, self.g, self.b)
        lightness -= (lightness * amount)

        red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)

        return Colour(red, green, blue)

    def lighter(self, amount=0.25):
        """
        Returns a lighter colour.

        :type amount: float
        :rtype: Color
        """

        hue, lightness, saturation = colorsys.rgb_to_hls(self.r, self.g, self.b)
        lightness += ((1.0 - lightness) * amount)

        red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)

        return Colour(red, green, blue)

    def hexify(self):
        """
        Converts this colour to a hex string.

        :rtype: str
        """

        return '#{:X}{:X}{:X}'.format(int(self.r * 255.0), int(self.g * 255.0), int(self.b * 255.0))

    def inverse(self):
        """
        Returns an inversed copy of this colour.

        :rtype: Colour
        """

        return Colour(1.0 - self.r, 1.0 - self.g, 1.0 - self.b, self.a)

    def isEquivalent(self, other, tolerance=1e-3):
        """
        Evaluates if the two supplied colours are equivalent.

        :type other: Colour
        :type tolerance: float
        :rtype: bool
        """

        return all(math.isclose(x, y, abs_tol=tolerance) for (x, y) in zip(self, other))

    def copy(self):
        """
        Returns a copy of this colour.

        :rtype: Colour
        """

        return replace(self)

    def toList(self):
        """
        Converts this colour to a list.

        :rtype: List[float]
        """

        return list(self)
    # endregion
