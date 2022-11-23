import math

from dataclasses import dataclass, fields, field, replace
from six import string_types, integer_types
from ..decorators.classproperty import classproperty
from . import vector, eulerangles

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class TransformationMatrix:
    """
    Data class for transformation matrices.
    """

    # region Fields
    row1: vector.Vector = field(default_factory=(lambda: vector.Vector.xAxis))
    row2: vector.Vector = field(default_factory=(lambda: vector.Vector.yAxis))
    row3: vector.Vector = field(default_factory=(lambda: vector.Vector.zAxis))
    row4: vector.Vector = field(default_factory=(lambda: vector.Vector.origin))
    # endregion

    # region Dunderscores
    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[str, int, Tuple[int, int]]
        :rtype: Union[float, vector.Vector]
        """

        if isinstance(key, string_types):

            return getattr(self, key)

        elif isinstance(key, integer_types):

            dataFields = fields(self.__class__)
            numDataFields = len(dataFields)

            if 0 <= key < numDataFields:

                return getattr(self, dataFields[key].name)

            else:

                raise IndexError('__getitem__() index is out of range!')

        elif isinstance(key, tuple):

            count = len(key)

            if count == 2:

                row, column = key
                return self[row][column]

            else:

                raise IndexError(f'__getitem__() expects 2 co-ordinates ({count} given)!')

        else:

            raise TypeError(f'__getitem__() expects either a str or int ({type(key).__name__} given)!')

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[str, int, Tuple[int, int]]
        :type value: Union[float, vector.Vector]
        :rtype: None
        """

        if isinstance(key, string_types):

            return setattr(self, key, value)

        elif isinstance(key, integer_types):

            dataFields = fields(self.__class__)
            numDataFields = len(dataFields)

            if 0 <= key < numDataFields:

                return setattr(self, dataFields[key].name, value)

            else:

                raise IndexError('__setitem__() index is out of range!')

        elif isinstance(key, tuple):

            count = len(key)

            if count == 2:

                row, column = key
                self[row][column] = value

            else:

                raise IndexError(f'__setitem__() expects 2 co-ordinates ({count} given)!')

        else:

            raise TypeError(f'__setitem__() expects either a str or int ({type(key).__name__} given)!')

    def __mul__(self, other):
        """
        Private method that implements the multiplication operator.

        :type other: TransformationMatrix
        :rtype: TransformationMatrix
        """

        matrix = self.__class__()
        numRows = len(matrix)

        for row in range(numRows):

            numColumns = len(matrix[row])

            for column in range(numColumns):

                matrix[row, column] = sum(self[row, i] * other[i, column] for i in range(numColumns))

        return matrix

    def __imul__(self, other):
        """
        Private method that implements the in-place multiplication operator.

        :type other: TransformationMatrix
        :rtype: TransformationMatrix
        """

        matrix = self * other
        self.row1 = matrix.row1
        self.row2 = matrix.row2
        self.row3 = matrix.row3
        self.row4 = matrix.row4

        return self

    def __neg__(self):
        """
        Private method that implements the invert operator.

        :rtype: TransformationMatrix
        """

        return self.inverse()

    def __iter__(self):
        """
        Private method that returns a generator that yields data field values.

        :rtype: Iterator[Vector]
        """

        for row in (self.row1, self.row2, self.row3, self.row4):

            yield row

    def __len__(self):
        """
        Private method that returns the number of fields belonging to this class.

        :rtype: int
        """

        return self.rowCount()
    # endregion

    # region Properties
    @classproperty
    def identity(cls):
        """
        Getter method that returns the identity matrix.

        :rtype: Vector
        """

        return cls(vector.Vector.xAxis, vector.Vector.yAxis, vector.Vector.zAxis, vector.Vector.origin)
    # endregion

    # region Methods
    def translation(self):
        """
        Returns the translation value from this matrix.

        :rtype: vector.Vector
        """

        return replace(self.row4)

    def setTranslation(self, translation):
        """
        Updates the translation component of this matrix.

        :type translation: vector.Vector
        :rtype: None
        """

        self.row4 = replace(translation)

    def translationPart(self):
        """
        Returns the translation component from this matrix.

        :rtype: TransformationMatrix
        """

        return self.__class__(
            vector.Vector.xAxis,
            vector.Vector.yAxis,
            vector.Vector.zAxis,
            replace(self.row4)
        )

    @classmethod
    def matrixToEulerXYZ(cls, matrix):
        """
        Converts the supplied matrix to euler XYZ angles.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        x, y, z = 0, 0, 0

        if matrix[0, 2] < 1.0:

            if matrix[0, 2] > -1.0:

                y = math.asin(matrix[0, 2])
                x = math.atan2(-matrix[1, 2], matrix[2, 2])
                z = math.atan2(-matrix[0, 1], matrix[0, 0])

            else:

                y = -math.pi / 2.0
                x = -math.atan2(matrix[1, 0], matrix[1, 1])
                z = 0.0

        else:

            y = math.pi / 2.0
            x = math.atan2(matrix[1, 0], matrix[1, 1])
            z = 0.0

        return eulerangles.EulerAngles(-x, -y, -z, order='xyz')  # Why the inverse though???

    @classmethod
    def matrixToEulerXZY(cls, matrix):
        """
        Converts the supplied matrix to euler XZY angles.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        x, z, y = 0, 0, 0

        if matrix[0, 1] < 1.0:

            if matrix[0, 1] > -1.0:

                z = math.asin(-matrix[0, 1])
                x = math.atan2(matrix[2, 1], matrix[1, 1])
                y = math.atan2(matrix[0, 2], matrix[0, 0])

            else:

                z = math.pi / 2.0
                x = -math.atan2(-matrix[2, 0], matrix[2, 2])
                y = 0.0

        else:

            z = -math.pi / 2.0
            x = math.atan2(-matrix[2, 0], matrix[2, 2])
            y = 0.0

        return eulerangles.EulerAngles(-x, -z, -y, order='xzy')

    @classmethod
    def matrixToEulerYXZ(cls, matrix):
        """
        Converts the supplied matrix to euler YXZ angles.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        y, x, z = 0, 0, 0

        if matrix[1, 2] < 1.0:

            if matrix[1, 2] > -1.0:

                x = math.asin(-matrix[1, 2])
                y = math.atan2(matrix[0, 2], matrix[2, 2])
                z = math.atan2(matrix[1, 0], matrix[1, 1])

            else:

                x = math.pi / 2.0
                y = -math.atan2(-matrix[0, 1], matrix[0, 0])
                z = 0.0

        else:

            x = -math.pi / 2.0
            y = math.atan2(-matrix[0, 1], matrix[0, 0])
            z = 0.0

        return eulerangles.EulerAngles(-y, -x, -z, order='yxz')

    @classmethod
    def matrixToEulerYZX(cls, matrix):
        """
        Converts the supplied matrix to euler YZX angles.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        y, z, x = 0, 0, 0

        if matrix[1, 0] < 1.0:

            if matrix[1, 0] > -1.0:

                z = math.asin(matrix[1, 0])
                y = math.atan2(-matrix[2, 0], matrix[0, 0])
                x = math.atan2(-matrix[1, 2], matrix[1, 1])

            else:

                z = -math.pi / 2.0
                y = -math.atan2(matrix[2, 1], matrix[2, 2])
                x = 0.0

        else:

            z = math.pi / 2.0
            y = math.atan2(matrix[2, 1], matrix[2, 2])
            x = 0.0

        return eulerangles.EulerAngles(-y, -z, -x, order='yzx')

    @classmethod
    def matrixToEulerZXY(cls, matrix):
        """
        Converts the supplied matrix to euler ZXY angles.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        z, x, y = 0, 0, 0

        if matrix[2, 1] < 1.0:

            if matrix[2, 1] > -1.0:

                x = math.asin(matrix[2, 1])
                z = math.atan2(-matrix[0, 1], matrix[1, 1])
                y = math.atan2(-matrix[2, 0], matrix[2, 2])

            else:

                x = -math.pi / 2.0
                z = -math.atan2(matrix[0, 2], matrix[0, 0])
                y = 0.0

        else:

            x = math.pi / 2.0
            z = math.atan2(matrix[0, 2], matrix[0, 0])
            y = 0.0

        return eulerangles.EulerAngles(-z, -x, -y, order='zxy')

    @classmethod
    def matrixToEulerZYX(cls, matrix):
        """
        Converts the supplied matrix to euler ZYX angles.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        z, y, x = 0, 0, 0

        if matrix[2, 0] < 1.0:

            if matrix[2, 0] > -1.0:

                y = math.asin(-matrix[2, 0])
                z = math.atan2(matrix[1, 0], matrix[0, 0])
                x = math.atan2(matrix[2, 1], matrix[2, 2])

            else:

                y = math.pi / 2.0
                z = -math.atan2(-matrix[1, 2], matrix[1, 1])
                x = 0.0

        else:

            y = -math.pi / 2.0
            z = math.atan2(-matrix[1, 2], matrix[1, 1])
            x = 0.0

        return eulerangles.EulerAngles(-z, -y, -x, order='zyx')

    def eulerRotation(self, order='xyz'):
        """
        Returns the rotation component from this matrix.

        :type order: str
        :rtype: eulerangles.EulerAngles
        """

        func = getattr(self, f'matrixToEuler{order.upper()}', None)

        if callable(func):

            return func(self)

        else:

            raise TypeError('eulerRotation() expects a valid rotation order!')

    def setEulerRotation(self, eulerAngles):
        """
        Updates the rotation component of this matrix.

        :type eulerAngles: eulerangles.EulerAngles
        :rtype: None
        """

        rotationMatrix = eulerAngles.asMatrix()
        scale = self.scale()

        self.row1 = rotationMatrix.row1 * scale.x
        self.row2 = rotationMatrix.row2 * scale.y
        self.row3 = rotationMatrix.row3 * scale.z

    def rotationPart(self):
        """
        Returns the rotation component from this matrix.

        :rtype: TransformationMatrix
        """

        return self.__class__(
            replace(self.row1),
            replace(self.row2),
            replace(self.row3),
            vector.Vector.origin
        )

    def scale(self):
        """
        Returns the scale value from this matrix.

        :rtype: vector.Vector
        """

        return vector.Vector(self.row1.length(), self.row2.length(), self.row3.length())

    def setScale(self, scale):
        """
        Updates the scale component of this matrix.

        :type scale: vector.Vector
        :rtype: None
        """

        self.row1 = self.row1.normal() * scale[0]
        self.row2 = self.row2.normal() * scale[1]
        self.row3 = self.row3.normal() * scale[2]

    def scalePart(self):
        """
        Returns the scale component from this matrix.

        :rtype: TransformationMatrix
        """

        return self.__class__(
            vector.Vector(self.row1.length(), 0.0, 0.0),
            vector.Vector(0.0, self.row2.length(), 0.0),
            vector.Vector(0.0, 0.0, self.row3.length()),
            vector.Vector.origin
        )

    def minors(self, row, column):
        """
        Returns the minors for the specified row and column.

        :type row: int
        :type column: int
        :rtype: float
        """

        pass

    def determinant(self):
        """
        Returns the determinant of this matrix.
        See the following for details: https://semath.info/src/determinant-four-by-four.html
        TODO: Simplify this code!

        :rtype: float
        """

        a11 = (self[1, 1] * self[2, 2] * self[3, 3]) + (self[1, 2] * self[2, 3] * self[3, 1]) + (self[1, 3] * self[2, 1] * self[3, 2]) - (self[1, 3] * self[2, 2] * self[3, 1]) - (self[1, 2] * self[2, 1] * self[3, 3]) - (self[1, 1] * self[2, 3] * self[3, 2])
        a21 = (self[0, 1] * self[2, 2] * self[3, 3]) + (self[0, 2] * self[2, 3] * self[3, 1]) + (self[0, 3] * self[2, 1] * self[3, 2]) - (self[0, 3] * self[2, 2] * self[3, 1]) - (self[0, 2] * self[2, 1] * self[3, 3]) - (self[0, 1] * self[2, 3] * self[3, 2])
        a31 = (self[0, 1] * self[1, 2] * self[3, 3]) + (self[0, 2] * self[1, 3] * self[3, 1]) + (self[0, 3] * self[1, 1] * self[3, 2]) - (self[0, 3] * self[1, 2] * self[3, 1]) - (self[0, 2] * self[1, 1] * self[3, 3]) - (self[0, 1] * self[1, 3] * self[3, 2])
        a41 = (self[0, 1] * self[1, 2] * self[2, 3]) + (self[0, 2] * self[1, 3] * self[2, 1]) + (self[0, 3] * self[1, 1] * self[2, 2]) - (self[0, 3] * self[1, 2] * self[2, 1]) - (self[0, 2] * self[1, 1] * self[2, 3]) - (self[0, 1] * self[1, 3] * self[2, 2])

        return a11 - a21 + a31 - a41

    def adjugate(self):
        """
        Returns the adjugate of this matrix.
        See the following for details: https://semath.info/src/inverse-cofactor-ex4.html
        TODO: Simplify this code!

        :rtype: TransformationMatrix
        """

        a11 = (self[1, 1] * self[2, 2] * self[3, 3]) + (self[1, 2] * self[2, 3] * self[3, 1]) + (self[1, 3] * self[2, 1] * self[3, 2]) - (self[1, 3] * self[2, 2] * self[3, 1]) - (self[1, 2] * self[2, 1] * self[3, 3]) - (self[1, 1] * self[2, 3] * self[3, 2])
        a12 = -(self[0, 1] * self[2, 2] * self[3, 3]) - (self[0, 2] * self[2, 3] * self[3, 1]) - (self[0, 3] * self[2, 1] * self[3, 2]) + (self[0, 3] * self[2, 2] * self[3, 1]) + (self[0, 2] * self[2, 1] * self[3, 3]) + (self[0, 1] * self[2, 3] * self[3, 2])
        a13 = (self[0, 1] * self[1, 2] * self[3, 3]) + (self[0, 2] * self[1, 3] * self[3, 1]) + (self[0, 3] * self[1, 1] * self[3, 2]) - (self[0, 3] * self[1, 2] * self[3, 1]) - (self[0, 2] * self[1, 1] * self[3, 3]) - (self[0, 1] * self[1, 3] * self[3, 2])
        a14 = -(self[0, 1] * self[1, 2] * self[2, 3]) - (self[0, 2] * self[1, 3] * self[2, 1]) - (self[0, 3] * self[1, 1] * self[2, 2]) + (self[0, 3] * self[1, 2] * self[2, 1]) + (self[0, 2] * self[1, 1] * self[2, 3]) + (self[0, 1] * self[1, 3] * self[2, 2])

        a21 = -(self[1, 0] * self[2, 2] * self[3, 3]) - (self[1, 2] * self[2, 3] * self[3, 0]) - (self[1, 3] * self[2, 0] * self[3, 2]) + (self[1, 3] * self[2, 2] * self[3, 0]) + (self[1, 2] * self[2, 0] * self[3, 3]) + (self[1, 0] * self[2, 3] * self[3, 2])
        a22 = (self[0, 0] * self[2, 2] * self[3, 3]) + (self[0, 2] * self[2, 3] * self[3, 0]) + (self[0, 3] * self[2, 0] * self[3, 2]) - (self[0, 3] * self[2, 2] * self[3, 0]) - (self[0, 2] * self[2, 0] * self[3, 3]) - (self[0, 0] * self[2, 3] * self[3, 2])
        a23 = -(self[0, 0] * self[1, 2] * self[3, 3]) - (self[0, 2] * self[1, 3] * self[3, 0]) - (self[0, 3] * self[1, 0] * self[3, 2]) + (self[0, 3] * self[1, 2] * self[3, 0]) + (self[0, 2] * self[1, 0] * self[3, 3]) + (self[0, 0] * self[1, 3] * self[3, 1])
        a24 = (self[0, 0] * self[1, 2] * self[2, 3]) + (self[0, 2] * self[1, 3] * self[2, 0]) + (self[0, 3] * self[1, 0] * self[2, 2]) - (self[0, 3] * self[1, 2] * self[2, 0]) - (self[0, 2] * self[1, 0] * self[2, 3]) - (self[0, 0] * self[1, 3] * self[2, 2])

        a31 = (self[1, 0] * self[2, 1] * self[3, 3]) + (self[1, 1] * self[2, 3] * self[3, 1]) + (self[1, 3] * self[2, 0] * self[3, 1]) - (self[1, 3] * self[2, 1] * self[3, 0]) - (self[1, 1] * self[2, 0] * self[3, 3]) - (self[1, 0] * self[2, 3] * self[3, 1])
        a32 = -(self[0, 0] * self[2, 1] * self[3, 3]) - (self[0, 2] * self[2, 3] * self[3, 0]) - (self[0, 3] * self[2, 0] * self[3, 1]) + (self[0, 3] * self[2, 1] * self[3, 0]) + (self[0, 1] * self[2, 0] * self[3, 3]) + (self[0, 0] * self[2, 3] * self[3, 1])
        a33 = (self[0, 0] * self[1, 1] * self[3, 3]) + (self[0, 1] * self[1, 3] * self[3, 0]) + (self[0, 3] * self[1, 0] * self[3, 1]) - (self[0, 3] * self[1, 1] * self[3, 0]) - (self[0, 1] * self[1, 0] * self[3, 3]) - (self[0, 0] * self[1, 3] * self[3, 1])
        a34 = -(self[0, 0] * self[1, 1] * self[2, 3]) - (self[0, 1] * self[1, 3] * self[2, 0]) - (self[0, 3] * self[1, 0] * self[2, 1]) + (self[0, 3] * self[1, 1] * self[2, 0]) + (self[0, 1] * self[1, 0] * self[2, 3]) + (self[0, 0] * self[1, 3] * self[2, 1])

        a41 = -(self[1, 0] * self[2, 1] * self[3, 2]) - (self[1, 1] * self[2, 2] * self[3, 0]) - (self[1, 2] * self[2, 0] * self[3, 1]) + (self[1, 2] * self[2, 1] * self[3, 0]) + (self[1, 1] * self[2, 0] * self[3, 2]) + (self[1, 0] * self[2, 2] * self[3, 1])
        a42 = (self[0, 0] * self[2, 1] * self[3, 2]) + (self[0, 1] * self[2, 2] * self[3, 0]) + (self[0, 2] * self[2, 0] * self[3, 1]) - (self[0, 2] * self[2, 1] * self[3, 0]) - (self[0, 1] * self[2, 0] * self[3, 2]) - (self[0, 0] * self[2, 2] * self[3, 1])
        a43 = -(self[0, 0] * self[1, 1] * self[3, 2]) - (self[0, 1] * self[1, 2] * self[3, 1]) - (self[0, 2] * self[1, 0] * self[3, 1]) + (self[0, 2] * self[1, 1] * self[3, 0]) + (self[0, 1] * self[1, 0] * self[3, 2]) + (self[0, 0] * self[1, 2] * self[3, 1])
        a44 = (self[0, 0] * self[1, 1] * self[2, 2]) + (self[0, 1] * self[1, 2] * self[2, 0]) + (self[0, 2] * self[1, 0] * self[2, 1]) - (self[0, 2] * self[1, 1] * self[2, 0]) - (self[0, 1] * self[1, 0] * self[2, 2]) - (self[0, 0] * self[1, 2] * self[2, 1])

        return self.__class__(vector.Vector(a11, a12, a13, a14), vector.Vector(a21, a22, a23, a24), vector.Vector(a31, a32, a33, a34), vector.Vector(a41, a42, a43, a44))

    def inverse(self):
        """
        Returns the inverse of this matrix.

        :rtype: TransformationMatrix
        """

        determinant = 1.0 / abs(self.determinant())

        adjugate = self.adjugate()
        adjugate[0] *= determinant
        adjugate[1] *= determinant
        adjugate[2] *= determinant
        adjugate[3] *= determinant

        return adjugate

    def rowCount(self):

        return len(fields(self.__class__))

    def columnCount(self):

        return len(self.row1)
    # endregion
