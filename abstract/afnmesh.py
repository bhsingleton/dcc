import math
import numpy

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from six.moves import collections_abc
from enum import IntEnum
from itertools import chain
from collections import deque, namedtuple
from scipy.spatial import cKDTree

from dcc.abstract import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnMesh(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase used to outline function set behaviour for meshes.
    When dealing with indices it's encouraged to use dictionaries since there are DCCs that use one-based arrays.
    Don't shoot the messenger, shoot 3ds Max instead...
    """

    __slots__ = ()
    __facetriangles__ = {}  # Lookup optimization

    Components = IntEnum('Components', {'Unknown': -1, 'Vertex': 0, 'Edge': 1, 'Face': 2})
    Hit = namedtuple('Hit', ['hitIndex', 'hitPoint', 'hitBary'])

    def range(self, *args):
        """
        Returns a generator for yielding a range of mesh elements.
        This helps support programs that don't utilize zero-based arrays.

        :rtype: iter
        """

        # Inspect arguments
        #
        numArgs = len(args)
        start, stop, step = self.arrayIndexType, self.arrayIndexType, 1

        if numArgs == 1:

            stop = args[0] + self.arrayIndexType

        elif numArgs == 2:

            start = args[0]
            stop = args[1] + self.arrayIndexType

        elif numArgs == 3:

            start = args[0]
            stop = args[1] + self.arrayIndexType
            step = args[2]

        else:

            raise TypeError('range() expects at least 1 argument (%s given)!' % numArgs)

        return range(start, stop, step)

    def enumerate(self, elements):
        """
        Returns a generator for yielding local indices for global mesh elements.
        This helps support programs that don't utilize zero-based arrays.

        :type elements: List[int]
        :rtype: iter
        """

        numElements = len(elements)

        for i in range(numElements):

            yield (i + self.arrayIndexType), elements[i]

    @abstractmethod
    def triMesh(self):
        """
        Returns the triangulated mesh data object for this mesh.

        :rtype: object
        """

        pass

    @abstractmethod
    def selectedVertices(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
        """

        pass

    @abstractmethod
    def selectedEdges(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
        """

        pass

    @abstractmethod
    def selectedFaces(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
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

    def numTriangles(self):
        """
        Returns the number of triangles in this mesh.

        :rtype: int
        """

        return self.__class__(self.triMesh()).numFaces()

    @abstractmethod
    def iterVertices(self, *args):
        """
        Returns a generator that yields vertex points.
        If no arguments are supplied then all vertex points will be yielded.

        :rtype: iter
        """

        pass

    def vertices(self, *args):
        """
        Returns a list of vertex points.

        :rtype: list[tuple[float, float, float]]
        """

        return list(self.iterVertices(*args))

    @abstractmethod
    def iterVertexNormals(self, *args):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.

        :rtype: iter
        """

        pass

    def vertexNormals(self, *args):
        """
        Returns a list of vertex normals.

        :rtype: list[tuple[float, float, float]]
        """

        return list(self.iterVertexNormals(*args))

    @abstractmethod
    def iterFaceVertexIndices(self, *args):
        """
        Returns a generator that yields face-vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: iter
        """

        pass

    def faceVertexIndices(self, *args):
        """
        Returns a list of face-vertex indices.

        :rtype: list[int]
        """

        return list(self.iterFaceVertexIndices(*args))

    def cacheFaceTriangleIndices(self):
        """
        Returns a dictionary of face-triangle indices.

        :rtype: Dict[int, List[int]]
        """

        # Check if map has already been generated
        #
        handle = self.handle()
        faceTriangleIndices = self.__facetriangles__.get(handle, {})

        if len(faceTriangleIndices) == self.numFaces():

            return faceTriangleIndices

        # Iterate through faces
        #
        faceVertexIndices = self.faceVertexIndices()
        faceTriangleIndices = {}

        start = self.arrayIndexType

        for (faceIndex, vertexIndices) in self.enumerate(faceVertexIndices):

            # Get triangle count
            #
            faceVertexCount = len(vertexIndices)
            triangleCount = faceVertexCount - 2

            # Yield triangle range
            #
            end = start + triangleCount
            faceTriangleIndices[faceIndex] = list(range(start, end))

            # Increment start position
            #
            start += triangleCount

        # Store map and return value
        #
        self.__facetriangles__[handle] = faceTriangleIndices
        return faceTriangleIndices

    def iterFaceTriangleIndices(self, *args):
        """
        Returns a generator that yields face-triangle indices.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = self.range(self.numFaces())

        # Iterate through arguments
        #
        faceTriangleIndices = self.cacheFaceTriangleIndices()

        for arg in args:

            yield faceTriangleIndices[arg]

    def faceTriangleIndices(self, *args):
        """
        Returns a list of face-triangle indices.

        :rtype: List[List[int]]
        """

        return list(self.iterFaceTriangleIndices(*args))

    def triangleFaceIndices(self):
        """
        Returns a reverse lookup map for triangle-face indices.

        :rtype: Dict[int, int]
        """

        # Iterate through face-triangle indices
        #
        faceTriangleIndices = self.cacheFaceTriangleIndices()
        triangleFaceIndices = {}

        for (faceIndex, triangleIndices) in faceTriangleIndices.items():

            # Create reverse lookup for triangle
            #
            for triangleIndex in triangleIndices:

                triangleFaceIndices[triangleIndex] = faceIndex

        return triangleFaceIndices

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

        :rtype: Sequence[List[float, float, float]]
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

        :rtype: Sequence[List[float, float, float]]
        """

        return list(self.iterFaceNormals(*args))

    @staticmethod
    def getCentroid(points):
        """
        Returns the centroid of the given triangle.

        :type points: Sequence[List[float, float, float]]
        :rtype: List[float, float, float]
        """

        return (sum(numpy.array(points)) / len(points)).tolist()

    @abstractmethod
    def iterConnectedVertices(self, *args, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :key componentType: int
        :rtype: iter
        """

        pass

    @abstractmethod
    def iterConnectedEdges(self, *args, **kwargs):
        """
        Returns a generator that yields the connected edge elements.

        :key componentType: int
        :rtype: iter
        """

        pass

    @abstractmethod
    def iterConnectedFaces(self, *args, **kwargs):
        """
        Returns a generator that yields the connected face elements.

        :key componentType: int
        :rtype: iter
        """

        pass

    @staticmethod
    def distanceBetween(start, end):
        """
        Returns the distance between the two points.

        :type start: tuple[float, float, float]
        :type end: tuple[float, float, float]
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

    def shortestPathBetweenTwoVertices(self, startVertex, endVertex, maxIterations=20):
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

        return []

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
        if not isinstance(vertexIndices, collections_abc.MutableSequence):

            raise TypeError('mirrorVertices() expects a list (%s given)!' % type(vertexIndices).__name__)

        # Define inverse map
        # This will be used to inverse out input data
        #
        points = self.vertices(*vertexIndices)

        inverse = {x: -1 if x == axis else 1 for x in range(3)}
        mirrorPoints = [[value * inverse[index] for (index, value) in enumerate(point)] for point in points]

        # Query closest points from point tree
        # Might be worth trying to optimize this with only opposite points?
        #
        tree = cKDTree(self.vertices())
        distances, indices = tree.query(mirrorPoints, distance_upper_bound=tolerance)

        # Generate mirror map
        # Be sure to compensate for 1-based arrays!
        #
        numVertices = self.numVertices()
        return {vertexIndex: int(index + self.arrayIndexType) for (vertexIndex, index) in zip(vertexIndices, indices) if index != numVertices}

    def nearestNeighbours(self, vertexIndices):
        """
        Returns a list of the closest connected vertex indices.

        :type vertexIndices: list[int]
        :rtype: dict[int:int]
        """

        pass

    def closestVertices(self, points, vertexIndices=None):
        """
        Returns the vertices that are closest to the given points.
        An optional list of vertices can be used to limit the range of points considered.

        :type points: Sequence[List[float, float, float]]
        :type vertexIndices: List[int]
        :rtype: int
        """

        # Check if vertices were supplied
        #
        if vertexIndices is None:

            vertexIndices = list(self.range(self.numVertices()))

        # Get control points
        #
        controlPoints = self.vertices(*vertexIndices)
        vertexMap = dict(enumerate(vertexIndices))

        # Query point tree
        #
        tree = cKDTree(controlPoints)
        distances, indices = tree.query(points)

        return [vertexMap[x] for x in indices]

    def closestFaces(self, points, faceIndices=None):
        """
        Returns the faces that are closest to the given points.
        An optional list of faces can be used to limit the range of centroids considered.

        :type points: Sequence[List[float, float, float]]
        :type faceIndices: List[int]
        :rtype: int
        """

        # Check if vertices were supplied
        #
        if faceIndices is None:

            faceIndices = list(self.range(self.numFaces()))

        # Get control points
        #
        faceCenters = self.faceCenters(*faceIndices)
        faceMap = dict(enumerate(faceCenters))

        # Query point tree
        #
        tree = cKDTree(faceCenters)
        distances, indices = tree.query(points)

        return [faceMap[x] for x in indices]

    @staticmethod
    def getBarycentricCoordinates(point, triangle):
        """
        Finds the closest point on the given triangle.
        Shamelessly ripped from: http://www.geometrictools.com/Documentation/DistancePoint3Triangle3.pdf

        :type point: numpy.array
        :type triangle: numpy.array
        :rtype: list[float, float, float]
        """

        # Get edge vectors
        #
        point = point
        p0, p1, p2 = triangle

        v0 = p1 - p0
        v1 = p2 - p0
        v2 = p0 - point

        # Get dot products
        #
        a = numpy.dot(v0, v0)
        b = numpy.dot(v0, v1)
        c = numpy.dot(v1, v1)
        d = numpy.dot(v0, v2)
        e = numpy.dot(v1, v2)

        # Evaluate every triangle configuration
        #
        det = (a * c) - (b * b)
        s = (b * e) - (c * d)
        t = (b * d) - (a * e)

        if s + t <= det:

            if s < 0.0:

                if t < 0.0:  # Region 4

                    if d < 0.0:

                        s = numpy.clip(-d / a, 0.0, 1.0)
                        t = 0.0

                    else:

                        s = 0.0
                        t = numpy.clip(-e / c, 0.0, 1.0)

                else:  # Region 3

                    s = 0.0
                    t = numpy.clip(-e / c, 0.0, 1.0)

            elif t < 0:  # Region 5

                s = numpy.clip(-d / a, 0.0, 1.0)
                t = 0.0

            else:  # Region 0

                invDet = 1.0 / det
                s *= invDet
                t *= invDet

        else:

            if s < 0.0:  # Region 2

                tmp0 = b + d
                tmp1 = c + e

                if tmp1 > tmp0:  # Minimum on edge: s + t = 1.0

                    numerator = tmp1 - tmp0
                    denominator = a - 2.0 * b + c
                    s = numpy.clip(numerator / denominator, 0.0, 1.0)
                    t = 1.0 - s

                else:  # Minimum on edge: s = 0.0

                    t = numpy.clip(-e / c, 0.0, 1.0)
                    s = 0.0

            elif t < 0.0:  # Region 6

                if a + d > b + e:

                    numerator = c + e - b - d
                    denominator = a - 2 * b + c
                    s = numpy.clip(numerator / denominator, 0.0, 1.0)
                    t = 1.0 - s

                else:

                    s = numpy.clip(-e / c, 0.0, 1.0)
                    t = 0.0

            else:  # Region 1

                numerator = c + e - b - d
                denominator = a - 2 * b + c
                s = numpy.clip(numerator / denominator, 0.0, 1.0)
                t = 1.0 - s

        return float(1.0 - s - t), float(s), float(t)

    def closestPointsOnSurface(self, points, faceIndices=None):
        """
        Returns the faces that are closest to the given points.
        An optional list of faces can be used to limit the range of surfaces considered.
        The returns values are organized by: triangleIndex, hitPoint

        :type points: Sequence[List[float, float, float]]
        :type faceIndices: List[int]
        :rtype: List[AfnMesh.Hit]
        """

        # Check if faces were supplied
        #
        if faceIndices is None:

            faceIndices = list(self.range(self.numFaces()))

        # Get control points
        #
        faceTriangleIndices = self.faceTriangleIndices(*faceIndices)
        triangleIndices = list(chain(*faceTriangleIndices))
        triangleMap = dict(enumerate(triangleIndices))

        triMesh = self.__class__(self.triMesh())
        triangleCentroids = triMesh.faceCenters(*triangleIndices)

        # Get the closest triangles using point tree
        #
        tree = cKDTree(triangleCentroids)
        distances, indices = tree.query(points)

        # Project points onto closest triangles
        # Remember to use the triangle map to resolve the local indices!
        #
        closestTriangles = [triangleMap[index] for index in indices]
        triangleVertexIndices = dict(zip(closestTriangles, triMesh.faceVertexIndices(*closestTriangles)))

        numHits = len(indices)
        hits = [None] * numHits

        for (index, (triangleIndex, point)) in enumerate(zip(closestTriangles, points)):

            point = numpy.array(point)
            triangle = numpy.array(self.vertices(*triangleVertexIndices[triangleIndex]))

            baryCoords = self.getBarycentricCoordinates(point, triangle)
            closestPoint = (triangle[0] * baryCoords[0]) + (triangle[1] * baryCoords[1]) + (triangle[2] * baryCoords[2])

            log.debug('Hit: point=%s -> closestPoint=%s, bary=%s' % (point, closestPoint, baryCoords))
            hits[index] = self.Hit(hitIndex=triangleIndex, hitPoint=closestPoint, hitBary=baryCoords)

        return hits
