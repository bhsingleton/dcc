from maya import cmds as mc
from maya.api import OpenMaya as om
from enum import IntEnum
from dcc.maya import fnnode
from dcc.maya.libs import dagutils, transformutils, skinutils
from dcc.dataclasses import vector, eulerangles, transformationmatrix, boundingbox
from dcc.abstract import afntransform

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RotateOrder(IntEnum):
    """
    Overload if `IntEnum` that lists all available rotation orders.
    """

    xyz = 0
    yzx = 1
    zxy = 2
    xzy = 3
    yxz = 4
    zyx = 5


class FnTransform(afntransform.AFnTransform, fnnode.FnNode):
    """
    Overload of `AFnTransform` that implements the transform interface for Maya.
    """

    __slots__ = ()
    __rotate_order__ = RotateOrder

    def translation(self, worldSpace=False):
        """
        Returns the translation values for this node.

        :type worldSpace: bool
        :rtype: vector.Vector
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        space = om.MSpace.kWorld if worldSpace else om.MSpace.kTransform
        translation = transformutils.getTranslation(dagPath, space=space)

        return vector.Vector(translation.x, translation.y, translation.z)

    def setTranslation(self, translation, **kwargs):
        """
        Updates the translation values for this node.

        :type translation: vector.Vector
        :rtype: None
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        translation = om.MVector(translation.x, translation.y, translation.z)

        transformutils.setTranslation(dagPath, translation, **kwargs)

    def rotationOrder(self):
        """
        Returns the rotation order for this node.

        :rtype: str
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        rotateOrder = transformutils.getRotationOrder(dagPath)

        return RotateOrder(rotateOrder).name

    def eulerRotation(self):
        """
        Returns the rotation values, as euler angles, from this node.

        :rtype: eulerangles.EulerAngles
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        eulerRotation = transformutils.getEulerRotation(dagPath)
        order = RotateOrder(eulerRotation.order).name

        return eulerangles.EulerAngles(eulerRotation.x, eulerRotation.y, eulerRotation.z, order=order)

    def setEulerRotation(self, rotation, **kwargs):
        """
        Updates the rotation values, as euler angles, for this node.

        :type rotation: eulerangles.EulerAngles
        :rtype: None
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        eulerRotation = om.MEulerRotation(*rotation, order=RotateOrder[rotation.order].value)

        transformutils.setEulerRotation(dagPath, eulerRotation, **kwargs)

    def scale(self):
        """
        Returns the scale values for this node.

        :rtype: vector.Vector
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        scale = transformutils.getScale(dagPath)

        return vector.Vector(*scale)

    def setScale(self, scale, **kwargs):
        """
        Updates the scale values for this node.

        :type scale: vector.Vector
        :rtype: None
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        scale = om.MVector(scale.x, scale.y, scale.z)

        transformutils.setScale(dagPath, scale, **kwargs)

    def inverseScaleEnabled(self):
        """
        Evaluates if inverse scale is enabled.

        :rtype: bool
        """

        obj = self.object()

        if obj.hasFn(om.MFn.kJoint):

            return self.getAttr('segmentScaleCompensate')

        else:

            return False

    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of a minimum and maximum point in world space.

        :rtype: List[float, float, float], List[float, float, float]
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        boundingBox = transformutils.getBoundingBox(dagPath)

        return boundingbox.BoundingBox(
            vector.Vector(boundingBox.min.x, boundingBox.min.y, boundingBox.min.z),
            vector.Vector(boundingBox.max.x, boundingBox.max.y, boundingBox.max.z)
        )

    @staticmethod
    def nativizeMatrix(matrix):
        """
        Converts a DCC agnostic matrix to the native MMatrix class.

        :type matrix: transformationmatrix.TransformationMatrix
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
        Converts a MMatrix class to a DCC agnostic matrix.

        :type matrix: om.MMatrix
        :rtype: transformationmatrix.TransformationMatrix
        """

        return transformationmatrix.TransformationMatrix(
            (matrix.getElement(0, 0), matrix.getElement(0, 1), matrix.getElement(0, 2)),
            (matrix.getElement(1, 0), matrix.getElement(1, 1), matrix.getElement(1, 2)),
            (matrix.getElement(2, 0), matrix.getElement(2, 1), matrix.getElement(2, 2)),
            (matrix.getElement(3, 0), matrix.getElement(3, 1), matrix.getElement(3, 2))
        )

    def matrix(self):
        """
        Returns the local transform matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        matrix = transformutils.getMatrix(dagPath)

        return self.denativizeMatrix(matrix)

    def bindMatrix(self):
        """
        Returns the bind matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        # Check if any skins are dependent on this transform
        #
        skins = list(dagutils.dependents(self.object(), apiType=om.MFn.kSkinClusterFilter))
        numSkins = len(skins)

        if numSkins > 0:

            # Get bind-matrix from skin
            #
            skin = skins[0]
            influenceId = skinutils.getInfluenceId(skin, self.object())
            preBindMatrix = skinutils.getPreBindMatrix(skin, influenceId)

            return self.denativizeMatrix(preBindMatrix.inverse())

        else:

            # Check user-properties for skin pose
            #
            userProperties = self.userProperties()
            preBindMatrix = userProperties.get('worldSkinPose', om.MMatrix.kIdentity)

            return transformationmatrix.TransformationMatrix(preBindMatrix)

    def worldMatrix(self):
        """
        Returns the world matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        dagPath = om.MDagPath.getAPathTo(self.object())
        worldMatrix = dagPath.inclusiveMatrix()

        return self.denativizeMatrix(worldMatrix)

    def setMatrix(self, matrix, **kwargs):
        """
        Updates the local transform matrix for this node.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: None
        """

        matrix = self.nativizeMatrix(matrix)
        transformutils.applyTransformMatrix(self.object(), matrix, **kwargs)

    def parentMatrix(self):
        """
        Returns the world parent matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
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
