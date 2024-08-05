import math

from dataclasses import dataclass, fields, replace
from . import adc, transformationmatrix
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Vector(adc.ADC):
    """
    Data class for 3D vectors.
    """

    # region Fields
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
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
            for (i, item) in enumerate(args[0:3]):

                self[i] = item

        else:

            raise TypeError(f'__post_init__() expects either an int or float ({type(args).__name__} given)!')

    def __eq__(self, other):
        """
        Private method that implements the equal operator.

        :type other: Vector
        :rtype: bool
        """

        return self.isEquivalent(other)

    def __ne__(self, other):
        """
        Private method that implements the not equal operator.

        :type other: Vector
        :rtype: bool
        """

        return not self.isEquivalent(other)

    def __lt__(self, other):
        """
        Private method that implements the less than operator.

        :type other: Vector
        :rtype: bool
        """

        return self.x < other.x and self.y < other.y and self.z < other.z

    def __le__(self, other):
        """
        Private method that implements the less than or equal to operator.

        :type other: Vector
        :rtype: bool
        """

        return self < other or self.isEquivalent(other)

    def __gt__(self, other):
        """
        Private method that implements the greater than operator.

        :type other: Vector
        :rtype: bool
        """

        return self.x > other.x and self.y > other.y and self.z > other.z

    def __ge__(self, other):
        """
        Private method that implements the greater than or equal to operator.

        :type other: Vector
        :rtype: bool
        """

        return self > other or self.isEquivalent(other)

    def __add__(self, other):
        """
        Private method that implements the addition operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        copy = self.copy()
        copy.__iadd__(other)

        return copy

    def __radd__(self, other):
        """
        Private method that implements the right-side addition operator.

        :type other: Union[int, float]
        :rtype: Vector
        """

        if isinstance(other, (int, float)):

            other = Vector(other, other, other)
            return other.__add__(self)

        else:

            raise NotImplemented(f'__radd__() expects either an int or float ({type(other).__name__} given)!')

    def __iadd__(self, other):
        """
        Private method that implements the in-place addition operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        if isinstance(other, Vector):

            self.x += other.x
            self.y += other.y
            self.z += other.z

        elif isinstance(other, (int, float)):

            self.x += other
            self.y += other
            self.z += other

        else:

            return NotImplemented

        return self

    def __sub__(self, other):
        """
        Private method that implements the subtraction operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        copy = self.copy()
        copy.__isub__(other)

        return copy

    def __rsub__(self, other):
        """
        Private method that implements the right-side subtraction operator.

        :type other: Union[int, float]
        :rtype: Vector
        """

        if isinstance(other, (int, float)):

            other = Vector(other, other, other)
            return other.__sub__(self)

        else:

            return NotImplemented

    def __isub__(self, other):
        """
        Private method that implements the in-place subtraction operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        if isinstance(other, Vector):

            self.x -= other.x
            self.y -= other.y
            self.z -= other.z

        elif isinstance(other, (int, float)):

            self.x -= other
            self.y -= other
            self.z -= other

        else:

            return NotImplemented

        return self

    def __mul__(self, other):
        """
        Private method that implements the multiplication operator.

        :type other: Union[int, float, Vector]
        :rtype: Union[float, Vector]
        """

        if isinstance(other, Vector):

            return self.dot(other)

        else:

            copy = self.copy()
            copy.__imul__(other)

            return copy

    def __rmul__(self, other):
        """
        Private method that implements the right-side multiplication operator.

        :type other: Union[int, float]
        :rtype: Vector
        """

        if isinstance(other, (int, float)):

            copy = self.copy()
            return copy.__imul__(other)

        else:

            return NotImplemented

    def __imul__(self, other):
        """
        Private method that implements the in-place multiplication operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        if isinstance(other, Vector):

            self.x *= other.x
            self.y *= other.y
            self.z *= other.z

        elif isinstance(other, (int, float)):

            self.x *= other
            self.y *= other
            self.z *= other

        elif isinstance(other, transformationmatrix.TransformationMatrix):

            matrix = transformationmatrix.TransformationMatrix(row4=self)
            matrix *= other

            self.x, self.y, self.z = matrix.row4

        else:

            return NotImplemented

        return self

    def __truediv__(self, other):
        """
        Private method that implements the division operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        copy = self.copy()
        copy.__itruediv__(other)

        return copy

    def __rtruediv__(self, other):
        """
        Private method that implements the right-side division operator.

        :type other: Union[int, float]
        :rtype: Vector
        """

        if isinstance(other, (int, float)):

            other = Vector(other, other, other)
            return other.__itruediv__(self)

        else:

            raise NotImplemented(f'__rtruediv__() expects either an int or float ({type(other).__name__} given)!')

    def __itruediv__(self, other):
        """
        Private method that implements the in-place division operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        if isinstance(other, Vector):

            try:

                self.x /= other.x
                self.y /= other.y
                self.z /= other.z

            except ZeroDivisionError as exception:

                log.debug(exception)

        elif isinstance(other, (float, int)):

            try:

                self.x /= other
                self.y /= other
                self.z /= other

            except ZeroDivisionError as exception:

                log.debug(exception)

        else:

            raise NotImplemented(f'__itruediv__() expects either a float or Vector ({type(other).__name__} given)!')

        return self

    def __pow__(self, power, modulo=None):
        """
        Private method that implements the power operator.

        :type power: Union[int, float]
        :type modulo: Union[int, float, None]
        :rtype: Vector
        """

        copy = self.copy()

        if isinstance(power, (int, float)):

            copy.x = copy.x ** power
            copy.y = copy.y ** power
            copy.z = copy.z ** power

        elif isinstance(power, Vector):

            copy.x = copy.x ** power.x
            copy.y = copy.y ** power.y
            copy.z = copy.z ** power.z

        else:

            return NotImplemented

        return copy

    def __xor__(self, other):
        """
        Private method that implements the bitwise operator.

        :type other: Vector
        :rtype: Vector
        """

        return self.cross(other)

    def __neg__(self):
        """
        Private method that implements the inversion operator.

        :rtype: Vector
        """

        return self.inverse()

    def __iter__(self):
        """
        Private method that returns a generator that yields data field values.

        :rtype: Iterator[float]
        """

        return iter((self.x, self.y, self.z))

    def __len__(self):
        """
        Private method that returns the number of fields belonging to this class.

        :rtype: int
        """

        return 3
    # endregion

    # region Properties
    @classproperty
    def xAxis(cls):
        """
        Getter method that returns the x-axis vector.

        :rtype: Vector
        """

        return Vector(1.0, 0.0, 0.0)

    @classproperty
    def yAxis(cls):
        """
        Getter method that returns the y-axis vector.

        :rtype: Vector
        """

        return Vector(0.0, 1.0, 0.0)

    @classproperty
    def zAxis(cls):
        """
        Getter method that returns the z-axis vector.

        :rtype: Vector
        """

        return Vector(0.0, 0.0, 1.0)

    @classproperty
    def zero(cls):
        """
        Getter method that returns the origin vector.

        :rtype: Vector
        """

        return Vector(0.0, 0.0, 0.0)

    @classproperty
    def one(cls):
        """
        Getter method that returns a one vector.

        :rtype: Vector
        """

        return Vector(1.0, 1.0, 1.0)
    # endregion

    # region Methods
    def dot(self, other):
        """
        Returns the dot product between this and the supplied vector.

        :type other: Vector
        :rtype: float
        """

        return (self.x * other.x) + (self.y * other.y) + (self.z * other.z)

    def cross(self, other):
        """
        Returns the cross product between this and the supplied vector.
        This solution uses the right hand rule!

        :type other: Vector
        :rtype: Vector
        """

        x = (self.y * other.z) - (self.z * other.y)
        y = (self.z * other.x) - (self.x * other.z)
        z = (self.x * other.y) - (self.y * other.x)

        return Vector(x, y, z)

    def distanceBetween(self, other):
        """
        Returns the distance between this and the supplied vector.

        :type other: Vector
        :rtype: float
        """

        return (other - self).length()

    def angleBetween(self, other, asDegrees=False):
        """
        Returns the angle, in radians, between this and the supplied vector.

        :type other: Vector
        :type asDegrees: bool
        :rtype: float
        """

        try:

            radian = math.acos(self.dot(other) / self.length() * other.length())

            if asDegrees:

                return math.degrees(radian)

            else:

                return radian

        except ZeroDivisionError:

            return 0.0

    def length(self):
        """
        Returns the length of this vector.

        :rtype: float
        """

        return math.sqrt(math.pow(self.x, 2.0) + math.pow(self.y, 2.0) + math.pow(self.z, 2.0))

    def normal(self):
        """
        Returns a normalized copy of this vector.

        :rtype: Vector
        """

        try:

            return self / self.length()

        except ZeroDivisionError:

            return replace(self)

    def normalize(self):
        """
        Normalizes this vector.

        :rtype: Vector
        """

        self /= self.length()
        return self

    def inverse(self):
        """
        Returns an inversed copy of this vector.

        :rtype: Vector
        """

        return self * -1.0

    def isEquivalent(self, other, tolerance=1e-3):
        """
        Evaluates if the two supplied vectors are equivalent.

        :type other: Vector
        :type tolerance: float
        :rtype: bool
        """

        return all(math.isclose(x, y, abs_tol=tolerance) for (x, y) in zip(self, other))

    def toList(self):
        """
        Converts this vector a list.

        :rtype: List[float]
        """

        return list(self)

    def toTuple(self):
        """
        Converts this vector a list.

        :rtype: Tuple[float, float, float]
        """

        return tuple(self)
    # endregion
