import numpy
import math
import sys

from copy import copy, deepcopy
from dcc.math import vectormath

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


TOLERANCE = sys.float_info.epsilon * 10.0
IDENTITY_MATRIX = numpy.matrix([(1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)])
INVERSE_IDENTITY_MATRIX = numpy.linalg.inv(IDENTITY_MATRIX)
DEFAULT_ROTATE_ORDER = 'xyz'


def createTranslateMatrix(value):
    """
    Creates a position matrix based on the supplied value.

    :type value: Union[list, tuple, numpy.array]
    :rtype: numpy.matrix
    """

    # Check value type
    #
    if hasattr(value, '__getitem__') and hasattr(value, '__len__'):

        # Check number of items
        #
        numItems = len(value)

        if numItems != 3:

            raise TypeError('createTranslateMatrix() expects 3 values (%s given)!' % numItems)

        # Compose matrix
        #
        return numpy.matrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (value[0], value[1], value[2], 1.0)
            ]
        )

    else:

        raise TypeError('createTranslateMatrix() expects a list (%s given)!' % type(value).__name__)


def createRotationMatrix(value, rotateOrder='xyz'):
    """
    Creates a rotation matrix based on the supplied value.
    All values are intended to be in degrees.
    Rotate order only supports xyz characters.

    :type value: Union[list, tuple, numpy.array, numpy.matrix]
    :type rotateOrder: str
    :rtype: numpy.matrix
    """

    # Check value type
    #
    if hasattr(value, '__getitem__') and hasattr(value, '__len__'):

        # Compose rotation components
        #
        rotateXMatrix = numpy.matrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, math.cos(value[0]), math.sin(value[0]), 0.0),
                (0.0, -math.sin(value[0]), math.cos(value[0]), 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

        rotateYMatrix = numpy.matrix(
            [
                (math.cos(value[1]), 0.0, -math.sin(value[1]), 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (math.sin(value[1]), 0.0, math.cos(value[1]), 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

        rotateZMatrix = numpy.matrix(
            [
                (math.cos(value[2]), math.sin(value[2]), 0.0, 0.0),
                (-math.sin(value[2]), math.cos(value[2]), 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

        # Multiply components based on rotation order
        #
        rotateMatrix = deepcopy(IDENTITY_MATRIX)
        matrices = [rotateXMatrix, rotateYMatrix, rotateZMatrix]

        for char in rotateOrder:

            index = DEFAULT_ROTATE_ORDER.index(char)
            rotateMatrix *= matrices[index]

        return rotateMatrix

    else:

        raise TypeError('createRotationMatrix() expects a list (%s given)!' % type(value).__name__)


def createScaleMatrix(value):
    """
    Creates a scale matrix from the supplied value.

    :type value: Union[list, tuple, numpy.ndarray]
    :rtype: numpy.matrix
    """

    # Check value type
    #
    if hasattr(value, '__getitem__') and hasattr(value, '__len__'):

        # Check number of items
        #
        numItems = len(value)

        if numItems != 3:

            raise TypeError('createScaleMatrix() expects 3 values (%s given)!' % numItems)

        # Compose matrix
        #
        return numpy.matrix(
            [
                (value[0], 0.0, 0.0, 0.0),
                (0.0, value[1], 0.0, 0.0),
                (0.0, 0.0, value[2], 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

    elif isinstance(value, (int, float)):

        return createScaleMatrix([value, value, value])  # Return a unit scale matrix

    else:

        raise TypeError('createScaleMatrix() expects a list (%s given)!' % type(value).__name__)


def breakMatrix(matrix, normalize=False):
    """
    Returns the axis vectors from the supplied matrix.

    :type matrix: numpy.matrix
    :type normalize: bool
    :rtype: numpy.array, numpy.array, numpy.array, numpy.array
    """

    # Check value type
    #
    if isinstance(matrix, numpy.matrix):

        # Check if vectors should be normalized
        # Don't forget matrices must be converted to arrays in order to flatten them!
        #
        array = numpy.asarray(matrix)

        x = array[0, 0:3]
        y = array[1, 0:3]
        z = array[2, 0:3]
        p = array[3, 0:3]

        if normalize:

            return vectormath.normalizeVector(x), vectormath.normalizeVector(y), vectormath.normalizeVector(z), p

        else:

            return x, y, z, p

    else:

        raise ValueError('getAxisVectors() expects a matrix (%s given)!' % type(matrix).__name__)


def decomposeTransform(matrix, rotateOrder='xyz'):
    """
    Breaks apart the matrix into its individual translate, rotate and scale components.
    A rotation order must be supplied in order to be resolved correctly.

    :type matrix: numpy.matrix
    :type rotateOrder: str
    :rtype: numpy.array, list[float, float, float], list[float, float, float]
    """

    # Check value type
    #
    if isinstance(matrix, numpy.matrix):

        translation = decomposeTranslateMatrix(matrix)
        rotation = decomposeRotateMatrix(matrix, rotateOrder=rotateOrder)
        scale = decomposeScaleMatrix(matrix)

        return translation, rotation, scale

    else:

        raise TypeError('decomposeMatrix() expects a matrix (%s given)!' % type(matrix).__name__)


def decomposeMatrix(matrix):
    """
    Breaks apart the matrix into its individual translate, rotate and scale matrices

    :type matrix: numpy.matrix
    :rtype: numpy.matrix, numpy.matrix, numpy.matrix
    """

    # Check value type
    #
    if isinstance(matrix, numpy.matrix):

        translateMatrix = createTranslateMatrix(decomposeTranslateMatrix(matrix))
        rotateMatrix = createRotationMatrix(decomposeRotateMatrix(matrix))
        scaleMatrix = createScaleMatrix(decomposeScaleMatrix(matrix))

        return translateMatrix, rotateMatrix, scaleMatrix

    else:

        raise TypeError('decomposeMatrix() expects a matrix (%s given)!' % type(matrix).__name__)


def decomposeTranslateMatrix(matrix):
    """
    Breaks the supplied transform matrix into its translate component.

    :type matrix: numpy.matrix
    :rtype: list[float, float, float]
    """

    return numpy.array([matrix[3, 0], matrix[3, 1], matrix[3, 2]])


def decomposeRotateMatrix(matrix, rotateOrder='xyz'):
    """
    Breaks the supplied transform matrix into its rotate component.
    See the following pdf for details: https://www.geometrictools.com/Documentation/EulerAngles.pdf

    :type matrix: numpy.matrix
    :type rotateOrder: str
    :rtype: list[float, float, float]
    """

    return __matrixtoeuler__[rotateOrder](matrix)


def matrixToEulerXYZ(matrix):
    """
    Converts the supplied matrix to euler XYZ angles.

    :type matrix: numpy.matrix
    :rtype: list[float, float, float]
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

    return [-math.degrees(x), -math.degrees(y), -math.degrees(z)]  # Why the inverse though???


def matrixToEulerXZY(matrix):
    """
    Converts the supplied matrix to euler XZY angles.

    :type matrix: numpy.matrix
    :rtype: list[float, float, float]
    """

    x, y, z = 0, 0, 0

    if matrix[0, 1] < 1.0:

        if matrix[0, 1] > -1.0:

            z = math.asin(-matrix[0, 2])
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

    return [math.degrees(x), math.degrees(y), math.degrees(z)]


def matrixToEulerYXZ(matrix):
    """
    Converts the supplied matrix to euler YXZ angles.

    :type matrix: numpy.matrix
    :rtype: list[float, float, float]
    """

    x, y, z = 0, 0, 0

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

    return [math.degrees(x), math.degrees(y), math.degrees(z)]


def matrixToEulerYZX(matrix):
    """
    Converts the supplied matrix to euler YZX angles.

    :type matrix: numpy.matrix
    :rtype: list[float, float, float]
    """

    x, y, z = 0, 0, 0

    if matrix[1, 0] < 1.0:

        if matrix[1, 0] > -1.0:

            x = math.asin(matrix[1, 0])
            y = math.atan2(-matrix[2, 0], matrix[0, 0])
            z = math.atan2(-matrix[1, 2], matrix[1, 1])

        else:

            x = -math.pi / 2.0
            y = -math.atan2(matrix[2, 1], matrix[2, 2])
            z = 0.0

    else:

        x = math.pi / 2.0
        y = math.atan2(matrix[2, 1], matrix[2, 2])
        z = 0.0

    return [math.degrees(x), math.degrees(y), math.degrees(z)]


def matrixToEulerZXY(matrix):
    """
    Converts the supplied matrix to euler ZXY angles.

    :type matrix: numpy.matrix
    :rtype: list[float, float, float]
    """

    x, y, z = 0, 0, 0

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

    return [math.degrees(x), math.degrees(y), math.degrees(z)]


def matrixToEulerZYX(matrix):
    """
    Converts the supplied matrix to euler XZY angles.

    :type matrix: numpy.matrix
    :rtype: list[float, float, float]
    """

    x, y, z = 0, 0, 0

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
        z = math.atan2(matrix[1, 2], matrix[1, 1])
        x = 0.0

    return [math.degrees(x), math.degrees(y), math.degrees(z)]


__matrixtoeuler__ = {
    'xyz': matrixToEulerXYZ,
    'xzy': matrixToEulerXZY,
    'yxz': matrixToEulerYXZ,
    'yzx': matrixToEulerYZX,
    'zxy': matrixToEulerZXY,
    'zyx': matrixToEulerZYX
}


def decomposeScaleMatrix(matrix):
    """
    Breaks the supplied transform matrix into its scale component.

    :type matrix: numpy.matrix
    :rtype: list[float, float, float]
    """

    return [numpy.linalg.norm(matrix[0]), numpy.linalg.norm(matrix[1]), numpy.linalg.norm(matrix[2])]


def createAimMatrix(forwardAxis, forwardVector, upAxis, upVector, origin=None, forwardAxisSign=1, upAxisSign=1):
    """
    Creates an aim matrix based on the supplied values.

    :type forwardAxis: int
    :type forwardVector: numpy.array
    :type upAxis: int
    :type upVector: numpy.array
    :type origin: numpy.array
    :type forwardAxisSign: int
    :type upAxisSign: int
    :rtype: numpy.matrix
    """

    # Check if a start point was supplied
    #
    if origin is None:

        origin = vectormath.ORIGIN

    # Check which forward axis is selected
    #
    xAxis = vectormath.X_AXIS_VECTOR
    yAxis = vectormath.Y_AXIS_VECTOR
    zAxis = vectormath.Z_AXIS_VECTOR

    if forwardAxis == 0:

        xAxis = forwardVector * forwardAxisSign

        if upAxis == 1:

            zAxis = numpy.cross(xAxis, (upVector * upAxisSign))
            yAxis = numpy.cross(zAxis, xAxis)

        elif upAxis == 2:

            yAxis = numpy.cross((upVector * upAxisSign), xAxis)
            zAxis = numpy.cross(xAxis, yAxis)

        else:

            raise TypeError('createAimMatrix() expects a unique up axis (%s given)!' % upAxis)

    elif forwardAxis == 1:

        yAxis = forwardVector * forwardAxisSign

        if upAxis == 0:

            zAxis = numpy.cross((upVector * upAxisSign), yAxis)
            xAxis = numpy.cross(yAxis, zAxis)

        elif upAxis == 2:

            xAxis = numpy.cross(yAxis, (upVector * upAxisSign))
            zAxis = numpy.cross(xAxis, yAxis)

        else:

            raise TypeError('createAimMatrix() expects a unique up axis (%s given)!' % upAxis)

    elif forwardAxis == 2:

        zAxis = forwardVector * forwardAxisSign

        if upAxis == 0:

            yAxis = numpy.cross(zAxis, (upVector * upAxisSign))
            xAxis = numpy.cross(yAxis, zAxis)

        elif upAxis == 1:

            xAxis = numpy.cross((upVector * upAxisSign), zAxis)
            yAxis = numpy.cross(zAxis, xAxis)

        else:

            raise TypeError('createAimMatrix() expects a unique up axis (%s given)!' % upAxis)

    else:

        raise TypeError('createAimMatrix() expects a valid forward axis (%s given)!' % forwardAxis)

    # Normalize axis vectors
    #
    xAxis = vectormath.normalizeVector(xAxis)
    yAxis = vectormath.normalizeVector(yAxis)
    zAxis = vectormath.normalizeVector(zAxis)

    # Compose aim matrix from axis vectors
    #
    return numpy.matrix(
        [
            (xAxis[0], xAxis[1], xAxis[2], 0.0),
            (yAxis[0], yAxis[1], yAxis[2], 0.0),
            (zAxis[0], zAxis[1], zAxis[2], 0.0),
            (origin[0], origin[1], origin[2], 1.0)
        ]
    )
