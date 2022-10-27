import numpy

from maya import cmds as mc
from maya.api import OpenMaya as om
from enum import IntEnum
from dcc.maya import fnnode
from dcc.maya.libs import transformutils
from dcc.abstract import afntransform

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RotateOrder(IntEnum):

    xyz = 0
    yzx = 1
    zxy = 2
    xzy = 3
    yxz = 4
    zyx = 5


class FnTransform(afntransform.AFnTransform, fnnode.FnNode):
    """
    Overload of AFnTransform that implements the transform interface for Maya.
    """

    __slots__ = ()
    __rotateorder__ = RotateOrder

    def translation(self, worldSpace=False):
        """
        Returns the translation values for this node.

        :type worldSpace: bool
        :rtype: List[float, float, float]
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        vector = transformutils.getTranslation(dagPath)

        return vector.x, vector.y, vector.z

    def setTranslation(self, translation, **kwargs):
        """
        Updates the translation values for this node.

        :type translation: List[float, float, float]
        :rtype: None
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        vector = om.MVector(translation[0], translation[1], translation[2])

        transformutils.setTranslation(dagPath, vector, **kwargs)

    def rotationOrder(self):
        """
        Returns the rotation order for this node.

        :rtype: str
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        rotateOrder = transformutils.getRotationOrder(dagPath)

        return RotateOrder(rotateOrder).name

    def rotation(self):
        """
        Returns the rotation values, as euler angles, from this node.

        :rtype: List[float, float, float]
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        eulerRotation = transformutils.getEulerRotation(self.dagPath())

        return eulerRotation.x, eulerRotation.y, eulerRotation.z

    def setRotation(self, rotation, **kwargs):
        """
        Updates the rotation values, as euler angles, for this node.

        :type rotation: List[float, float, float]
        :rtype: None
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        eulerRotation = om.MEulerRotation(*rotation)

        transformutils.setEulerRotation(dagPath, eulerRotation, **kwargs)

    def scale(self):
        """
        Returns the scale values for this node.

        :rtype: List[float, float, float]
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        return transformutils.getScale(dagPath)

    def setScale(self, scale, **kwargs):
        """
        Updates the scale values for this node.

        :type scale: List[float, float, float]
        :rtype: None
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        transformutils.setScale(dagPath, scale, **kwargs)

    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of a minimum and maximum point in world space.

        :rtype: List[float, float, float], List[float, float, float]
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        boundingBox = transformutils.getBoundingBox(dagPath)

        return (boundingBox.min.x, boundingBox.min.y, boundingBox.min.z), (boundingBox.max.x, boundingBox.max.y, boundingBox.max.z)

    @staticmethod
    def nativizeMatrix(matrix):
        """
        Converts a numpy matrix to a Matrix3 class.

        :type matrix: numpy.matrix
        :rtype: om.MMatrix
        """

        return om.MMatrix(
            [
                (matrix[0, 0], matrix[0, 1], matrix[0, 2], 0.0),
                (matrix[1, 0], matrix[1, 1], matrix[1, 2], 0.0),
                (matrix[2, 0], matrix[2, 1], matrix[2, 2], 0.0),
                (matrix[3, 0], matrix[3, 1], matrix[3, 2], 1.0),
            ]
        )

    @staticmethod
    def denativizeMatrix(matrix):
        """
        Converts a Matrix3 class to a numpy matrix.

        :type matrix: om.MMatrix
        :rtype: numpy.matrix
        """

        return numpy.matrix(
            [
                (matrix.getElement(0, 0), matrix.getElement(0, 1), matrix.getElement(0, 2), 0.0),
                (matrix.getElement(1, 0), matrix.getElement(1, 1), matrix.getElement(1, 2), 0.0),
                (matrix.getElement(2, 0), matrix.getElement(2, 1), matrix.getElement(2, 2), 0.0),
                (matrix.getElement(3, 0), matrix.getElement(3, 1), matrix.getElement(3, 2), 1.0),
            ]
        )

    def matrix(self):
        """
        Returns the local transform matrix for this node.

        :rtype: numpy.matrix
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        matrix = transformutils.getMatrix(dagPath)

        return self.denativizeMatrix(matrix)

    def worldMatrix(self):
        """
        Returns the world matrix for this node.

        :rtype: numpy.matrix
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        worldMatrix = dagPath.inclusiveMatrix()

        return self.denativizeMatrix(worldMatrix)

    def setMatrix(self, matrix, **kwargs):
        """
        Updates the local transform matrix for this node.

        :type matrix: numpy.matrix
        :rtype: None
        """

        matrix = self.nativizeMatrix(matrix)
        transformutils.applyTransformMatrix(self.object(), matrix)

    def parentMatrix(self):
        """
        Returns the world parent matrix for this node.

        :rtype: numpy.matrix
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        parentMatrix = dagPath.exclusiveMatrix()

        return self.denativizeMatrix(parentMatrix)

    def freezeTransform(self):
        """
        Freezes this transform node so all values equal zero.

        :rtype: None
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        transformutils.freezeTransform(dagPath)
