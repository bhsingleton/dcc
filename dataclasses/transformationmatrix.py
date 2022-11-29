import math

from . import matrix, vector, eulerangles

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TransformationMatrix(matrix.Matrix):
    """
    Data class for transformation matrices.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :type args: List[list[float]]
        :key row1: vector.Vector
        :key row2: vector.Vector
        :key row3: vector.Vector
        :key row4: vector.Vector
        :rtype: None
        """

        # Call parent method
        #
        super(TransformationMatrix, self).__init__(4)

        # Assume the default identity pattern
        #
        self.identitize()

        # Inspect supplied arguments
        #
        numArgs = len(args)
        numKwargs = len(kwargs)

        if numArgs == 1:

            self.fill(args[0])

        elif numArgs > 1:

            self.fill(args)

        elif numKwargs > 0:

            row1 = kwargs.get('row1', vector.Vector.xAxis)
            row2 = kwargs.get('row2', vector.Vector.yAxis)
            row3 = kwargs.get('row3', vector.Vector.zAxis)
            row4 = kwargs.get('row4', vector.Vector.zero)

            self.fill([row1, row2, row3, row4])

        else:

            pass
    # endregion

    # region Properties
    @property
    def row1(self):
        """
        Getter method that returns the X-axis as a vector.

        :rtype: vector.Vector
        """

        return vector.Vector(*self[0, 0:3])

    @property
    def row2(self):
        """
        Getter method that returns the Y-axis as a vector.

        :rtype: vector.Vector
        """

        return vector.Vector(*self[1, 0:3])

    @property
    def row3(self):
        """
        Getter method that returns the Z-axis as a vector.

        :rtype: vector.Vector
        """

        return vector.Vector(*self[2, 0:3])

    @property
    def row4(self):
        """
        Getter method that returns the position as a vector.

        :rtype: vector.Vector
        """

        return vector.Vector(*self[3, 0:3])
    # endregion

    # region Matrix Methods
    def decompose(self, normalize=False):
        """
        Returns the x, y, z and position components from this matrix.
        An optional `normalize` flag can be passed to normalize the x, y and z axis vectors.

        :rtype: Tuple[vector.Vector, vector.Vector, vector.Vector, vector.Vector]
        """

        xAxis, yAxis, zAxis, position = self.row1, self.row2, self.row3, self.row4

        if normalize:

            return xAxis.normalize(), yAxis.normalize(), zAxis.normalize(), position

        else:

            return xAxis, yAxis, zAxis, position
    # endregion

    # region Translation Methods
    def translation(self):
        """
        Returns the translation value from this matrix.

        :rtype: vector.Vector
        """

        return self.row4

    def setTranslation(self, translation):
        """
        Updates the translation component of this matrix.

        :type translation: vector.Vector
        :rtype: None
        """

        self[3] = translation

    def translationPart(self):
        """
        Returns the translation component from this matrix.

        :rtype: TransformationMatrix
        """

        return self.__class__(
            [
                vector.Vector.xAxis,
                vector.Vector.yAxis,
                vector.Vector.zAxis,
                self.row4
            ]
        )
    # endregion

    # region Euler Rotation Methods
    @classmethod
    def matrixToEulerXYZ(cls, m):
        """
        Converts the supplied m to euler XYZ angles.

        :type m: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        x, y, z = 0, 0, 0

        if m[0, 2] < 1.0:

            if m[0, 2] > -1.0:

                y = math.asin(m[0, 2])
                x = math.atan2(-m[1, 2], m[2, 2])
                z = math.atan2(-m[0, 1], m[0, 0])

            else:

                y = -math.pi / 2.0
                x = -math.atan2(m[1, 0], m[1, 1])
                z = 0.0

        else:

            y = math.pi / 2.0
            x = math.atan2(m[1, 0], m[1, 1])
            z = 0.0

        return eulerangles.EulerAngles(-x, -y, -z, order='xyz')  # Why the inverse though???

    @classmethod
    def matrixToEulerXZY(cls, m):
        """
        Converts the supplied m to euler XZY angles.

        :type m: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        x, z, y = 0, 0, 0

        if m[0, 1] < 1.0:

            if m[0, 1] > -1.0:

                z = math.asin(-m[0, 1])
                x = math.atan2(m[2, 1], m[1, 1])
                y = math.atan2(m[0, 2], m[0, 0])

            else:

                z = math.pi / 2.0
                x = -math.atan2(-m[2, 0], m[2, 2])
                y = 0.0

        else:

            z = -math.pi / 2.0
            x = math.atan2(-m[2, 0], m[2, 2])
            y = 0.0

        return eulerangles.EulerAngles(-x, -z, -y, order='xzy')

    @classmethod
    def matrixToEulerYXZ(cls, m):
        """
        Converts the supplied m to euler YXZ angles.

        :type m: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        y, x, z = 0, 0, 0

        if m[1, 2] < 1.0:

            if m[1, 2] > -1.0:

                x = math.asin(-m[1, 2])
                y = math.atan2(m[0, 2], m[2, 2])
                z = math.atan2(m[1, 0], m[1, 1])

            else:

                x = math.pi / 2.0
                y = -math.atan2(-m[0, 1], m[0, 0])
                z = 0.0

        else:

            x = -math.pi / 2.0
            y = math.atan2(-m[0, 1], m[0, 0])
            z = 0.0

        return eulerangles.EulerAngles(-y, -x, -z, order='yxz')

    @classmethod
    def matrixToEulerYZX(cls, m):
        """
        Converts the supplied m to euler YZX angles.

        :type m: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        y, z, x = 0, 0, 0

        if m[1, 0] < 1.0:

            if m[1, 0] > -1.0:

                z = math.asin(m[1, 0])
                y = math.atan2(-m[2, 0], m[0, 0])
                x = math.atan2(-m[1, 2], m[1, 1])

            else:

                z = -math.pi / 2.0
                y = -math.atan2(m[2, 1], m[2, 2])
                x = 0.0

        else:

            z = math.pi / 2.0
            y = math.atan2(m[2, 1], m[2, 2])
            x = 0.0

        return eulerangles.EulerAngles(-y, -z, -x, order='yzx')

    @classmethod
    def matrixToEulerZXY(cls, m):
        """
        Converts the supplied m to euler ZXY angles.

        :type m: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        z, x, y = 0, 0, 0

        if m[2, 1] < 1.0:

            if m[2, 1] > -1.0:

                x = math.asin(m[2, 1])
                z = math.atan2(-m[0, 1], m[1, 1])
                y = math.atan2(-m[2, 0], m[2, 2])

            else:

                x = -math.pi / 2.0
                z = -math.atan2(m[0, 2], m[0, 0])
                y = 0.0

        else:

            x = math.pi / 2.0
            z = math.atan2(m[0, 2], m[0, 0])
            y = 0.0

        return eulerangles.EulerAngles(-z, -x, -y, order='zxy')

    @classmethod
    def matrixToEulerZYX(cls, m):
        """
        Converts the supplied m to euler ZYX angles.

        :type m: transformationmatrix.TransformationMatrix
        :rtype: EulerAngles
        """

        z, y, x = 0, 0, 0

        if m[2, 0] < 1.0:

            if m[2, 0] > -1.0:

                y = math.asin(-m[2, 0])
                z = math.atan2(m[1, 0], m[0, 0])
                x = math.atan2(m[2, 1], m[2, 2])

            else:

                y = math.pi / 2.0
                z = -math.atan2(-m[1, 2], m[1, 1])
                x = 0.0

        else:

            y = -math.pi / 2.0
            z = math.atan2(-m[1, 2], m[1, 1])
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

        self[0] = rotationMatrix.row1 * scale.x
        self[1] = rotationMatrix.row2 * scale.y
        self[2] = rotationMatrix.row3 * scale.z

    def rotationPart(self):
        """
        Returns the rotation component from this matrix.

        :rtype: TransformationMatrix
        """

        return self.__class__(
            [
                self.row1,
                self.row2,
                self.row3,
                vector.Vector.origin
            ]
        )
    # endregion

    # region Look-At Methods
    def lookAt(self, *targets, forwardVector=None, forwardAxis=0, forwardAxisSign=1, upVector=None, upAxis=1, upAxisSign=1, origin=None):
        """
        Re-orients this matrix to look-at the specified target.
        An optional point of origin can be supplied to override the current fourth row value.

        :type targets: Union[vector.Vector, List[vector.Vector]]
        :type forwardVector: Union[vector.Vector, None]
        :type forwardAxis: int
        :type forwardAxisSign: Union[int, float]
        :type upVector: Union[vector.Vector, None]
        :type upAxis: int
        :type upAxisSign: Union[int, float]
        :type origin: Union[vector.Vector, None]
        """

        # Check if axes are valid
        #
        if not (0 <= forwardAxis < 3) or not (0 <= upAxis < 3):

            raise TypeError('lookAt() expects a valid axis!')

        # Check if an origin was supplied
        #
        if origin is None:

            origin = self.row4

        # Check if a forward vector was supplied
        #
        if forwardVector is None:

            forwardVector = ((sum(targets) / len(targets)) - origin).normalize()

        # Check if an up-vector was supplied
        #
        xAxis = vector.Vector.xAxis
        yAxis = vector.Vector.yAxis
        zAxis = vector.Vector.zAxis,

        axes = (xAxis, yAxis, zAxis)

        if upVector is None:

            upVector = axes[upAxis]

        # Evaluate forward axis
        #
        if forwardAxis == 0:

            xAxis = forwardVector * forwardAxisSign

            if upAxis == 1:

                zAxis = xAxis ^ (upVector * upAxisSign)
                yAxis = zAxis ^ xAxis

            elif upAxis == 2:

                yAxis = (upVector * upAxisSign) ^ xAxis
                zAxis = xAxis ^ yAxis

            else:

                raise TypeError(f'lookAt() expects a unique up axis ({upAxis} given)!')

        elif forwardAxis == 1:

            yAxis = forwardVector * forwardAxisSign

            if upAxis == 0:

                zAxis = (upVector * upAxisSign) ^ yAxis
                xAxis = yAxis ^ zAxis

            elif upAxis == 2:

                xAxis = yAxis ^ (upVector * upAxisSign)
                zAxis = xAxis ^ yAxis

            else:

                raise TypeError(f'lookAt() expects a unique up axis ({upAxis} given)!')

        elif forwardAxis == 2:

            zAxis = forwardVector * forwardAxisSign

            if upAxis == 0:

                yAxis = zAxis ^ (upVector * upAxisSign)
                xAxis = yAxis ^ zAxis

            elif upAxis == 1:

                xAxis = (upVector * upAxisSign) ^ zAxis
                yAxis = zAxis ^ xAxis

            else:

                raise TypeError(f'lookAt() expects a unique up axis ({upAxis} given)!')

        else:

            raise TypeError(f'lookAt() expects a valid forward axis ({forwardAxis} given)!')

        # Assume aim matrix from axis vectors
        #
        return self.fill([xAxis.normalize(), yAxis.normalize(), zAxis.normalize(), origin], shape=self.shape)
    # endregion

    # region Scale Methods
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

        self[0] = self.row1.normal() * scale[0]
        self[1] = self.row2.normal() * scale[1]
        self[2] = self.row3.normal() * scale[2]

    def scalePart(self):
        """
        Returns the scale component from this matrix.

        :rtype: TransformationMatrix
        """

        return self.__class__(
            [
                vector.Vector(self.row1.length(), 0.0, 0.0),
                vector.Vector(0.0, self.row2.length(), 0.0),
                vector.Vector(0.0, 0.0, self.row3.length()),
                vector.Vector.origin
            ]
        )
    # endregion
