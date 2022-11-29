import math

from dataclasses import dataclass, fields, replace
from six import string_types, integer_types
from six.moves import collections_abc
from . import transformationmatrix
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Vector(collections_abc.Sequence):
    """
    Data class for 3D vectors.
    """

    # region Fields
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    # endregion

    # region Dunderscores
    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[str, int]
        :rtype: float
        """

        # Evaluate key type
        #
        if isinstance(key, string_types):

            return getattr(self, key)

        elif isinstance(key, integer_types):

            dataFields = fields(self.__class__)
            numDataFields = len(dataFields)

            if 0 <= key < numDataFields:

                return getattr(self, dataFields[key].name)

            else:

                raise IndexError('__getitem__() index is out of range!')

        else:

            raise TypeError(f'__getitem__() expects either a str or int ({type(key).__name__} given)!')

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[str, int]
        :type value: float
        :rtype: None
        """

        # Evaluate key type
        #
        if isinstance(key, string_types):

            return setattr(self, key, value)

        elif isinstance(key, integer_types):

            dataFields = fields(self.__class__)
            numDataFields = len(dataFields)

            if 0 <= key < numDataFields:

                return setattr(self, dataFields[key].name, value)

            else:

                raise IndexError('__setitem__() index is out of range!')

        else:

            raise TypeError(f'__setitem__() expects either a str or int ({type(key).__name__} given)!')

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

    def __add__(self, other):
        """
        Private method that implements the addition operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        copy = self.copy()
        copy += other

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

            raise NotImplemented(f'__iadd__() expects either a float or Vector ({type(other).__name__} given)!')

        return self

    def __sub__(self, other):
        """
        Private method that implements the subtraction operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        copy = self.copy()
        copy -= other

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

            raise NotImplemented(f'__rsub__() expects either an int or float ({type(other).__name__} given)!')

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

            raise NotImplemented(f'__isub__() expects either a float or Vector ({type(other).__name__} given)!')

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
            copy *= other

            return copy

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

            raise NotImplemented(f'__imul__() expects either a float or Vector ({type(other).__name__} given)!')

        return self

    def __truediv__(self, other):
        """
        Private method that implements the division operator.

        :type other: Union[int, float, Vector]
        :rtype: Vector
        """

        copy = self.copy()
        copy /= other

        return copy

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

    def copy(self):
        """
        Returns a copy of this vector.

        :rtype: Vector
        """

        return replace(self)

    def toList(self):
        """
        Converts this vector a list.

        :rtype: List[float]
        """

        return list(self)
    # endregion
