import numpy

from abc import ABCMeta, abstractmethod
from six import with_metaclass

from dcc.abstract import afnnode
from dcc.math import matrixmath

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
        Returns the translation values for this node.

        :type worldSpace: bool
        :rtype: list[float, float, float]
        """

        pass

    @abstractmethod
    def setTranslation(self, translation, **kwargs):
        """
        Updates the translation values for this node.

        :type translation: list[float, float, float]
        :rtype: None
        """

        pass

    def resetTranslation(self):
        """
        Resets the translation values for this node.

        :rtype: None
        """

        self.setTranslation([0.0, 0.0, 0.0])

    @abstractmethod
    def rotationOrder(self):
        """
        Returns the rotation order for this node.

        :rtype: str
        """

        pass

    @abstractmethod
    def rotation(self):
        """
        Returns the rotation values, as euler angles, from this node.

        :rtype: list[float, float, float]
        """

        pass

    @abstractmethod
    def setRotation(self, rotation, **kwargs):
        """
        Updates the rotation values, as euler angles, for this node.

        :type rotation: list[float, float, float]
        :rtype: None
        """

        pass

    def resetRotation(self):
        """
        Resets the rotation values for this node.

        :rtype: None
        """

        self.setRotation([0.0, 0.0, 0.0])

    @abstractmethod
    def scale(self):
        """
        Returns the scale values for this node.

        :rtype: list[float, float, float]
        """

        pass

    @abstractmethod
    def setScale(self, scale, **kwargs):
        """
        Updates the scale values for this node.

        :type scale: list[float, float, float]
        :rtype: None
        """

        pass

    def resetScale(self):
        """
        Resets the scale values for this node.

        :rtype: None
        """

        self.setScale([1.0, 1.0, 1.0])

    @abstractmethod
    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of a minimum and maximum point in world space.

        :rtype: list[float, float, float], list[float, float, float]
        """

        pass

    def centerPoint(self):
        """
        Returns the bounding box center for this node.

        :rtype: numpy.array
        """

        boundingBox = self.boundingBox()
        return (numpy.array(boundingBox[0]) * 0.5) + (numpy.array(boundingBox[1]) * 0.5)

    @abstractmethod
    def matrix(self):
        """
        Returns the local transform matrix for this node.

        :rtype: numpy.matrix
        """

        pass

    def inverseMatrix(self):
        """
        Returns the local inverse matrix for this node.

        :rtype: numpy.matrix
        """

        return self.matrix().I

    @abstractmethod
    def setMatrix(self, matrix, **kwargs):
        """
        Updates the local transform matrix for this node.

        :type matrix: numpy.matrix
        :rtype: None
        """

        pass

    @abstractmethod
    def worldMatrix(self):
        """
        Returns the world matrix for this node.

        :rtype: numpy.matrix
        """

        pass

    def worldInverseMatrix(self):
        """
        Returns the world inverse matrix for this node.

        :rtype: numpy.matrix
        """

        return self.worldMatrix().I

    @abstractmethod
    def parentMatrix(self):
        """
        Returns the world parent matrix for this node.

        :rtype: numpy.matrix
        """

        pass

    def parentInverseMatrix(self):
        """
        Returns the world parent inverse matrix for this node.

        :rtype: numpy.matrix
        """

        return self.parentMatrix().I

    @abstractmethod
    def freezeTransform(self):
        """
        Freezes this transform node so all values equal zero.

        :rtype: None
        """

        pass

    def copyTransform(self, otherTransform, **kwargs):
        """
        Copies the transform matrix from the supplied node.

        :type otherTransform: Any
        :rtype: None
        """

        fnTransform = self.__class__(otherTransform)
        worldMatrix = fnTransform.worldMatrix()
        parentInverseMatrix = self.parentInverseMatrix()

        offsetMatrix = kwargs.get('offsetMatrix', matrixmath.IDENTITY_MATRIX)
        matrix = (offsetMatrix * worldMatrix) * parentInverseMatrix

        self.setMatrix(matrix, **kwargs)

    def offsetMatrix(self, otherTransform, maintainTranslate=True, maintainRotate=True, maintainScale=True):
        """
        Returns the offset matrix between the supplied transform.
        Optional keywords can be used to determine which transform component offsets are preserved.
        By default all component offsets are maintained.

        :type otherTransform: Any
        :type maintainTranslate: bool
        :type maintainRotate: bool
        :type maintainScale: bool
        :rtype: numpy.matrix
        """

        # Calculate offset matrix
        #
        fnTransform = self.__class__(otherTransform)

        worldInverseMatrix = fnTransform.worldInverseMatrix()
        offsetMatrix = self.worldMatrix() * worldInverseMatrix

        # Evaluate which transform components should be maintained
        #
        matrices = matrixmath.decomposeMatrix(offsetMatrix)

        translateMatrix = matrices[0] if maintainTranslate else matrixmath.IDENTITY_MATRIX
        rotateMatrix = matrices[1] if maintainRotate else matrixmath.IDENTITY_MATRIX
        scaleMatrix = matrices[2] if maintainScale else matrixmath.IDENTITY_MATRIX

        return scaleMatrix * rotateMatrix * translateMatrix

    def snapshot(self):
        """
        Stores a transform snapshot for all of the descendants derived from this node.

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
