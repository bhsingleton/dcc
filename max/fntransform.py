import pymxs

from enum import IntEnum
from . import fnnode
from .libs import transformutils, skinutils
from ..abstract import afntransform
from ..dataclasses import vector, eulerangles, transformationmatrix, boundingbox

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RotateOrder(IntEnum):
    """
    Enum class of all available rotation orders in 3ds-Max.
    """

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
    Overload of `AFnTransform` that implements the transform interface for 3ds-Max.
    """

    __slots__ = ()
    __rotate_order__ = RotateOrder

    def translation(self, worldSpace=False):
        """
        Returns the translation values for this node.

        :type worldSpace: bool
        :rtype: vector.Vector
        """

        if worldSpace:

            return self.worldMatrix().translation()

        else:

            translation = transformutils.getTranslation(self.object())
            return vector.Vector(translation.x, translation.y, translation.z)

    def setTranslation(self, translation, **kwargs):
        """
        Updates the translation values for this node.

        :type translation: vector.Vector
        :rtype: None
        """

        point = pymxs.runtime.Point3(translation.x, translation.y, translation.z)
        transformutils.setTranslation(self.object(), point, **kwargs)

    def rotationOrder(self):
        """
        Returns the rotation order for this node.

        :rtype: str
        """

        rotateOrder = transformutils.getRotationOrder(self.object())
        return RotateOrder(rotateOrder).name

    def eulerRotation(self):
        """
        Returns the rotation values, as euler angles, from this node.

        :rtype: List[float, float, float]
        """

        eulerAngles = transformutils.getEulerRotation(self.object())
        return eulerangles.EulerAngles(eulerAngles.x, eulerAngles.y, eulerAngles.z, order=self.rotationOrder())

    def setEulerRotation(self, eulerAngles, **kwargs):
        """
        Updates the rotation values, as euler angles, for this node.

        :type eulerAngles: List[float, float, float]
        :rtype: None
        """

        eulerAngles = pymxs.runtime.EulerAngles(float(eulerAngles[0]), float(eulerAngles[1]), float(eulerAngles[2]))
        transformutils.setEulerRotation(self.object(), eulerAngles, **kwargs)

    def scale(self):
        """
        Returns the scale values for this node.

        :rtype: vector.Vector
        """

        scale = transformutils.getScale(self.object())
        return vector.Vector(scale[0], scale[1], scale[2])

    def setScale(self, scale, **kwargs):
        """
        Updates the scale values for this node.

        :type scale: vector.Vector
        :rtype: None
        """

        point = pymxs.runtime.Point3(scale.x, scale.y, scale.z)
        transformutils.setScale(self.object(), point, **kwargs)

    def inverseScaleEnabled(self):
        """
        Evaluates if inverse scale is enabled.

        :rtype: bool
        """

        return False  # Max does not support inverse scale!

    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of a minimum and maximum point in world space.

        :rtype: boundingbox.BoundingBox
        """

        minPoint, maxPoint = transformutils.getBoundingBox(self.object())
        return boundingbox.BoundingBox(vector.Vector(*minPoint), vector.Vector(*maxPoint))

    @staticmethod
    def nativizeMatrix(matrix):
        """
        Converts a DCC agnostic matrix to the native Matrix3 class.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: pymxs.runtime.Matrix3
        """

        return pymxs.runtime.Matrix3(
            pymxs.runtime.Point3(float(matrix[0, 0]), float(matrix[0, 1]), float(matrix[0, 2])),
            pymxs.runtime.Point3(float(matrix[1, 0]), float(matrix[1, 1]), float(matrix[1, 2])),
            pymxs.runtime.Point3(float(matrix[2, 0]), float(matrix[2, 1]), float(matrix[2, 2])),
            pymxs.runtime.Point3(float(matrix[3, 0]), float(matrix[3, 1]), float(matrix[3, 2]))
        )

    @staticmethod
    def denativizeMatrix(matrix):
        """
        Converts the native Matrix3 class to a DCC agnostic matrix.

        :type matrix: pymxs.runtime.Matrix3
        :rtype: transformationmatrix.TransformationMatrix
        """

        return transformationmatrix.TransformationMatrix(
            (matrix.row1.x, matrix.row1.y, matrix.row1.z),
            (matrix.row2.x, matrix.row2.y, matrix.row2.z),
            (matrix.row3.x, matrix.row3.y, matrix.row3.z),
            (matrix.row4.x, matrix.row4.y, matrix.row4.z)
        )

    def matrix(self):
        """
        Returns the local transform matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        matrix = transformutils.getMatrix(self.object())
        return self.denativizeMatrix(matrix)

    def setMatrix(self, matrix, **kwargs):
        """
        Updates the local transform matrix for this node.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: None
        """

        matrix = self.nativizeMatrix(matrix)
        transformutils.applyTransformMatrix(self.object(), matrix)

    def bindMatrix(self):
        """
        Returns the bind matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        # Check if any skins are dependent on this transform
        #
        skins = [dependent for dependent in pymxs.runtime.refs.dependents(self.object()) if pymxs.runtime.isKindOf(dependent, pymxs.runtime.Skin)]
        numSkins = len(skins)

        if numSkins == 0:

            return transformationmatrix.TransformationMatrix()

        # Get bind-matrix from skin
        #
        skin = skins[0]
        node = pymxs.runtime.refs.dependentNode(skin, firstOnly=True)
        preBindMatrix = pymxs.runtime.skinutils.getBoneBindTM(node, self.object())

        return self.denativizeMatrix(preBindMatrix)

    def worldMatrix(self):
        """
        Returns the world matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        worldMatrix = transformutils.getWorldMatrix(self.object())
        return self.denativizeMatrix(worldMatrix)

    def parentMatrix(self):
        """
        Returns the world parent matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        parentMatrix = transformutils.getParentMatrix(self.object())
        return self.denativizeMatrix(parentMatrix)

    def freezeTransform(self):
        """
        Freezes this transform node so all values equal zero.

        :rtype: None
        """

        transformutils.freezeTransform(self.object())
