import pymxs

from dcc import fnnode
from dcc.abstract import afnmesh
from dcc.max.libs import meshutils, arrayutils
from dcc.max.decorators import coordsysoverride

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

    def isEditablePoly(self):
        """
        Evaluates if this is an editable poly object.

        :rtype: bool
        """

        return pymxs.runtime.classOf(self.baseObject()) == pymxs.runtime.Editable_Poly

    def isEditableMesh(self):
        """
        Evaluates if this is an editable mesh object.

        :rtype: bool
        """

        return pymxs.runtime.classOf(self.baseObject()) in (pymxs.runtime.Editable_Mesh, pymxs.runtime.TriMesh)

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

        obj = self.baseObject()

        if self.isEditablePoly():

            return pymxs.runtime.polyOp.getNumVerts(obj)

        else:

            return pymxs.runtime.meshOp.getNumVerts(obj)

    def numEdges(self):
        """
        Returns the number of edges in this mesh.

        :rtype: int
        """

        obj = self.baseObject()

        if self.isEditablePoly():

            return pymxs.runtime.polyOp.getNumEdges(obj)

        else:

            return pymxs.runtime.meshOp.getNumFaces(obj) * 3  # Whatever you say Max?

    def numFaces(self):
        """
        Returns the number of faces in this mesh.

        :rtype: int
        """

        obj = self.baseObject()

        if self.isEditablePoly():

            return pymxs.runtime.polyOp.getNumFaces(obj)

        else:

            return pymxs.runtime.meshOp.getNumFaces(obj)

    def selectedVertices(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
        """

        obj = self.baseObject()

        if self.isEditablePoly():

            bitArray = obj.getSelection(pymxs.runtime.Name('vertex'))
            return list(arrayutils.iterBitArray(bitArray))

        else:

            bitArray = pymxs.runtime.getVertSelection(obj)
            return list(arrayutils.iterBitArray(bitArray))

    def selectedEdges(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
        """

        obj = self.baseObject()

        if self.isEditablePoly():

            bitArray = self.object().getSelection(pymxs.runtime.Name('edge'))
            return list(arrayutils.iterBitArray(bitArray))

        else:

            bitArray = pymxs.runtime.getEdgeSelection(obj)
            return list(arrayutils.iterBitArray(bitArray))

    def selectedFaces(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
        """

        obj = self.baseObject()

        if self.isEditablePoly():

            bitArray = self.object().getSelection(pymxs.runtime.Name('face'))
            return list(arrayutils.iterBitArray(bitArray))

        else:

            bitArray = pymxs.runtime.getFaceSelection(obj)
            return list(arrayutils.iterBitArray(bitArray))

    @coordsysoverride.coordSysOverride(mode='local')
    def iterVertices(self, *indices):
        """
        Returns a generator that yields vertex points.
        If no arguments are supplied then all vertex points will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = self.range(self.numVertices())

        # Iterate through vertices
        #
        obj = self.baseObject()

        if self.isEditablePoly():

            for index in indices:

                point = pymxs.runtime.polyOp.getVert(obj, index)
                yield point.x, point.y, point.z

        else:

            for index in indices:

                point = pymxs.runtime.meshOp.getVert(obj, index)
                yield point.x, point.y, point.z

    @coordsysoverride.coordSysOverride(mode='local')
    def iterVertexNormals(self, *indices):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = self.range(self.numVertices())

        # Iterate through vertices
        #
        obj = self.baseObject()

        if self.isEditablePoly():

            for index in indices:

                bits = pymxs.runtime.polyOp.getFacesUsingVert(obj, index)
                normals = [pymxs.runtime.polyOp.getFaceNormal(obj, x) for x in arrayutils.iterBitArray(bits)]
                normal = sum(normals) / len(normals)
                yield normal.x, normal.y, normal.z

        else:

            for index in indices:

                normal = pymxs.runtime.getNormal(obj, index)
                yield normal.x, normal.y, normal.z

    def iterFaceVertexIndices(self, *indices):
        """
        Returns a generator that yields face vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = self.range(self.numFaces())

        # Iterate through vertices
        #
        obj = self.baseObject()

        if self.isEditablePoly():

            for index in indices:

                vertices = pymxs.runtime.polyOp.getFaceVerts(obj, index)
                yield tuple(arrayutils.iterElements(vertices))

        else:

            for index in indices:

                indices = pymxs.runtime.getFace(obj, index)
                yield tuple(arrayutils.iterElements(indices))

    @coordsysoverride.coordSysOverride(mode='local')
    def iterFaceCenters(self, *indices):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = self.range(self.numFaces())

        # Iterate through vertices
        #
        obj = self.baseObject()

        if self.isEditablePoly():

            for index in indices:

                point = pymxs.runtime.polyOp.getFaceCenter(obj, index)
                yield point.x, point.y, point.z

        else:

            for index in indices:

                point = pymxs.runtime.meshOp.getFaceCenter(obj, index)
                yield point.x, point.y, point.z

    @coordsysoverride.coordSysOverride(mode='local')
    def iterFaceNormals(self, *indices):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = self.range(self.numFaces())

        # Iterate through vertices
        #
        obj = self.baseObject()

        if self.isEditablePoly():

            for index in indices:

                normal = pymxs.runtime.polyOp.getFaceNormal(obj, index)
                yield normal.x, normal.y, normal.z

        else:

            for index in indices:

                normals = pymxs.runtime.meshOp.getFaceRNormals(obj, index)
                normal = sum(normals) / len(normals)
                yield normal.x, normal.y, normal.z

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
