import pymxs
import numpy

from ..abstract import afnmesh
from . import fnnode
from .libs import meshutils, arrayutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(afnmesh.AFnMesh, fnnode.FnNode):
    """
    Overload of AFnMesh used to interface with meshes in 3ds Max.
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

    def iterVertices(self, *args):
        """
        Returns a generator that yield vertex points.
        If no arguments are supplied then all vertices will be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = range(1, self.numVertices() + 1, 1)

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            point = pymxs.runtime.polyOp.getVert(obj, arg)
            yield arg, [point.x, point.y, point.z]

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
            yield arg, tuple(arrayutils.iterElements(vertices))

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

            args = range(1, self.numFaces() + 1, 1)

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            point = pymxs.runtime.polyOp.getFaceCenter(obj, arg)
            yield arg, [point.x, point.y, point.z]

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

            args = range(1, self.numFaces() + 1, 1)

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            normal = pymxs.runtime.polyOp.getFaceNormal(obj, arg)
            yield arg, [normal.x, normal.y, normal.z]

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

            numTriangles = triMesh.numFaces
            args = self.range(numTriangles)

        # Iterate through triangles
        #
        for arg in args:

            indices = pymxs.runtime.getFace(triMesh, arg)
            yield arg, tuple(arrayutils.iterElements(indices))

    def iterConnectedVertices(self, *args, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :keyword componentType: int
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

        :keyword componentType: int
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

        :keyword componentType: int
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
