import math

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from enum import IntEnum
from collections import deque
from scipy.spatial import cKDTree

from . import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnMesh(with_metaclass(ABCMeta, afnbase.AFnBase)):

    __slots__ = ()

    Components = IntEnum('Components', {'Vertex': 0, 'Edge': 0, 'Face': 0})

    @abstractmethod
    def range(self, *args):
        """
        Returns a generator for yielding a range of mesh elements.
        This is useful for programs that don't utilize zero-based arrays.

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

    @abstractmethod
    def iterConnectedVertices(self, *args, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :keyword componentType: int
        :rtype: iter
        """

        pass

    @abstractmethod
    def iterConnectedEdges(self, *args, **kwargs):
        """
        Returns a generator that yields the connected edge elements.

        :keyword componentType: int
        :rtype: iter
        """

        pass

    @abstractmethod
    def iterConnectedFaces(self, *args, **kwargs):
        """
        Returns a generator that yields the connected face elements.

        :keyword componentType: int
        :rtype: iter
        """

        pass

    @staticmethod
    def distanceBetween(start, end):
        """
        Returns the distance between the two points.

        :type start: list[float, float, float]
        :type end: list[float, float, float]
        :rtype: float
        """

        return math.sqrt(sum([math.pow((y - x), 2.0) for (x, y) in zip(start, end)]))

    def distanceBetweenVertices(self, *args):
        """
        Evaluates the distance between the supplied vertices.

        :rtype: float
        """

        numArgs = len(args)
        points = self.vertices(*args)

        return sum([self.distanceBetween(points[x], points[x+1]) for x in range(numArgs - 1)])

    def shortestPathBetweenVertices(self, *args):
        """
        Returns the shortest paths between the supplied vertices.

        :type args: tuple[int]
        :rtype: list[list[int]]
        """
        # Check if we have enough arguments
        #
        numArgs = len(args)

        if numArgs < 2:

            raise TypeError('shortestPathBetweenVertices() expects at least 2 vertices (%s given)!' % numArgs)

        # Iterate through vertex pairs
        #
        return [self.shortestPathBetweenTwoVertices(args[x], args[x+1]) for x in range(numArgs - 1)]

    def shortestPathBetweenTwoVertices(self, startVertex, endVertex, maxIterations=10):
        """
        Returns the shortest path between the two vertices.
        An optional max iterations can be supplied to improve performance.

        :type startVertex: int
        :type endVertex: int
        :type maxIterations: int
        :rtype: deque[int]
        """

        # Iterate until we find a complete path
        #
        traversed = dict.fromkeys(self.range(self.numVertices()), False)
        paths = deque([[startVertex]])

        while len(paths) > 0:

            # Check if we've reached our max iterations
            #
            path = paths.popleft()

            if len(path) >= maxIterations:

                continue

            # Check if we're at the end
            #
            vertexIndex = path[-1]

            if vertexIndex == endVertex:

                return path

            # Iterate through connected vertices
            #
            for connectedVertex in self.iterConnectedVertices(vertexIndex):

                # Check if vertex has already been traversed
                # If not then append new path and mark as traversed
                #
                if not traversed[connectedVertex]:

                    paths.append(path + [connectedVertex])
                    traversed[connectedVertex] = True

                else:

                    continue

        return deque()

    def mirrorVertices(self, vertexIndices, axis=0, tolerance=1e-3):
        """
        Mirrors the supplied list of vertex indices.
        If no match is found then no key-value pair is created!

        :type vertexIndices: list[int]
        :type axis: int
        :type tolerance: float
        :rtype: dict[int:int]
        """

        # Check value type
        #
        if not isinstance(vertexIndices, (list, set, tuple)):

            raise TypeError('mirrorVertices() expects a list (%s given)!' % type(vertexIndices).__name__)

        # Define inverse map
        # This will be used to inverse out input data
        #
        inverse = {x: -1 if x == axis else 1 for x in range(3)}
        points = [[value * inverse[index] for (index, value) in enumerate(x)] for x in self.iterVertices(*vertexIndices)]

        # Query closest points from point tree
        # Might be worth trying to optimize this with only opposite points?
        #
        tree = cKDTree(self.vertices())
        distances, indices = tree.query(points, distance_upper_bound=tolerance)

        # Generate mirror map
        # Be sure to compensate for 1-based arrays!
        #
        numVertices = self.numVertices()
        return {vertexIndex: (index + self.arrayOffset) for (vertexIndex, index) in zip(vertexIndices, indices) if index != numVertices}

    def nearestNeighbours(self, vertexIndices):
        """
        Returns a list of the closest connected vertex indices.

        :type vertexIndices: list[int]
        :rtype: dict[int:int]
        """

        pass

    def projectPointOnPlane(self, vertices, normal, point):
        """
        Projects a point onto the specified plane.

        :type vertices: list[list[float, float, float]]
        :type normal: list[float, float, float]
        :type point: list[float, float, float]
        :rtype: list[float, float, float]
        """

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
