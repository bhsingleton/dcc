import pymxs
import numpy

from dcc.max import fnnode
from dcc.math import matrixmath, vectormath
from dcc.max.libs import transformutils
from dcc.abstract import afntransform

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnTransform(afntransform.AFnTransform, fnnode.FnNode):
    """
    Overload of AFnTransform that implements the transform interface for 3ds Max.
    """

    __slots__ = ()

    def translation(self, worldSpace=False):
        """
        Returns the translation component from the local transform matrix.

        :type worldSpace: bool
        :rtype: list[float, float, float]
        """

        if worldSpace:

            worldMatrix = self.worldMatrix()
            return [worldMatrix[3, 0], worldMatrix[3, 1], worldMatrix[3, 2]]

        else:

            point3 = transformutils.getTranslation(self.object())
            return [point3.x, point3.y, point3.z]

    def setTranslation(self, translation):
        """
        Updates the translation component for the local transform matrix.

        :type translation: list[float, float, float]
        :rtype: None
        """

        transformutils.setTranslation(self.object(), pymxs.runtime.Point3(*translation))

    def rotation(self):
        """
        Returns the rotation component from the local transform matrix.
        These values are stored as euler angles!

        :rtype: list[float, float, float]
        """

        eulerAngles = transformutils.getEulerRotation(self.object())
        return [eulerAngles.x, eulerAngles.y, eulerAngles.z]

    def setRotation(self, rotation):
        """
        Updates the rotation component for the local transform matrix.

        :type rotation: list[float, float, float]
        :rtype: None
        """

        eulerAngles = pymxs.runtime.EulerAngles(rotation[0], rotation[1], rotation[2])
        transformutils.setEulerRotation(self.object(), eulerAngles)

    def scale(self):
        """
        Returns the scale component from the local transform matrix.

        :rtype: list[float, float, float]
        """

        return transformutils.getScale(self.object())

    def setScale(self, scale):
        """
        Updates the scale component for the local transform matrix.

        :type scale: list[float, float, float]
        :rtype: None
        """

        transformutils.setScale(self.object(), scale)

    def boundingBox(self):
        """
        Returns the bounding box for this node.
        The returned list consists of: minX, maxX, minY, maxY, minZ, maxZ

        :rtype: list[float, float, float], list[float, float, float]
        """

        minPoint, maxPoint = transformutils.getBoundingBox(self.object())
        return (minPoint.x, minPoint.y, minPoint.z), (maxPoint.x, maxPoint.y, maxPoint.z)

    @staticmethod
    def matrix3ToMatrix(matrix3):
        """
        Converts a Matrix3 class to a numpy matrix.

        :type matrix3: pymxs.runtime.Matrix3
        :rtype: list[list[float, float, float, float], list[float, float, float, float], list[float, float, float, float], list[float, float, float, float]]
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

    def setMatrix(self, matrix, preserveChildren=False):
        """
        Updates the local transform matrix for this node.

        :type matrix: numpy.matrix
        :type preserveChildren: bool
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

        :rtype: list[list[Any], list[Any], list[Any], list[Any]]
        """

        matrix3 = transformutils.getParentMatrix(self.object())
        return self.matrix3ToMatrix(matrix3)
