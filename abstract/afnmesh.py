from abc import ABCMeta, abstractmethod
from six import with_metaclass
from enum import IntEnum
from itertools import chain
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple
from scipy.spatial import cKDTree
from dcc.abstract import afnbase
from dcc.math import linearalgebra
from dcc.dataclasses.vector import Vector
from dcc.dataclasses.colour import Colour

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ComponentType(IntEnum):
    """
    Enum class of all the available mesh components.
    """

    Vertex = 0
    Edge = 1
    Face = 2


@dataclass
class Hit:
    """
    Data class for interfacing with face-hits.
    """

    point: Vector = field(default_factory=lambda: Vector())
    faceIndex: int = 0
    faceVertexIndices: List[int] = field(default_factory=lambda: [])
    biCoords: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    triangleIndex: int = 0
    triangleVertexIndices: List[int] = field(default_factory=lambda: [])
    baryCoords: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))


class AFnMesh(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of `AFnBase` that outlines DCC function set behaviour for meshes.
    """

    __slots__ = ()

    ComponentType = ComponentType
    Hit = Hit

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

        return enumerate(elements, start=self.arrayIndexType)

    @abstractmethod
    def triangulatedObject(self):
        """
        Returns the triangulated mesh data object for this mesh.

        :rtype: Any
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

    def numFaceVertexIndices(self, *indices):
        """
        Returns the number of face-vertex indices.

        :type indices: Union[int, List[int]]
        :rtype: int
        """

        return sum([len(faceVertexIndices) for faceVertexIndices in self.iterFaceVertexIndices(*indices)])

    def numTriangles(self):
        """
        Returns the number of triangles in this mesh.

        :rtype: int
        """

        return sum(len(x) * 3 for x in self.iterFaceTriangleIndices())

    @abstractmethod
    def selectedVertices(self):
        """
        Returns a list of selected vertex indices.

        :rtype: List[int]
        """

        pass

    @abstractmethod
    def selectedEdges(self):
        """
        Returns a list of selected edge indices.

        :rtype: List[int]
        """

        pass

    @abstractmethod
    def selectedFaces(self):
        """
        Returns a list of selected face indices.

        :rtype: List[int]
        """

        pass

    @abstractmethod
    def iterVertices(self, *indices, cls=Vector, worldSpace=False):
        """
        Returns a generator that yields vertex points.
        If no arguments are supplied then all vertex points will be yielded.

        :type cls: Callable
        :type worldSpace: bool
        :rtype: Iterator[Vector]
        """

        pass

    def getVertices(self, *indices, cls=Vector, worldSpace=False):
        """
        Returns a list of vertex points.

        :type cls: Callable
        :type worldSpace: bool
        :rtype: List[Vector]
        """

        return list(self.iterVertices(*indices, cls=cls, worldSpace=worldSpace))

    @abstractmethod
    def iterVertexNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.

        :rtype: Iterator[Vector]
        """

        pass

    def getVertexNormals(self, *indices, cls=Vector):
        """
        Returns a list of vertex normals.

        :rtype: List[Vector]
        """

        return list(self.iterVertexNormals(*indices, cls=cls))

    @abstractmethod
    def hasEdgeSmoothings(self):
        """
        Evaluates if this mesh uses edge smoothings.

        :rtype: bool
        """

        pass

    @abstractmethod
    def iterEdgeSmoothings(self, *indices):
        """
        Returns a generator that yields edge smoothings for the specified indices.

        :rtype: Iterator[bool]
        """

        pass

    def getEdgeSmoothings(self, *indices):
        """
        Returns a list of edge of smoothings for the specified indices.

        :rtype: List[bool]
        """

        return list(self.iterEdgeSmoothings(*indices))

    @abstractmethod
    def hasSmoothingGroups(self):
        """
        Evaluates if this mesh uses smoothing groups.

        :rtype: bool
        """

        pass

    @abstractmethod
    def numSmoothingGroups(self):
        """
        Returns the number of smoothing groups currently in use.

        :rtype: int
        """

        pass

    @abstractmethod
    def iterSmoothingGroups(self, *indices):
        """
        Returns a generator that yields face smoothing groups for the specified indices.

        :rtype: Iterator[int]
        """

        pass

    def getSmoothingGroups(self, *indices):
        """
        Returns a list of face smoothing groups for the specified indices.

        :rtype: List[int]
        """

        return list(self.iterSmoothingGroups(*indices))

    @abstractmethod
    def iterFaceVertexIndices(self, *indices):
        """
        Returns a generator that yields face-vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: Iterator[List[int]]
        """

        pass

    def getFaceVertexIndices(self, *indices):
        """
        Returns a list of face-vertex indices.

        :rtype: List[List[int]]
        """

        return list(self.iterFaceVertexIndices(*indices))

    @abstractmethod
    def iterFaceVertexNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields face-vertex indices for the specified faces.

        :type cls: Callable
        :rtype: Iterator[List[Vector]]
        """

        pass

    def getFaceVertexNormals(self, *indices, cls=Vector):
        """
        Returns a list of face-vertex indices for the specified faces.

        :type cls: Callable
        :rtype: List[List[Vector]]
        """

        return list(self.iterFaceVertexNormals(*indices, cls=cls))

    @abstractmethod
    def iterFaceCenters(self, *indices, cls=Vector):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.

        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        pass

    def getFaceCenters(self, *indices, cls=Vector):
        """
        Returns a list of face centers.

        :type cls: Callable
        :rtype: List[Vector]
        """

        return list(self.iterFaceCenters(*indices, cls=cls))

    @abstractmethod
    def iterFaceNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.

        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        pass

    def getFaceNormals(self, *indices, cls=Vector):
        """
        Returns a list of face normals.

        :type cls: Callable
        :rtype: List[Vector]
        """

        return list(self.iterFaceNormals(*indices, cls=cls))

    @abstractmethod
    def getFaceTriangleVertexIndices(self):
        """
        Returns a dictionary of faces and their corresponding triangle-vertex indices.

        :rtype: Dict[int, List[Tuple[int, int, int]]]
        """

        pass

    @abstractmethod
    def iterFaceMaterialIndices(self, *indices):
        """
        Returns a generator that yields face material indices.
        If no arguments are supplied then all face-material indices will be yielded.

        :rtype: Iterator[int]
        """

        pass

    def faceMaterialIndices(self, *indices):
        """
        Returns a list of face material indices.
        If no arguments are supplied then all face-material indices will be yielded.

        :rtype: List[int]
        """

        return list(self.iterFaceMaterialIndices(*indices))

    @abstractmethod
    def getAssignedMaterials(self):
        """
        Returns a list of material-texture pairs from this mesh.

        :rtype: List[Tuple[Any, str]]
        """

        pass

    @abstractmethod
    def numUVSets(self):
        """
        Returns the number of UV sets.

        :rtype: int
        """

        pass

    @abstractmethod
    def getUVSetNames(self):
        """
        Returns the UV set names.

        :rtype: List[str]
        """

        pass

    @abstractmethod
    def iterUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV vertex points from the specified UV channel.

        :type channel: int
        :rtype: iter
        """

        pass

    def getUVs(self, *indices, channel=0):
        """
        Returns a list of UV vertex points from the specified UV channel.

        :type channel: int
        :rtype: iter
        """

        return list(self.iterUVs(*indices, channel=channel))

    @abstractmethod
    def iterAssignedUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV face-vertex indices from the specified UV channel.

        :type channel: int
        :rtype: Iterator[List[int]]
        """

        pass

    def getAssignedUVs(self, *indices, channel=0):
        """
        Returns a list of UV face-vertex indices from the specified UV channel.

        :rtype: List[List[int]]
        """

        return list(self.iterAssignedUVs(*indices, channel=channel))

    @abstractmethod
    def iterTangentsAndBinormals(self, *indices, cls=Vector, channel=0):
        """
        Returns a generator that yields face-vertex tangents and binormals for the specified channel.

        :type cls: Callable
        :type channel: int
        :rtype: Iterator[List[Vector]]
        """

        pass

    def getTangentsAndBinormals(self, *indices, cls=Vector, channel=0):
        """
        Returns a list of face-vertex tangents and binormals for the specified channel.

        :type cls: Callable
        :type channel: int
        :rtype: List[List[Vector]]
        """

        return list(self.iterTangentsAndBinormals(*indices, cls=cls, channel=channel))

    @abstractmethod
    def getColorSetNames(self):
        """
        Returns a list of color set names.

        :rtype: List[str]
        """

        pass

    @abstractmethod
    def getColorSetName(self, channel):
        """
        Returns the color set name at the specified channel.

        :type channel: int
        :rtype: str
        """

        pass

    @abstractmethod
    def iterColors(self, cls=Colour, channel=0):
        """
        Returns a generator that yields index-color pairs for the specified vertex color channel.

        :type cls: Callable
        :type channel: int
        :rtype: Iterator[colour.Colour]
        """

        pass

    def getColors(self, cls=Colour, channel=0):
        """
        Returns a list of index-color pairs for the specified vertex color channel.

        :type cls: Callable
        :type channel: int
        :rtype: Iterator[colour.Colour]
        """

        return list(self.iterColors(cls=cls, channel=channel))

    @abstractmethod
    def iterFaceVertexColorIndices(self, *indices, channel=0):
        """
        Returns a generator that yields face-vertex color indices for the specified faces.

        :type channel: int
        :rtype: Iterator[List[int]]
        """

        pass

    def getFaceVertexColorIndices(self, *indices, channel=0):
        """
        Returns a generator that yields face-vertex color indices for the specified faces.

        :type channel: int
        :rtype: Iterator[List[int]]
        """

        return list(self.iterFaceVertexColorIndices(*indices, channel=channel))

    @abstractmethod
    def iterConnectedVertices(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: Iterator[int]
        """

        pass

    def getConnectedVertices(self, *indices, **kwargs):
        """
        Returns a list of connected vertex elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: List[int]
        """

        return list(self.iterConnectedVertices(*indices, **kwargs))

    @abstractmethod
    def iterConnectedEdges(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected edge elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: Iterator[int]
        """

        pass

    def getConnectedEdges(self, *indices, **kwargs):
        """
        Returns a list of connected edge elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: List[int]
        """

        return list(self.iterConnectedEdges(*indices, **kwargs))

    @abstractmethod
    def iterConnectedFaces(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected face elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: Iterator[int]
        """

        pass

    def getConnectedFaces(self, *indices, **kwargs):
        """
        Returns a list of connected face elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: List[int]
        """

        return list(self.iterConnectedFaces(*indices, **kwargs))

    def distanceBetweenVertices(self, *indices):
        """
        Evaluates the distance between the supplied vertices.

        :type indices: Union[int, List[int]]
        :rtype: float
        """

        numIndices = len(indices)
        points = self.getVertices(*indices)

        return sum([points[i].distanceBetween(points[i+1]) for i in range(numIndices - 1)])

    def shortestPathBetweenVertices(self, *indices):
        """
        Returns the shortest paths between the supplied vertices.

        :type indices: Union[int, List[int]]
        :rtype: List[List[int]]
        """

        # Check if we have enough arguments
        #
        numIndices = len(indices)

        if numIndices < 2:

            raise TypeError('shortestPathBetweenVertices() expects at least 2 vertices (%s given)!' % numIndices)

        # Iterate through vertex pairs
        #
        return [self.shortestPathBetweenTwoVertices(indices[x], indices[x + 1]) for x in range(numIndices - 1)]

    def shortestPathBetweenTwoVertices(self, startVertex, endVertex, maxIterations=20):
        """
        Returns the shortest path between the two vertices.
        An optional max iterations can be supplied to improve performance.

        :type startVertex: int
        :type endVertex: int
        :type maxIterations: int
        :rtype: deque
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

        :type vertexIndices: List[int]
        :type axis: int
        :type tolerance: float
        :rtype: Dict[int, int]
        """

        # Check value type
        #
        if not isinstance(vertexIndices, (list, tuple, set)):

            raise TypeError(f'mirrorVertices() expects a list ({type(vertexIndices).__name__} given)!')

        # Define inverse map
        # This will be used to inverse out input data
        #
        points = self.getVertices(*vertexIndices)

        inverse = {i: -1 if i == axis else 1 for i in range(3)}
        mirrorPoints = [[value * inverse[index] for (index, value) in enumerate(point)] for point in points]

        # Query the closest points from point tree
        # TODO: Might be worth trying to optimize this with only opposite points?
        #
        tree = cKDTree(self.getVertices())
        distances, closestIndices = tree.query(mirrorPoints, distance_upper_bound=tolerance)

        # Generate mirror map
        # Be sure to compensate for 1-based arrays!
        #
        numVertices = self.numVertices()
        return {vertexIndex: int(closestIndex + self.arrayIndexType) for (vertexIndex, closestIndex) in zip(vertexIndices, closestIndices) if closestIndex != numVertices}

    def nearestNeighbours(self, *indices):
        """
        Returns a list of the closest connected vertex indices.

        :type indices: Union[int, List[int]]
        :rtype: List[int]
        """

        # Iterate through vertices
        #
        numIndices = len(indices)
        neighbours = [None] * numIndices

        for (localIndex, globalIndex) in enumerate(indices):

            # Get connected points
            #
            point = self.getVertices(globalIndex)[0]

            connectedIndices = self.getConnectedVertices(globalIndex)
            connectedPoints = self.getVertices(*connectedIndices)

            # Evaluate distance between points
            #
            distances = [point.distanceBetween(otherPoint) for otherPoint in connectedPoints]
            minDistance = min(distances)

            neighbours[localIndex] = connectedIndices[distances.index(minDistance)]

        return neighbours

    def nearestVertices(self, *indices):
        """
        Returns a list of the closest vertex indices.

        :type indices: Union[int, List[int]]
        :rtype: List[int]
        """

        # Initialize point tree
        #
        otherIndices = list(set(self.range(self.numVertices())).difference(set(indices)))
        otherPoints = self.getVertices(*otherIndices)
        indexMap = dict(enumerate(otherIndices))

        tree = cKDTree(otherPoints)

        # Find the closest vertices
        #
        points = self.getVertices(*indices)
        distances, closestIndices = tree.query(points)

        return [indexMap[index] for index in closestIndices]

    def closestVertices(self, points, dataset=None):
        """
        Returns the vertices that are closest to the supplied points.
        An optional list of vertices can be used to limit the range of points considered.

        :type points: List[Vector]
        :type dataset: List[int]
        :rtype: List[int]
        """

        # Check if vertices were supplied
        #
        if dataset is None:

            dataset = list(self.range(self.numVertices()))

        # Get vertex points
        #
        vertexPoints = self.getVertices(*dataset, worldSpace=True)
        vertexMap = dict(enumerate(dataset))

        # Query point tree
        #
        tree = cKDTree(vertexPoints)
        distances, indices = tree.query(points)

        return [vertexMap[x] for x in indices]

    def getBarycentricCoordinates(self, point, triangle):
        """
        Returns the barycentric co-ordinates for the point on the supplied triangle.
        Shamelessly ripped from: http://www.geometrictools.com/Documentation/DistancePoint3Triangle3.pdf

        :type point: Vector
        :type triangle: Tuple[Vector, Vector, Vector]
        :rtype: Tuple[float, float, float]
        """

        # Get edge vectors
        #
        p0, p1, p2 = triangle

        v0 = p1 - p0
        v1 = p2 - p0
        v2 = p0 - point

        # Get dot products
        #
        a = v0 * v0
        b = v0 * v1
        c = v1 * v1
        d = v0 * v2
        e = v1 * v2

        # Evaluate every triangle configuration
        #
        det = (a * c) - (b * b)
        s = (b * e) - (c * d)
        t = (b * d) - (a * e)

        if s + t <= det:

            if s < 0.0:

                if t < 0.0:  # Region 4

                    if d < 0.0:

                        s = linearalgebra.clamp(-d / a, 0.0, 1.0)
                        t = 0.0

                    else:

                        s = 0.0
                        t = linearalgebra.clamp(-e / c, 0.0, 1.0)

                else:  # Region 3

                    s = 0.0
                    t = linearalgebra.clamp(-e / c, 0.0, 1.0)

            elif t < 0:  # Region 5

                s = linearalgebra.clamp(-d / a, 0.0, 1.0)
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
                    s = linearalgebra.clamp(numerator / denominator, 0.0, 1.0)
                    t = 1.0 - s

                else:  # Minimum on edge: s = 0.0

                    t = linearalgebra.clamp(-e / c, 0.0, 1.0)
                    s = 0.0

            elif t < 0.0:  # Region 6

                if a + d > b + e:

                    numerator = c + e - b - d
                    denominator = a - 2 * b + c
                    s = linearalgebra.clamp(numerator / denominator, 0.0, 1.0)
                    t = 1.0 - s

                else:

                    s = linearalgebra.clamp(-e / c, 0.0, 1.0)
                    t = 0.0

            else:  # Region 1

                numerator = c + e - b - d
                denominator = a - 2 * b + c
                s = linearalgebra.clamp(numerator / denominator, 0.0, 1.0)
                t = 1.0 - s

        return float(1.0 - s - t), float(s), float(t)

    def getBilinearCoordinates(self, point, faceIndex):
        """
        Returns the bilinear co-ordinates for the point on the specified face.
        Shamelessly ripped from: https://math.stackexchange.com/questions/13404/mapping-irregular-quadrilateral-to-a-rectangle

        :type point: Vector
        :type faceIndex: int
        :rtype: Tuple[float, float]
        """

        # Get tangent vectors
        #
        faceVertexIndices = self.getFaceVertexIndices(faceIndex)[0]
        p0, p1, p2, p3 = self.getVertices(*faceVertexIndices, worldSpace=True)
        n = self.getFaceNormals(faceIndex)[0]

        n0 = ((p3 - p0) ^ n).normal()
        n1 = (n ^ (p1 - p0)).normal()
        n2 = (n ^ (p2 - p1)).normal()
        n3 = ((p2 - p3) ^ n).normal()

        # Calculate bi-linear co-ordinates
        #
        u = ((point - p0) * n0) / (((point - p0) * n0) + ((point - p2) * n2))
        v = ((point - p0) * n1) / (((point - p0) * n1) + ((point - p3) * n3))

        return u, v

    def closestPointOnSurface(self, *points, dataset=None):
        """
        Returns the faces that are closest to the given points.
        An optional list of faces can be used to limit the range of surfaces considered.

        :type points: Union[Vector, List[Vector]]
        :type dataset: List[int]
        :rtype: List[AFnMesh.Hit]
        """

        # Check if faces were supplied
        #
        if dataset is None:

            dataset = list(self.range(self.numFaces()))

        # Get control points
        #
        faceTriangleVertexIndices = self.getFaceTriangleVertexIndices()

        triangleIndices = list(chain(*[[(faceIndex, triangleIndex) for triangleIndex in range(len(faceTriangleVertexIndices[faceIndex]))] for faceIndex in dataset]))
        triangleMap = dict(enumerate(triangleIndices))

        triangles = [faceTriangleVertexIndices[faceIndex][triangleIndex] for (faceIndex, triangleIndex) in triangleIndices]
        trianglePoints = [self.getVertices(*vertexIndices, worldSpace=True) for vertexIndices in triangles]
        triangleCentroids = [sum(vertexPoints) / len(vertexPoints) for vertexPoints in trianglePoints]

        # Get the closest triangles using point tree
        #
        tree = cKDTree(triangleCentroids)
        distances, closestIndices = tree.query(points)

        # Project points onto the closest triangles
        # Remember to use the triangle map to resolve the local indices!
        #
        numHits = len(closestIndices)
        hits = [None] * numHits

        for (i, (closestIndex, point)) in enumerate(zip(closestIndices, points)):

            point = Vector(*point)
            faceIndex, triangleIndex = triangleMap[closestIndex]
            faceVertexIndices = self.getFaceVertexIndices(faceIndex)[0]
            triangleVertexIndices = triangles[closestIndex]

            vertexPoints = trianglePoints[closestIndex]
            baryCoords = self.getBarycentricCoordinates(point, vertexPoints)
            closestPoint = (vertexPoints[0] * baryCoords[0]) + (vertexPoints[1] * baryCoords[1]) + (vertexPoints[2] * baryCoords[2])
            biCoords = self.getBilinearCoordinates(closestPoint, faceIndex) if len(faceVertexIndices) == 4 else None

            log.debug('Hit: point=%s -> closestPoint=%s, bary=%s' % (point, closestPoint, baryCoords))
            hits[i] = self.Hit(
                point=closestPoint,
                faceIndex=faceIndex,
                faceVertexIndices=faceVertexIndices,
                biCoords=biCoords,
                triangleIndex=triangleIndex,
                triangleVertexIndices=triangleVertexIndices,
                baryCoords=baryCoords
            )

        return hits
