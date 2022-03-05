import pymxs
import numpy

from enum import IntEnum
from dcc.max import fnnode
from dcc.max.libs import transformutils
from dcc.abstract import afntransform

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RotateOrder(IntEnum):

    xyz = 1
    xzy = 2
    yzx = 3
    yxz = 4
    zxy = 5
    zyx = 6
    xyx = 7
    yzy = 8
    zxz = 9


class FnTransform(afntransform.AFnTransform, fnnode.FnNode):
    """
    Overload of AFnTransform that implements the transform interface for 3ds Max.
    """

    __slots__ = ()

    def translation(self, worldSpace=False):
        """
        Returns the translation values for this node.

        :type worldSpace: bool
        :rtype: List[float, float, float]
        """

        if worldSpace:

            worldMatrix = self.worldMatrix()
            return float(worldMatrix[3, 0]), float(worldMatrix[3, 1]), float(worldMatrix[3, 2])

        else:

            point3 = transformutils.getTranslation(self.object())
            return point3.x, point3.y, point3.z

    def setTranslation(self, translation, **kwargs):
        """
        Updates the translation values for this node.

        :type translation: List[float, float, float]
        :rtype: None
        """

        point = pymxs.runtime.Point3(float(translation[0]), float(translation[1]), float(translation[2]))
        transformutils.setTranslation(self.object(), point, **kwargs)

    def rotationOrder(self):
        """
        Returns the rotation order for this node.

        :rtype: str
        """

        rotateOrder = transformutils.getRotationOrder(self.object())
        return RotateOrder(rotateOrder).name

    def rotation(self):
        """
        Returns the rotation values, as euler angles, from this node.

        :rtype: List[float, float, float]
        """

        eulerAngles = transformutils.getEulerRotation(self.object())
        return eulerAngles.x, eulerAngles.y, eulerAngles.z

    def setRotation(self, rotation, **kwargs):
        """
        Updates the rotation values, as euler angles, for this node.

        :type rotation: List[float, float, float]
        :rtype: None
        """

        eulerAngles = pymxs.runtime.EulerAngles(float(rotation[0]), float(rotation[1]), float(rotation[2]))
        transformutils.setEulerRotation(self.object(), eulerAngles, **kwargs)

    def scale(self):
        """
        Returns the scale values for this node.

        :rtype: List[float, float, float]
        """

        return transformutils.getScale(self.object())

    def setScale(self, scale, **kwargs):
        """
        Updates the scale values for this node.

        :type scale: List[float, float, float]
        :rtype: None
        """

        point = pymxs.runtime.Point3(float(scale[0]), float(scale[1]), float(scale[2]))
        transformutils.setScale(self.object(), point, **kwargs)

    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of a minimum and maximum point in world space.

        :rtype: List[float, float, float], List[float, float, float]
        """

        minPoint, maxPoint = transformutils.getBoundingBox(self.object())
        return (minPoint.x, minPoint.y, minPoint.z), (maxPoint.x, maxPoint.y, maxPoint.z)

    @staticmethod
    def matrix3ToMatrix(matrix3):
        """
        Converts a Matrix3 class to a numpy matrix.

        :type matrix3: pymxs.runtime.Matrix3
        :rtype: numpy.matrix
        """

        return numpy.matrix(
            [
                (matrix3.row1.x, matrix3.row1.y, matrix3.row1.z, 0.0),
                (matrix3.row2.x, matrix3.row2.y, matrix3.row2.z, 0.0),
                (matrix3.row3.x, matrix3.row3.y, matrix3.row3.z, 0.0),
                (matrix3.row4.x, matrix3.row4.y, matrix3.row4.z, 1.0),
            ]
        )

    @staticmethod
    def matrixToMatrix3(matrix):
        """
        Converts a numpy matrix to a Matrix3 class.

        :type matrix: numpy.matrix
        :rtype: pymxs.runtime.Matrix3
        """

        return pymxs.runtime.Matrix3(
            pymxs.runtime.Point3(float(matrix[0, 0]), float(matrix[0, 1]), float(matrix[0, 2])),
            pymxs.runtime.Point3(float(matrix[1, 0]), float(matrix[1, 1]), float(matrix[1, 2])),
            pymxs.runtime.Point3(float(matrix[2, 0]), float(matrix[2, 1]), float(matrix[2, 2])),
            pymxs.runtime.Point3(float(matrix[3, 0]), float(matrix[3, 1]), float(matrix[3, 2]))
        )

    def matrix(self):
        """
        Returns the local transform matrix for this node.

        :rtype: numpy.matrix
        """

        matrix3 = transformutils.getMatrix(self.object())
        return self.matrix3ToMatrix(matrix3)

    def setMatrix(self, matrix, **kwargs):
        """
        Updates the local transform matrix for this node.

        :type matrix: numpy.matrix
        :rtype: None
        """

        matrix3 = self.matrixToMatrix3(matrix)
        transformutils.applyTransformMatrix(self.object(), matrix3)

    def worldMatrix(self):
        """
        Returns the world matrix for this node.

        :rtype: numpy.matrix
        """

        matrix3 = transformutils.getWorldMatrix(self.object())
        return self.matrix3ToMatrix(matrix3)

    def parentMatrix(self):
        """
        Returns the world parent matrix for this node.

        :rtype: List[List[float], List[float], List[float], List[float]]
        """

        matrix3 = transformutils.getParentMatrix(self.object())
        return self.matrix3ToMatrix(matrix3)

    def freezeTransform(self):
        """
        Freezes this transform node so all values equal zero.

        :rtype: None
        """

        transformutils.freezeTransform(self.object())
