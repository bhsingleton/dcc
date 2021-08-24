import pymxs

from ..abstract import afnmesh
from . import fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(afnmesh.AFnMesh, fnnode.FnNode):

    __slots__ = ()

    def range(self, numElements):
        """
        Returns a generator for yielding mesh elements.

        :type numElements: int
        :rtype: iter
        """

        return range(1, numElements + 1, 1)

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
            yield point.x, point.y, point.z

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

            args = range(1, self.numFaces() + 1, 1)

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            vertices = pymxs.runtime.polyOp.getFaceVerts(obj, arg)
            numVertices = vertices.count

            yield [vertices[x] for x in range(numVertices)]

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

            args = range(1, self.numFaces() + 1, 1)

        # Iterate through vertices
        #
        obj = self.object()

        for arg in args:

            normal = pymxs.runtime.polyOp.getFaceNormal(obj, arg)
            yield normal.x, normal.y, normal.z
