import pymxs

from six import integer_types
from dcc import fnnode
from dcc.abstract import afnmesh
from dcc.max.libs import wrapperutils, meshutils, arrayutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(fnnode.FnNode, afnmesh.AFnMesh):
    """
    Overload of AFnMesh that outlines the mesh interface for 3ds Max.
    """

    __slots__ = ()

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: pymxs.MXSWrapperBase
        """

        # Call parent method
        #
        obj = super(fnnode.FnNode, self).object()

        # Inspect object type
        #
        if isinstance(obj, integer_types):

            return self.getNodeByHandle(obj)

        else:

            return obj

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Check if this is a wrapper
        #
        obj = self.getMXSWrapper(obj)

        if wrapperutils.isValidWrapper(obj):

            super(FnMesh, self).setObject(obj)

        elif wrapperutils.isKindOf(obj, pymxs.runtime.TriMesh):

            super(fnnode.FnNode, self).setObject(obj)  # TriMesh objects don't support anim handles!

        else:

            raise TypeError('setObject() expects a valid MAXWrapper (%s given)!' % type(obj).__name__)

    def triMesh(self):
        """
        Returns the triangulated mesh data object for this mesh.

        :rtype: pymxs.MXSWrapperBase
        """

        obj = self.baseObject()

        if pymxs.runtime.isProperty(obj, 'mesh'):

            return obj.mesh

        else:

            return obj

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

        :rtype: list[int]
        """

        return meshutils.getSelectedVertices(self.object())

    def selectedEdges(self):
        """
        Returns a list of selected edge indices.

        :rtype: list[int]
        """

        return meshutils.getSelectedEdges(self.object())

    def selectedFaces(self):
        """
        Returns a list of selected face indices.

        :rtype: list[int]
        """

        meshutils.getSelectedFaces(self.object())

    def iterVertices(self, *indices):
        """
        Returns a generator that yields vertex points.
        If no arguments are supplied then all vertex points will be yielded.

        :rtype: iter
        """

        for point in meshutils.iterVertices(self.baseObject(), indices=indices):

            yield point.x, point.y, point.z

    def iterVertexNormals(self, *indices):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.

        :rtype: iter
        """

        for normal in meshutils.iterVertexNormals(self.baseObject(), indices=indices):

            yield normal.x, normal.y, normal.z

    def hasEdgeSmoothings(self):
        """
        Evaluates if this mesh uses edge smoothings.

        :rtype: bool
        """

        return False

    def iterEdgeSmoothings(self, *indices):
        """
        Returns a generator that yields edge smoothings.

        :rtype: iter
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

        :rtype: iter
        """

        return meshutils.iterSmoothingGroups(self.baseObject(), indices=indices)

    def iterFaceVertexIndices(self, *indices):
        """
        Returns a generator that yields face vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: iter
        """

        return meshutils.iterFaceVertexIndices(self.baseObject(), indices=indices)

    def iterFaceVertexNormals(self, *indices):
        """
        Returns a generator that yields face-vertex indices for the specified faces.

        :rtype: Iterator[List[Tuple[float, float, float]]]
        """

        for normal in meshutils.iterFaceVertexNormals(self.baseObject(), indices=indices):

            yield normal.x, normal.y, normal.z

    def iterFaceCenters(self, *indices):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.

        :rtype: iter
        """

        for point in meshutils.iterFaceCenters(self.baseObject(), indices=indices):

            yield point.x, point.y, point.z

    def iterFaceNormals(self, *indices):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.

        :rtype: iter
        """

        for normal in meshutils.iterFaceNormals(self.baseObject(), indices=indices):

            yield normal.x, normal.y, normal.z

    def iterFaceMaterialIndices(self, *indices):
        """
        Returns a generator that yields face material indices.
        If no arguments are supplied then all face-material indices will be yielded.

        :rtype: iter
        """

        return meshutils.iterFaceMaterialIndices(self.baseObject(), indices=indices)

    def getAssignedMaterials(self):
        """
        Returns a list of material-texture pairs from this mesh.

        :rtype: List[Tuple[Any, str]]
        """

        # Evaluate material type
        #
        material = getattr(self.object(), 'material')

        if wrapperutils.isKindOf(material, pymxs.runtime.Multimaterial):

            # Iterate through material list
            #
            subMaterials = list(material.materialList)
            return [(subMaterial, list(filter(None, subMaterial.maps)))[0].filename for subMaterial in subMaterials if any(subMaterial.maps)]

        elif wrapperutils.isKindOf(material, pymxs.runtime.Standardmaterial):

            # Check if material has any valid maps
            #
            maps = list(filter(None, material.maps))
            numMaps = len(maps)

            if numMaps > 0:

                return [(material, maps[0].filename)]

            else:

                return [(material, '')]

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

        :type channel: int
        :rtype: iter
        """

        for point in meshutils.iterMapVertices(self.baseObject(), channel=(channel + 1), indices=indices):

            yield point.x, point.y

    def iterAssignedUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV face-vertex indices from the specified set.

        :type channel: int
        :rtype: iter
        """

        return meshutils.iterMapFaceVertexIndices(self.baseObject(), channel=(channel + 1), indices=indices)

    def iterTangentsAndBinormals(self, *indices, channel=0):
        """
        Returns a generator that yields face-vertex tangents and binormals for the specified channel.

        :type channel: int
        :rtype: Iterator[List[Tuple[float, float, float]], List[Tuple[float, float, float]]]
        """

        return iter([])

    def iterConnectedVertices(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :key componentType: int
        :rtype: iter
        """

        # Inspect component type
        #
        mesh = self.object()
        componentType = kwargs.get('componentType', self.Components.Vertex)

        if componentType == self.Components.Vertex:

            return iter(meshutils.getConnectedVerts(mesh, indices))

        elif componentType == self.Components.Edge:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getEdgesUsingVert(mesh, indices))

        elif componentType == self.Components.Face:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getFacesUsingVert(mesh, indices))

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
        componentType = kwargs.get('componentType', self.Components.Vertex)

        if componentType == self.Components.Vertex:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getEdgesUsingVert(mesh, indices))

        elif componentType == self.Components.Edge:

            return iter(meshutils.getConnectedEdges(mesh, indices))

        elif componentType == self.Components.Face:

            return arrayutils.iterElements(pymxs.runtime.polyOp.getFaceEdges(mesh, indices))

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
        componentType = kwargs.get('componentType', self.Components.Vertex)

        if componentType == self.Components.Vertex:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getFacesUsingVert(mesh, indices))

        elif componentType == self.Components.Edge:

            return arrayutils.iterElements(pymxs.runtime.polyOp.getEdgeFaces(mesh, indices))

        elif componentType == self.Components.Face:

            return iter(meshutils.getConnectedFaces(mesh, indices))

        else:

            raise TypeError('iterConnectedFaces() expects a valid component type (%s given)' % componentType)

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields texture instances.

        :rtype: iter
        """

        return iter(pymxs.runtime.getClassInstances(pymxs.runtime.Editable_Poly))
