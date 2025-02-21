from abc import ABCMeta, abstractmethod
from . import afnnode
from ..dataclasses import vector, eulerangles, transformationmatrix
from ..vendor.six import with_metaclass

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnTransform(with_metaclass(ABCMeta, afnnode.AFnNode)):
    """
    Overload of AFnNode used to outline a transform node interface.
    """

    __slots__ = ('_snapshot',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Call parent method
        #
        super(AFnTransform, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._snapshot = []

    @abstractmethod
    def translation(self, worldSpace=False):
        """
        Returns the translation values from this node.

        :type worldSpace: bool
        :rtype: vector.Vector
        """

        pass

    @abstractmethod
    def setTranslation(self, translation, **kwargs):
        """
        Updates the translation values for this node.

        :type translation: vector.Vector
        :rtype: None
        """

        pass

    def resetTranslation(self):
        """
        Resets the translation values for this node.

        :rtype: None
        """

        self.setTranslation(vector.Vector.origin)

    def translateTo(self, position):
        """
        Translates this node to the specified position.
        Unlike `setTranslation`, this method adds the translational difference to the current transform matrix.

        :type position: vector.Vector
        :rtype: None
        """

        currentPosition = self.matrix().translation()
        difference = position - currentPosition
        translation = self.translation() + difference

        self.setTranslation(translation)

    @abstractmethod
    def rotationOrder(self):
        """
        Returns the rotation order for this node.

        :rtype: str
        """

        pass

    @abstractmethod
    def eulerRotation(self):
        """
        Returns the euler rotation values from this node.

        :rtype: eulerangles.EulerAngles
        """

        pass

    @abstractmethod
    def setEulerRotation(self, eulerRotation, **kwargs):
        """
        Updates the euler rotation values for this node.

        :type eulerRotation: eulerangles.EulerAngles
        :rtype: None
        """

        pass

    def resetEulerRotation(self):
        """
        Resets the euler rotation values for this node.

        :rtype: None
        """

        self.setRotation(eulerangles.EulerAngles.identity)

    def rotateTo(self, eulerRotation):
        """
        Rotates this node to the specified orientation.
        Unlike `setEulerRotation`, this method adds the rotational difference to the current transform matrix.

        :type eulerRotation: eulerangles.EulerAngles
        :rtype: None
        """

        rotationMatrix = eulerRotation.asMatrix()
        currentMatrix = self.matrix().rotationPart()
        difference = rotationMatrix * currentMatrix.inverse()

        currentEulerRotation = self.eulerRotation()
        newRotationMatrix = difference * currentEulerRotation.asMatrix()
        newEulerRotation = newRotationMatrix.eulerRotation(order=currentEulerRotation.order)

        self.setEulerRotation(newEulerRotation)

    @abstractmethod
    def scale(self):
        """
        Returns the scale values for this node.

        :rtype: vector.Vector
        """

        pass

    @abstractmethod
    def setScale(self, scale, **kwargs):
        """
        Updates the scale values for this node.

        :type scale: vector.Vector
        :rtype: None
        """

        pass

    def resetScale(self):
        """
        Resets the scale values for this node.

        :rtype: None
        """

        self.setScale(vector.Vector.one)

    def scaleTo(self, scale):
        """
        Scales this node to the specified size.
        Unlike `setScale`, this method adds the scalar difference to the current transform matrix.

        :type scale: vector.Vector
        :rtype: None
        """

        currentScale = self.matrix().scale()
        difference = scale - currentScale
        newScale = self.scale() + difference

        self.setScale(newScale)

    @abstractmethod
    def inverseScaleEnabled(self):
        """
        Evaluates if inverse scale is enabled.

        :rtype: bool
        """

        pass

    @abstractmethod
    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of a minimum and maximum point in world space.

        :rtype: Tuple[vector.Vector, vector.Vector]
        """

        pass

    def centerPoint(self):
        """
        Returns the bounding box center for this node.

        :rtype: vector.Vector
        """

        minPoint, maxPoint = self.boundingBox()
        return (minPoint * 0.5) + (maxPoint * 0.5)

    @abstractmethod
    def matrix(self):
        """
        Returns the local transform matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        pass

    def inverseMatrix(self):
        """
        Returns the local inverse matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        return self.matrix().inverse()

    @abstractmethod
    def setMatrix(self, matrix, **kwargs):
        """
        Updates the local transform matrix for this node.

        :type matrix: transformationmatrix.TransformationMatrix
        :rtype: None
        """

        pass

    @abstractmethod
    def bindMatrix(self):
        """
        Returns the bind matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        pass

    @abstractmethod
    def worldMatrix(self):
        """
        Returns the world matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        pass

    def worldInverseMatrix(self):
        """
        Returns the world inverse matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        return self.worldMatrix().inverse()

    @abstractmethod
    def parentMatrix(self):
        """
        Returns the world parent matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        pass

    def parentInverseMatrix(self):
        """
        Returns the world parent inverse matrix for this node.

        :rtype: transformationmatrix.TransformationMatrix
        """

        return self.parentMatrix().inverse()

    @abstractmethod
    def freezeTransform(self):
        """
        Freezes this transform node so all values equal zero.

        :rtype: None
        """

        pass

    def copyTransform(self, otherNode, **kwargs):
        """
        Copies the transform matrix from the supplied node.

        :type otherNode: Any
        :rtype: None
        """

        otherNode = self.__class__(otherNode)
        worldMatrix = otherNode.worldMatrix()
        parentInverseMatrix = self.parentInverseMatrix()

        offsetMatrix = kwargs.get('offsetMatrix', transformationmatrix.TransformationMatrix())
        matrix = (offsetMatrix * worldMatrix) * parentInverseMatrix

        self.setMatrix(matrix, **kwargs)

    def offsetMatrix(self, otherTransform, maintainTranslate=True, maintainRotate=True, maintainScale=True):
        """
        Returns the offset matrix between the supplied transform.
        Optional keywords can be used to determine which transform component offsets are preserved.
        By default, all component offsets are maintained.

        :type otherTransform: Any
        :type maintainTranslate: bool
        :type maintainRotate: bool
        :type maintainScale: bool
        :rtype: transformationmatrix.TransformationMatrix
        """

        # Calculate offset matrix
        #
        fnTransform = self.__class__(otherTransform)

        worldInverseMatrix = fnTransform.worldInverseMatrix()
        offsetMatrix = self.worldMatrix() * worldInverseMatrix

        # Evaluate which transform components should be maintained
        #
        translateMatrix = offsetMatrix.translationPart() if maintainTranslate else transformationmatrix.TransformationMatrix()
        rotateMatrix = offsetMatrix.rotationPart() if maintainRotate else transformationmatrix.TransformationMatrix()
        scaleMatrix = offsetMatrix.scalePart() if maintainScale else transformationmatrix.TransformationMatrix()

        return scaleMatrix * rotateMatrix * translateMatrix

    def snapshot(self):
        """
        Stores a transform snapshot for all the descendants derived from this node.

        :rtype: None
        """

        # Iterate through descendants
        #
        del self._snapshot[:]
        fnTransform = self.__class__()

        for child in self.iterDescendants():

            fnTransform.setObject(child)
            self._snapshot.append((fnTransform.handle(), fnTransform.worldMatrix()))

    def assumeSnapshot(self):
        """
        Reassigns the transform matrices from the internal snapshot.

        :rtype: None
        """

        fnTransform = self.__class__()

        for (handle, worldMatrix) in self._snapshot:

            fnTransform.setObject(handle)
            parentInverseMatrix = fnTransform.parentInverseMatrix()
            matrix = worldMatrix * parentInverseMatrix

            fnTransform.setMatrix(matrix)
