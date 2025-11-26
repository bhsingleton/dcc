from . import fnnode
from ..abstract import afnmesh
from ..dataclasses.vector import Vector
from ..dataclasses.colour import Colour

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(fnnode.FnNode, afnmesh.AFnMesh):
    """
    Overload of AFnMesh that implements the mesh interface for Blender.
    """

    __slots__ = ()

    def triangulatedObject(self):
        """
        Returns the triangulated mesh data object for this mesh.

        :rtype: pymxs.MXSWrapperBase
        """

        return

    def numVertices(self):
        """
        Returns the number of vertices in this mesh.

        :rtype: int
        """

        return 0

    def numEdges(self):
        """
        Returns the number of edges in this mesh.

        :rtype: int
        """

        return 0

    def numFaces(self):
        """
        Returns the number of faces in this mesh.

        :rtype: int
        """

        return 0

    def selectedVertices(self):
        """
        Returns a list of selected vertex indices.

        :rtype: List[int]
        """

        return []

    def selectedEdges(self):
        """
        Returns a list of selected edge indices.

        :rtype: List[int]
        """

        return []

    def selectedFaces(self):
        """
        Returns a list of selected face indices.

        :rtype: List[int]
        """

        return []

    def iterVertices(self, *indices, cls=Vector, worldSpace=False):
        """
        Returns a generator that yields vertex points.
        If no arguments are supplied then all vertex points will be yielded.

        :type cls: Callable
        :type worldSpace: bool
        :rtype: Iterator[Vector]
        """

        return iter([])

    def setVertex(self, index, point):
        """
        Updates the vertex position at the specified zero-based index.

        :type index: int
        :type point: Union[Vector, Tuple[float, float, float]]
        :rtype: None
        """

        pass

    def iterVertexNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.

        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        return iter([])

    def hasEdgeSmoothings(self):
        """
        Evaluates if this mesh uses edge smoothings.

        :rtype: bool
        """

        return False

    def iterEdgeSmoothings(self, *indices):
        """
        Returns a generator that yields edge smoothings.

        :rtype: Iterator[bool]
        """

        return iter([])

    def hasSmoothingGroups(self):
        """
        Evaluates if this mesh uses smoothing groups.

        :rtype: bool
        """

        return False

    def numSmoothingGroups(self):
        """
        Returns the number of smoothing groups currently in use.

        :rtype: int
        """

        return 0

    def iterSmoothingGroups(self, *indices):
        """
        Returns a generator that yields face smoothing groups.

        :rtype: Iterator[int]
        """

        return iter([])

    def iterFaceVertexIndices(self, *indices):
        """
        Returns a generator that yields face vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: Iterator[List[int]]
        """

        return iter([])

    def iterFaceVertexNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields face-vertex indices for the specified faces.

        :type cls: Callable
        :rtype: Iterator[List[Vector]]
        """

        return iter([])

    def iterFaceCenters(self, *indices, cls=Vector):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.

        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        return iter([])

    def iterFaceNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.

        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        return iter([])

    def getFaceTriangleVertexIndices(self):
        """
        Returns a dictionary of faces and their corresponding triangle-vertex indices.

        :rtype: Dict[int, List[Tuple[int, int, int]]]
        """

        return {}

    def iterFaceMaterialIndices(self, *indices):
        """
        Returns a generator that yields face material indices.
        If no arguments are supplied then all face-material indices will be yielded.

        :rtype: iter
        """

        return iter([])

    def getAssignedMaterials(self):
        """
        Returns a list of material-texture pairs from this mesh.

        :rtype: List[Tuple[Any, str]]
        """

        return []

    def numUVSets(self):
        """
        Returns the number of UV sets.

        :rtype: int
        """

        return 0

    def getUVSetNames(self):
        """
        Returns the UV set names.

        :rtype: List[str]
        """

        return []

    def iterUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV vertex points from the specified set.

        :type indices: Union[int, List[int]]
        :type channel: int
        :rtype: iter
        """

        return iter([])

    def iterAssignedUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV face-vertex indices from the specified set.

        :type indices: Union[int, List[int]]
        :type channel: int
        :rtype: iter
        """

        return iter([])

    def iterTangentsAndBinormals(self, *indices, cls=Vector, channel=0):
        """
        Returns a generator that yields face-vertex tangents and binormals for the specified channel.

        :type indices: Union[int, List[int]]
        :type cls: Callable
        :type channel: int
        :rtype: Iterator[List[Vector], List[Vector]]
        """

        return iter([])

    def getColorSetNames(self):
        """
        Returns a list of color set names.

        :rtype: List[str]
        """

        []

    def getColorSetName(self, channel):
        """
        Returns the color set name at the specified channel.

        :type channel: int
        :rtype: str
        """

        return ''

    def iterColors(self, cls=Colour, channel=0):
        """
        Returns a generator that yields index-color pairs for the specified vertex color channel.

        :type cls: Callable
        :type channel: int
        :rtype: Iterator[Colour]
        """

        return iter([])

    def iterFaceVertexColorIndices(self, *indices, channel=0):
        """
        Returns a generator that yields face-vertex color indices for the specified faces.

        :type channel: int
        :rtype: Iterator[List[int]]
        """

        return iter([])

    def iterConnectedVertices(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :key componentType: int
        :rtype: iter
        """

        return iter([])

    def iterConnectedEdges(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected edge elements.

        :key componentType: int
        :rtype: iter
        """

        return iter([])

    def iterConnectedFaces(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected face elements.

        :key componentType: int
        :rtype: iter
        """

        return iter([])

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields mesh instances.

        :rtype: iter
        """

        return iter([])
