import pymxs

from dcc import fnnode
from dcc.abstract import afnmesh
from dcc.max.libs import meshutils, arrayutils
from dcc.max.decorators import coordsysoverride

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(afnmesh.AFnMesh, fnnode.FnNode):
    """
    Overload of AFnMesh that outlines the mesh interface for 3ds Max.
    """

    __slots__ = ()

    def range(self, *args):
        """
        Returns a generator for yielding a range of mesh elements.

        :rtype: iter
        """

        # Inspect arguments
        #
        numArgs = len(args)
        start, stop, step = 1, 2, 1

        if numArgs == 1:

            stop = args[0] + 1

        elif numArgs == 2:

            start = args[0]
            stop = args[1] + 1

        elif numArgs == 3:

            start = args[0]
            stop = args[1]
            step = args[2]

        else:

            raise TypeError('range() expects at least 1 argument (%s given)!' % numArgs)

        return range(start, stop, step)

    def enumerate(self, elements):
        """
        Returns a generator for yielding local indices for global mesh elements.

        :type elements: list[int]
        :rtype: iter
        """

        numElements = len(elements)

        for i in range(numElements):

            yield (i + 1), elements[i]

    def numVertices(self):
        """
        Returns the number of vertices in this mesh.

        :rtype: int
        """

        return pymxs.runtime.polyOp.getNumVerts(self.object())

    def numEdges(self):
        """
        Returns the number of edges in this mesh.

        :rtype: int
        """

        return pymxs.runtime.polyOp.getNumEdges(self.object())

    def numFaces(self):
        """
        Returns the number of faces in this mesh.

        :rtype: int
        """

        return pymxs.runtime.polyOp.getNumFaces(self.object())

    def selectedVertices(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
        """

        bitArray = self.object().getSelection(pymxs.runtime.Name('vertex'))
        return list(arrayutils.iterBitArray(bitArray))

    def selectedEdges(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
        """

        bitArray = self.object().getSelection(pymxs.runtime.Name('edge'))
        return list(arrayutils.iterBitArray(bitArray))

    def selectedFaces(self):
        """
        Returns a list of selected vertex indices.

        :rtype: list[int]
        """

        bitArray = self.object().getSelection(pymxs.runtime.Name('face'))
        return list(arrayutils.iterBitArray(bitArray))

    @coordsysoverride.coordSysOverride(mode='local')
    def iterVertices(self, *args):
        """
        Returns a generator that yields vertex points.
        If no arguments are supplied then all vertex points will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = self.range(self.numVertices())

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            point = pymxs.runtime.polyOp.getVert(obj, arg)
            yield point.x, point.y, point.z

    @coordsysoverride.coordSysOverride(mode='local')
    def iterVertexNormals(self, *args):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = self.range(self.numVertices())

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            bits = pymxs.runtime.polyOp.getFacesUsingVert(obj, arg)

            normals = [pymxs.runtime.polyOp.getFaceNormal(obj, x) for x in arrayutils.iterBitArray(bits)]
            normal = sum(normals) / len(normals)

            yield normal.x, normal.y, normal.z

    def iterFaceVertexIndices(self, *args):
        """
        Returns a generator that yields face vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = self.range(self.numFaces())

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            vertices = pymxs.runtime.polyOp.getFaceVerts(obj, arg)
            yield tuple(arrayutils.iterElements(vertices))

    @coordsysoverride.coordSysOverride(mode='local')
    def iterFaceCenters(self, *args):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = self.range(self.numFaces())

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            point = pymxs.runtime.polyOp.getFaceCenter(obj, arg)
            yield point.x, point.y, point.z

    def iterFaceNormals(self, *args):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = self.range(self.numFaces())

        # Iterate through vertices
        #
        obj = self.object()

        with pymxs.runtime.toolMode.coordsys(pymxs.runtime.Name("local")):

            for arg in args:

                normal = pymxs.runtime.polyOp.getFaceNormal(obj, arg)
                yield normal.x, normal.y, normal.z

    def iterTriangleVertexIndices(self, *args):
        """
        Returns a generator that yields face triangle vertex/point pairs.

        :rtype: iter
        """

        # Evaluate arguments
        #
        mesh = self.object()
        triMesh = mesh.mesh

        numArgs = len(args)

        if numArgs == 0:

            args = self.range(triMesh.numFaces)

        # Iterate through triangles
        #
        for arg in args:

            indices = pymxs.runtime.getFace(triMesh, arg)
            yield tuple(arrayutils.iterElements(indices))

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
