from enum import IntEnum
from . import fnnode
from ..abstract import afntransform
from ..dataclasses import vector, eulerangles, transformationmatrix, boundingbox

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RotateOrder(IntEnum):

    xyz = 0
    xzy = 1
    yxz = 2
    yzx = 3
    zxy = 4
    zyx = 5


class FnTransform(afntransform.AFnTransform, fnnode.FnNode):
    """
    Overload of `AFnTransform` that implements the transform interface for Blender.
    """

    __slots__ = ()
    __rotate_order__ = RotateOrder

    def translation(self, worldSpace=False):
        """
        Returns the translation values for this node.

        :type worldSpace: bool
        :rtype: vector.Vector
        """

        return vector.Vector.zero

    def setTranslation(self, translation, **kwargs):
        """
        Updates the translation values for this node.

        :type translation: vector.Vector
        :rtype: None
        """

        pass

    def rotationOrder(self):
        """
        Returns the rotation order for this node.

        :rtype: str
        """

        return RotateOrder.xyz

    def eulerRotation(self):
        """
        Returns the rotation values, as euler angles, from this node.

        :rtype: List[float, float, float]
        """

        return eulerangles.EulerAngles()

    def setEulerRotation(self, eulerAngles, **kwargs):
        """
        Updates the rotation values, as euler angles, for this node.

        :type eulerAngles: List[float, float, float]
        :rtype: None
        """

        pass

    def scale(self):
        """
        Returns the scale values for this node.

        :rtype: vector.Vector
        """

        return vector.Vector.one

    def setScale(self, scale, **kwargs):
        """
        Updates the scale values for this node.

        :type scale: vector.Vector
        :rtype: None
        """

        pass

    def inverseScaleEnabled(self):
        """
        Evaluates if inverse scale is enabled.

        :rtype: bool
        """

        return False

    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of a minimum and maximum point in world space.

        :rtype: boundingbox.BoundingBox
        """

        return boundingbox.BoundingBox()

    def matrix(self):
        """
        Returns the local transform matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        return transformationmatrix.TransformationMatrix()

    def setMatrix(self, matrix, **kwargs):
        """
        Updates the local transform matrix for this node.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: None
        """

        pass

    def bindMatrix(self):
        """
        Returns the bind matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        return transformationmatrix.TransformationMatrix()

    def worldMatrix(self):
        """
        Returns the world matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        return transformationmatrix.TransformationMatrix()

    def parentMatrix(self):
        """
        Returns the world parent matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        return transformationmatrix.TransformationMatrix()

    def freezeTransform(self):
        """
        Freezes this transform node so all values equal zero.

        :rtype: None
        """

        pass
