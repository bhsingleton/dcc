import math

from dataclasses import dataclass, fields, replace
from six import string_types, integer_types
from six.moves import collections_abc
from . import transformationmatrix, vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class EulerAngles(collections_abc.Sequence):
    """
    Data class for euler angles.
    """

    # region Fields
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    order: str = 'xyz'
    # endregion

    # region Dunderscores
    __default_order__ = 'xyz'

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

        :type other: EulerAngles
        :rtype: bool
        """

        return self.isEquivalent(other)

    def __ne__(self, other):
        """
        Private method that implements the not equal operator.

        :type other: EulerAngles
        :rtype: bool
        """

        return not self.isEquivalent(other)

    def __add__(self, other):
        """
        Private method that implements the addition operator.

        :type other: Union[int, float, EulerAngles]
        :rtype: Vector
        """

        copy = replace(self)
        copy += other

        return copy

    def __iadd__(self, other):
        """
        Private method that implements the in-place addition operator.

        :type other: Union[int, float, EulerAngles]
        :rtype: Vector
        """

        try:

            self.x += other[0]
            self.y += other[1]
            self.z += other[2]

        except (IndexError, TypeError) as exception:

            log.warning(exception)

        finally:

            return self

    def __sub__(self, other):
        """
        Private method that implements the subtraction operator.

        :type other: Union[int, float, EulerAngles]
        :rtype: Vector
        """

        copy = replace(self)
        copy -= other

        return copy

    def __isub__(self, other):
        """
        Private method that implements the in-place subtraction operator.

        :type other: Union[int, float, EulerAngles]
        :rtype: Vector
        """

        try:

            self.x -= other[0]
            self.y -= other[1]
            self.z -= other[2]

        except (IndexError, TypeError) as exception:

            log.warning(exception)

        finally:

            return self
    
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

    # region Methods
    def reorder(self, order):
        """
        Returns an alternate solution in the specified order.

        :type order: str
        :rtype: EulerAngles
        """

        return self.asMatrix().eulerRotation(order)

    def asMatrix(self):
        """
        Returns these euler angles as a rotation matrix.

        :rtype: transformationmatrix.TransformationMatrix
        """

        # Compose rotation components
        #
        rotateXMatrix = transformationmatrix.TransformationMatrix(
            [
                vector.Vector.xAxis,
                vector.Vector(0.0, math.cos(self.x), math.sin(self.x)),
                vector.Vector(0.0, -math.sin(self.x), math.cos(self.x)),
                vector.Vector.zero
            ]
        )

        rotateYMatrix = transformationmatrix.TransformationMatrix(
            [
                vector.Vector(math.cos(self.y), 0.0, -math.sin(self.y)),
                vector.Vector.yAxis,
                vector.Vector(math.sin(self.y), 0.0, math.cos(self.y)),
                vector.Vector.zero
            ]
        )

        rotateZMatrix = transformationmatrix.TransformationMatrix(
            [
                vector.Vector(math.cos(self.z), math.sin(self.z), 0.0),
                vector.Vector(-math.sin(self.z), math.cos(self.z), 0.0),
                vector.Vector.zAxis,
                vector.Vector.zero
            ]
        )

        # Multiply components based on rotation order
        #
        rotateMatrix = transformationmatrix.TransformationMatrix()
        matrices = [rotateXMatrix, rotateYMatrix, rotateZMatrix]

        for char in self.order:

            index = self.__default_order__.index(char)
            rotateMatrix *= matrices[index]

        return rotateMatrix

    def copy(self):
        """
        Returns a copy of these euler angles.

        :rtype: Vector
        """

        return replace(self)

    def isEquivalent(self, other, tolerance=1e-3):
        """
        Evaluates if the two supplied euler angles are equivalent.

        :type other: EulerAngles
        :type tolerance: float
        :rtype: bool
        """

        return self.asMatrix().isEquivalent(other.asMatrix(), tolerance=tolerance)

    def toList(self, asDegrees=False):
        """
        Converts these angles to a list.

        :type asDegrees: bool
        :rtype: List[float]
        """

        if asDegrees:

            return list(map(math.degrees, self))

        else:

            return list(self)
    # endregion
