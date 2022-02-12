import maya.cmds as mc
import maya.api.OpenMaya as om
import numpy

from dcc.maya import fnnode
from dcc.maya.libs import transformutils
from dcc.abstract import afntransform

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnTransform(afntransform.AFnTransform, fnnode.FnNode):
    """
    Overload of AFnTransform that implements the transform interface for Maya.
    """

    __slots__ = ()

    def translation(self, worldSpace=False):
        """
        Returns the translation component from the local transform matrix.

        :type worldSpace: bool
        :rtype: list[float, float, float]
        """

        vector = transformutils.getTranslation(self.dagPath())
        return vector.x, vector.y, vector.z

    def setTranslation(self, translation):
        """
        Returns the translation component from the local transform matrix.

        :type translation: list[float, float, float]
        :rtype: None
        """

        vector = om.MVector(translation[0], translation[1], translation[2])
        transformutils.setTranslation(self.dagPath(), vector)

    def rotation(self):
        """
        Returns the rotation component from the local transform matrix.
        These values are stored as euler angles!

        :rtype: list[float, float, float]
        """

        eulerRotation = transformutils.getEulerRotation(self.dagPath())
        return eulerRotation.x, eulerRotation.y, eulerRotation.z

    def setRotation(self, rotation):
        """
        Returns the translation component from the local transform matrix.

        :type rotation: list[float, float, float]
        :rtype: None
        """

        eulerRotation = om.MEulerRotation(*rotation)
        transformutils.setEulerRotation(self.dagPath(), eulerRotation)

    def scale(self):
        """
        Returns the scale component from the local transform matrix.

        :rtype: list[float, float, float]
        """

        return transformutils.getScale(self.dagPath())

    def setScale(self, scale):
        """
        Returns the translation component from the local transform matrix.

        :type scale: list[float, float, float]
        :rtype: None
        """

        transformutils.setScale(self.dagPath(), scale)

    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of minimum/maximum values for each axis in local space.

        :rtype: list[float, float, float], list[float, float, float]
        """

        boundingBox = transformutils.getBoundingBox(self.dagPath())
        return (boundingBox.min.x, boundingBox.min.y, boundingBox.min.z), (boundingBox.max.x, boundingBox.max.y, boundingBox.max.z)

    @staticmethod
    def mmatrixToMatrix(matrix):
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

    @staticmethod
    def matrixToMMatrix(matrix):
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

    def matrix(self):
        """
        Returns the local transform matrix for this node.

        :rtype: numpy.matrix
        """

        matrix = transformutils.getMatrix(self.dagPath())
        return self.mmatrixToMatrix(matrix)

    def setMatrix(self, matrix):
        """
        Updates the local transform matrix for this node.

        :type matrix: numpy.matrix
        :rtype: None
        """

        mmatrix = self.matrixToMMatrix(matrix)
        transformutils.setMatrix(self.dagPath(), mmatrix)

    def worldMatrix(self):
        """
        Returns the world matrix for this node.

        :rtype: numpy.matrix
        """

        worldMatrix = self.dagPath().inclusiveMatrix()
        return self.mmatrixToMatrix(worldMatrix)

    def parentMatrix(self):
        """
        Returns the world parent matrix for this node.

        :rtype: numpy.matrix
        """

        parentMatrix = self.dagPath().exclusiveMatrix()
        return self.mmatrixToMatrix(parentMatrix)
