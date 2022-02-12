import numpy

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from dcc.abstract import afnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnTransform(with_metaclass(ABCMeta, afnnode.AFnNode)):
    """
    Overload of AFnNode used to outline a transform node interface.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Call parent method
        #
        super(AFnTransform, self).__init__(*args, **kwargs)

    @abstractmethod
    def translation(self, worldSpace=False):
        """
        Returns the translation component from the local transform matrix.

        :type worldSpace: bool
        :rtype: numpy.array
        """

        pass

    @abstractmethod
    def setTranslation(self, translation):
        """
        Returns the translation component from the local transform matrix.

        :type translation: numpy.array
        :rtype: None
        """

        pass

    @abstractmethod
    def rotation(self):
        """
        Returns the rotation component from the local transform matrix.
        These values are stored as euler angles!

        :rtype: list[float, float, float]
        """

        pass

    @abstractmethod
    def setRotation(self, rotation):
        """
        Returns the translation component from the local transform matrix.

        :type rotation: list[float, float, float]
        :rtype: None
        """

        pass

    @abstractmethod
    def scale(self):
        """
        Returns the scale component from the local transform matrix.

        :rtype: list[float, float, float]
        """

        pass

    @abstractmethod
    def setScale(self, scale):
        """
        Returns the translation component from the local transform matrix.

        :type scale: list[float, float, float]
        :rtype: None
        """

        pass

    @abstractmethod
    def boundingBox(self):
        """
        Returns the bounding box for this node.
        This consists of minimum/maximum values for each axis in local space.

        :rtype: list[float, float, float], list[float, float, float]
        """

        pass

    def centerPoint(self):
        """
        Returns the bounding box center for this transform.

        :rtype: numpy.array
        """

        minPoint, maxPoint = self.boundingBox()
        return (minPoint * 0.5) + (maxPoint * 0.5)

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

        return numpy.linalg.inv(self.matrix())

    @abstractmethod
    def setMatrix(self, matrix):
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

        return numpy.linalg.inv(self.worldMatrix())

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

        return numpy.linalg.inv(self.parentMatrix())

    def snapshot(self):
        """
        Returns a transform snapshot for all of the descendants derived from this node.

        :rtype: list[tuple[int, numpy.matrix]]
        """

        # Iterate through descendants
        #
        snapshot = []
        fnTransform = self.__class__()

        for child in self.iterDescendants():

            fnTransform.setObject(child)
            snapshot.append((fnTransform.handle(), fnTransform.worldMatrix()))

        return snapshot

    def assumeSnapshot(self, snapshot):
        """
        Reassigns the transform matrices from the supplied snapshot.

        :type snapshot: list[tuple[int, numpy.matrix]]
        :rtype: None
        """

        fnTransform = self.__class__()

        for (handle, worldMatrix) in snapshot:

            fnTransform.setObject(handle)
            parentInverseMatrix = fnTransform.parentInverseMatrix()
            matrix = worldMatrix * parentInverseMatrix

            fnTransform.setMatrix(matrix)
