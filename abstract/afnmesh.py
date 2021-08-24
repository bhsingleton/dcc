from abc import ABCMeta, abstractmethod
from six import with_metaclass
from scipy.spatial import cKDTree

from . import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnMesh(with_metaclass(ABCMeta, afnbase.AFnBase)):

    __slots__ = ()

    @abstractmethod
    def range(self, numElements):
        """
        Returns a generator for yielding mesh elements.
        This is useful for programs that don't utilize zero-based arrays.

        :type numElements: int
        :rtype: iter
        """

        pass

    @abstractmethod
    def numVertices(self):
        """
        Returns the number of vertices in this mesh.

        :rtype: int
        """

        pass

    @abstractmethod
    def numEdges(self):
        """
        Returns the number of edges in this mesh.

        :rtype: int
        """

        pass

    @abstractmethod
    def numFaces(self):
        """
        Returns the number of faces in this mesh.

        :rtype: int
        """

        pass

    @abstractmethod
    def iterVertices(self, *args):
        """
        Returns a generator that yields vertex points.
        If no arguments are supplied then all vertices will be yielded.

        :rtype: iter
        """

        pass

    def vertices(self, *args):
        """
        Returns a list of vertex points.

        :rtype: list
        """

        return list(self.iterVertices(*args))

    @abstractmethod
    def iterFaceVertexIndices(self, *args):
        """
        Returns a generator that yields face vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: iter
        """

        pass

    @abstractmethod
    def iterFaceCenters(self, *args):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.

        :rtype: iter
        """

        pass

    def faceCenters(self, *args):
        """
        Returns a list of face centers.

        :rtype: list
        """

        return list(self.iterFaceCenters(*args))

    @abstractmethod
    def iterFaceNormals(self, *args):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.

        :rtype: iter
        """

        pass

    def faceNormals(self, *args):
        """
        Returns a list of face normals.

        :rtype: list
        """

        return list(self.iterFaceNormals(*args))

    def nearestNeighbours(self, vertexIndices):

        pass

    def projectPointOnPlane(self, vertices, normal, point):

        pass

    def closestPoints(self, points, vertexIndices=None):
        """
        Returns the vertices that are closest to the given points.
        An optional list of vertices can be used to limit the range of points considered.

        :type points: list[list[float, float, float]]
        :type vertexIndices: list[int]
        :rtype: int
        """

        # Check if vertices were supplied
        #
        if vertexIndices is None:

            vertexIndices = list(self.range(self.numVertices()))

        # Get control points
        #
        controlPoints = self.vertices(*vertexIndices)
        vertexMap = {localIndex: globalIndex for (localIndex, globalIndex) in enumerate(vertexIndices)}

        # Query point tree
        #
        tree = cKDTree(controlPoints)
        distances, indices = tree.query(points)

        return [vertexMap[x] for x in indices]

    def closestPointsOnSurface(self, points, faceIndices=None):
        """
        Returns the faces that are closest to the given points.
        An optional list of faces can be used to limit the range of surfaces considered.

        :type points: list[list[float, float, float]]
        :type faceIndices: list[int]
        :rtype: list[tuple[int, list[float, float, float]]]
        """

        # Check if face were supplied
        #
        if faceIndices is None:

            faceIndices = list(self.range(self.numFaces()))

        # Get control points
        #
        centers = self.faceCenters(*faceIndices)
        faceMap = {localIndex: globalIndex for (localIndex, globalIndex) in enumerate(faceIndices)}

        # Query point tree
        #
        tree = cKDTree(centers)
        distances, indices = tree.query(points)

        # Project points onto faces
        #
        numHits = len(indices)
        hits = [None] * numHits

        normals = self.faceNormals(*faceIndices)

        for (index, hit) in enumerate(indices):

            faceIndex = faceMap[index]
            hits[index] = faceIndex

        return hits
