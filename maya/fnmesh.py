import maya.cmds as mc
import maya.api.OpenMaya as om

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

        return range(numElements)

    def numVertices(self):
        """
        Returns the number of vertices in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object).numVertices

    def numEdges(self):
        """
        Returns the number of edges in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object).numEdges

    def numFaces(self):
        """
        Returns the number of faces in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object).numPolygons

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

            args = range(self.numVertices())

        # Iterate through vertices
        #
        iterVertices = om.MItMeshVertex(self.object())

        for arg in args:

            iterVertices.setIndex(arg)
            point = iterVertices.position()

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

            args = range(self.numFaces())

        # Iterate through vertices
        #
        iterPolygons = om.MItMeshPolygon(self.object())

        for arg in args:

            iterPolygons.setIndex(arg)
            yield iterPolygons.getVertices()

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

            args = range(self.numFaces())

        # Iterate through vertices
        #
        iterPolygons = om.MItMeshPolygon(self.object())

        for arg in args:

            iterPolygons.setIndex(arg)
            center = iterPolygons.center()

            yield center.x, center.y, center.z

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

            args = range(self.numFaces())

        # Iterate through vertices
        #
        iterPolygons = om.MItMeshPolygon(self.object())

        for arg in args:

            iterPolygons.setIndex(arg)

            normals = iterPolygons.getNormals()
            normal = sum(normals) / len(normals)

            yield normal.x, normal.y, normal.z
