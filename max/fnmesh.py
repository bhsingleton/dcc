import pymxs

from dcc import fnnode
from dcc.abstract import afnmesh
from dcc.max.libs import meshutils, arrayutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(fnnode.FnNode, afnmesh.AFnMesh):
    """
    Overload of AFnMesh that outlines the mesh interface for 3ds Max.
    """

    __slots__ = ()

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Check if this is a tri-mesh
        #
        obj = self.getMXSWrapper(obj)
        cls = pymxs.runtime.classOf(obj)

        if cls == pymxs.runtime.TriMesh:

            super(fnnode.FnNode, self).setObject(obj)

        else:

            handle = pymxs.runtime.getHandleByAnim(obj)
            super(fnnode.FnNode, self).setObject(handle)

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

        return meshutils.iterVertices(self.baseObject(), indices=indices)

    def iterVertexNormals(self, *indices):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.

        :rtype: iter
        """

        return meshutils.iterVertexNormals(self.baseObject(), indices=indices)

    def iterFaceVertexIndices(self, *indices):
        """
        Returns a generator that yields face vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: iter
        """

        return meshutils.iterFaceVertexIndices(self.baseObject(), indices=indices)

    def iterFaceCenters(self, *indices):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.

        :rtype: iter
        """

        return meshutils.iterFaceCenters(self.baseObject(), indices=indices)

    def iterFaceNormals(self, *indices):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.

        :rtype: iter
        """

        return meshutils.iterFaceNormals(self.baseObject(), indices=indices)

    def iterConnectedVertices(self, *args, **kwargs):
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

            return iter(meshutils.getConnectedVerts(mesh, args))

        elif componentType == self.Components.Edge:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getEdgesUsingVert(mesh, args))

        elif componentType == self.Components.Face:

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getFacesUsingVert(mesh, args))

        else:

            raise TypeError('iterConnectedVertices() expects a valid component type (%s given)' % componentType)

    def iterConnectedEdges(self, *args, **kwargs):
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

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getEdgesUsingVert(mesh, args))

        elif componentType == self.Components.Edge:

            return iter(meshutils.getConnectedEdges(mesh, args))

        elif componentType == self.Components.Face:

            return arrayutils.iterElements(pymxs.runtime.polyOp.getFaceEdges(mesh, args))

        else:

            raise TypeError('iterConnectedEdges() expects a valid component type (%s given)' % componentType)

    def iterConnectedFaces(self, *args, **kwargs):
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

            return arrayutils.iterBitArray(pymxs.runtime.polyOp.getFacesUsingVert(mesh, args))

        elif componentType == self.Components.Edge:

            return arrayutils.iterElements(pymxs.runtime.polyOp.getEdgeFaces(mesh, args))

        elif componentType == self.Components.Face:

            return iter(meshutils.getConnectedFaces(mesh, args))

        else:

            raise TypeError('iterConnectedFaces() expects a valid component type (%s given)' % componentType)

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields texture instances.

        :rtype: iter
        """

        return iter(pymxs.runtime.getClassInstances(pymxs.runtime.Editable_Poly))
