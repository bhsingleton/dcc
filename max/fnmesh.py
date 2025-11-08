import pymxs

from itertools import chain
from .libs import wrapperutils, propertyutils, arrayutils, meshutils
from . import fnnode
from ..abstract import afnmesh
from ..python import stringutils
from ..dataclasses.vector import Vector
from ..dataclasses.colour import Colour
from ..vendor.six import integer_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(fnnode.FnNode, afnmesh.AFnMesh):
    """
    Overload of `AFnMesh` that implements the mesh interface for 3ds-Max.
    """

    __slots__ = ()

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: pymxs.MXSWrapperBase
        """

        if isinstance(self._object, integer_types):

            return super(FnMesh, self).object()

        elif isinstance(self._object, pymxs.MXSWrapperBase):

            return self._object

        else:

            return None

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Check if this is a wrapper
        #
        obj = self.getMXSWrapper(obj)

        if meshutils.isTriMesh(obj):

            self._object = obj  # Tri-mesh object handles return the associated node!

        elif meshutils.isEditableMesh(obj) or meshutils.isEditablePoly(obj):

            super(FnMesh, self).setObject(obj)

        else:

            raise TypeError('setObject() expects a valid MAXWrapper (%s given)!' % type(obj).__name__)

    def objectTransform(self):
        """
        Returns the object transform for this mesh.

        :rtype: pymxs.runtime.Matrix3
        """

        obj = self.object()
        return getattr(obj, 'objectTransform', pymxs.runtime.Matrix3(1))

    def triangulatedObject(self):
        """
        Returns the triangulated mesh data object for this mesh.

        :rtype: pymxs.MXSWrapperBase
        """

        baseObject = self.baseObject()
        return getattr(baseObject, 'mesh', baseObject)

    def numVertices(self):
        """
        Returns the number of vertices in this mesh.

        :rtype: int
        """

        return meshutils.vertexCount(self.baseObject())

    def numEdges(self):
        """
        Returns the number of edges in this mesh.

        :rtype: int
        """

        return meshutils.edgeCount(self.baseObject())

    def numFaces(self):
        """
        Returns the number of faces in this mesh.

        :rtype: int
        """

        return meshutils.faceCount(self.baseObject())

    def selectedVertices(self):
        """
        Returns a list of selected vertex indices.

        :rtype: List[int]
        """

        return meshutils.getSelectedVertices(self.object())

    def selectedEdges(self):
        """
        Returns a list of selected edge indices.

        :rtype: List[int]
        """

        return meshutils.getSelectedEdges(self.object())

    def selectedFaces(self):
        """
        Returns a list of selected face indices.

        :rtype: List[int]
        """

        return meshutils.getSelectedFaces(self.object())

    def iterVertices(self, *indices, cls=Vector, worldSpace=False):
        """
        Returns a generator that yields vertex points.
        If no arguments are supplied then all vertex points will be yielded.

        :type cls: Callable
        :type worldSpace: bool
        :rtype: Iterator[Vector]
        """

        # Iterate through vertices
        #
        objectTransform = self.objectTransform()

        for point in meshutils.iterVertices(self.baseObject(), indices=indices):

            if worldSpace:

                point = point * objectTransform

            yield cls(point.x, point.y, point.z)

    def iterVertexNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.

        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        for normal in meshutils.iterVertexNormals(self.baseObject(), indices=indices):

            yield cls(normal.x, normal.y, normal.z)

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

        return True

    def numSmoothingGroups(self):
        """
        Returns the number of smoothing groups currently in use.

        :rtype: int
        """

        return len(set(self.iterSmoothingGroups()))

    def iterSmoothingGroups(self, *indices):
        """
        Returns a generator that yields face smoothing groups.

        :rtype: Iterator[int]
        """

        return meshutils.iterSmoothingGroups(self.baseObject(), indices=indices)

    def iterFaceVertexIndices(self, *indices):
        """
        Returns a generator that yields face vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: Iterator[List[int]]
        """

        return meshutils.iterFaceVertexIndices(self.baseObject(), indices=indices)

    def iterFaceVertexNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields face-vertex indices for the specified faces.

        :type cls: Callable
        :rtype: Iterator[List[Vector]]
        """

        for normals in meshutils.iterFaceVertexNormals(self.baseObject(), indices=indices):

            yield tuple(cls(normal.x, normal.y, normal.z) for normal in normals)

    def iterFaceCenters(self, *indices, cls=Vector):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.

        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        for point in meshutils.iterFaceCenters(self.baseObject(), indices=indices):

            yield cls(point.x, point.y, point.z)

    def iterFaceNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.

        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        for normal in meshutils.iterFaceNormals(self.baseObject(), indices=indices):

            yield cls(normal.x, normal.y, normal.z)

    def getFaceTriangleIndices(self):
        """
        Returns the face-triangle indices.

        :rtype: Dict[int, List[int]]
        """

        return meshutils.getFaceTriangleIndices(self.object())

    def getFaceTriangleVertexIndices(self):
        """
        Returns a dictionary of faces and their corresponding triangle-vertex indices.

        :rtype: Dict[int, List[Tuple[int, int, int]]]
        """

        triMesh = self.triangulatedObject()
        faceTriangleIndices = self.getFaceTriangleIndices()

        faceTriangleVertexIndices = {}

        for (faceIndex, faceTriangleIndices) in faceTriangleIndices.items():

            faceTriangleVertexIndices[faceIndex] = [tuple(map(int, pymxs.runtime.meshOp.getFace(triMesh, triangleIndex))) for triangleIndex in faceTriangleIndices]

        return faceTriangleVertexIndices

    def iterFaceMaterialIndices(self, *indices):
        """
        Returns a generator that yields face material indices.
        If no arguments are supplied then all face-material indices will be yielded.

        :rtype: iter
        """

        return meshutils.iterFaceMaterialIndices(self.baseObject(), indices=indices)

    @classmethod
    def getMapFromMaterial(cls, material):
        """
        Returns the texture path associated with the supplied material.

        :type material: pymxs.MXSWrapperBase
        :rtype: str
        """

        # Evaluate material type
        #
        maps = []

        if wrapperutils.isKindOf(material, pymxs.runtime.Standardmaterial):

            maps = getattr(material, 'maps', [])


        elif wrapperutils.isKindOf(material, pymxs.runtime.PhysicalMaterial):

            maps = [value for (key, value) in propertyutils.iterStaticProperties(material) if key.endswith('map')]

        else:

            log.warning(f'Unable to locate maps from: {pymxs.runtime.classOf(material)} class!')

        # Filter invalid maps and return file path
        #
        filteredMaps = tuple(filter(lambda obj: wrapperutils.isKindOf(obj, pymxs.runtime.BitmapTexture), maps))
        numMaps = len(filteredMaps)

        if numMaps > 0:

            return filteredMaps[0].filename

        else:

            return ''

    def getAssignedMaterials(self):
        """
        Returns a list of material-texture pairs from this mesh.

        :rtype: List[Tuple[Any, str]]
        """

        # Evaluate material type
        #
        material = getattr(self.object(), 'material')

        if wrapperutils.isKindOf(material, pymxs.runtime.Multimaterial):

            # Iterate through sub-material maps
            #
            subMaterials = list(material.materialList)
            numSubMaterials = len(subMaterials)

            assignedMaterials = [None] * numSubMaterials

            for (i, subMaterial) in enumerate(subMaterials):

                assignedMaterials[i] = (subMaterial, self.getMapFromMaterial(subMaterial))

            return assignedMaterials

        elif wrapperutils.isKindOf(material, pymxs.runtime.Standardmaterial):

            # Return material map
            #
            return [(material, self.getMapFromMaterial(material))]

        else:

            return []

    def numUVSets(self):
        """
        Returns the number of UV sets.

        :rtype: int
        """

        return meshutils.mapCount(self.baseObject()) - 1  # Base map is unusable

    def getUVSetNames(self):
        """
        Returns the UV set names.

        :rtype: List[str]
        """

        return ['UVChannel_{index}'.format(index=(i + 1)) for i in range(self.numUVSets())]

    def iterUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV vertex points from the specified set.

        :type indices: Union[int, List[int]]
        :type channel: int
        :rtype: iter
        """

        for point in meshutils.iterMapVertices(self.baseObject(), channel=(channel + 1), indices=indices):

            yield point.x, point.y

    def iterAssignedUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV face-vertex indices from the specified set.

        :type indices: Union[int, List[int]]
        :type channel: int
        :rtype: iter
        """

        return meshutils.iterMapFaceVertexIndices(self.baseObject(), channel=(channel + 1), indices=indices)

    def iterTangentsAndBinormals(self, *indices, cls=Vector, channel=0):
        """
        Returns a generator that yields face-vertex tangents and binormals for the specified channel.

        :type indices: Union[int, List[int]]
        :type cls: Callable
        :type channel: int
        :rtype: Iterator[List[Vector], List[Vector]]
        """

        return iter([])  # As far as I'm aware this data is not readily available?

    def getColorSetNames(self):
        """
        Returns a list of color set names.

        :rtype: List[str]
        """

        triMesh = self.triangulatedObject()
        hasColors = bool(triMesh.numCPVVerts)

        if hasColors:

            return ['']  # 3ds Max does not utilize colour set names!

        else:

            return []

    def getColorSetName(self, channel):
        """
        Returns the color set name at the specified channel.

        :type channel: int
        :rtype: str
        """

        colorSetNames = self.getColorSetNames()
        numColorSetNames = len(colorSetNames)

        if 0 <= channel < numColorSetNames:

            return colorSetNames[channel]

        else:

            return ''

    def iterColors(self, cls=Colour, channel=0):
        """
        Returns a generator that yields index-color pairs for the specified vertex color channel.

        :type cls: Callable
        :type channel: int
        :rtype: Iterator[Colour]
        """

        for color in meshutils.iterVertexColors(self.object()):

            yield cls((color.r / 255.0), (color.g / 255.0), (color.b / 255.0))

    def iterFaceVertexColorIndices(self, *indices, channel=0):
        """
        Returns a generator that yields face-vertex color indices for the specified faces.

        :type channel: int
        :rtype: Iterator[List[int]]
        """

        return meshutils.iterFaceVertexColorIndices(self.object(), indices=indices)

    def iterConnectedVertices(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :key componentType: int
        :rtype: iter
        """

        # Inspect component type
        #
        mesh = self.object()
        componentType = kwargs.get('componentType', self.ComponentType.Vertex)

        if componentType == self.ComponentType.Vertex:

            return iter(meshutils.getConnectedVerts(mesh, indices))

        elif componentType == self.ComponentType.Edge:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getVertsUsingEdge(mesh, indices))

        elif componentType == self.ComponentType.Face:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getVertsUsingFace(mesh, indices))

        else:

            raise TypeError('iterConnectedVertices() expects a valid component type (%s given)' % componentType)

    def iterConnectedEdges(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected edge elements.

        :key componentType: int
        :rtype: iter
        """

        # Inspect component type
        #
        mesh = self.object()
        componentType = kwargs.get('componentType', self.ComponentType.Edge)

        if componentType == self.ComponentType.Vertex:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getEdgesUsingVert(mesh, indices))

        elif componentType == self.ComponentType.Edge:

            return iter(meshutils.getConnectedEdges(mesh, indices))

        elif componentType == self.ComponentType.Face:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getEdgesUsingFace(mesh, indices))

        else:

            raise TypeError('iterConnectedEdges() expects a valid component type (%s given)' % componentType)

    def iterConnectedFaces(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected face elements.

        :key componentType: int
        :rtype: iter
        """

        # Inspect component type
        #
        mesh = self.object()
        componentType = kwargs.get('componentType', self.ComponentType.Face)

        if componentType == self.ComponentType.Vertex:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getFacesUsingVert(mesh, indices))

        elif componentType == self.ComponentType.Edge:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getFacesUsingEdge(mesh, indices))

        elif componentType == self.ComponentType.Face:

            return iter(meshutils.getConnectedFaces(mesh, indices))

        else:

            raise TypeError('iterConnectedFaces() expects a valid component type (%s given)' % componentType)

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields mesh instances.

        :rtype: iter
        """

        return iter(pymxs.runtime.getClassInstances(pymxs.runtime.Editable_Poly))
