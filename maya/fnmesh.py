import maya.cmds as mc
import maya.api.OpenMaya as om
import numpy

from itertools import chain

from ..abstract import afnmesh
from . import fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(afnmesh.AFnMesh, fnnode.FnNode):
    """
    Overload of AFnMesh used to interface with meshes in Maya.
    """

    __slots__ = ()

    def range(self, *args):
        """
        Returns a generator for yielding a range of mesh elements.

        :rtype: iter
        """

        return range(*args)

    def enumerate(self, elements):
        """
        Returns a generator for yielding local indices for global mesh elements.

        :type elements: list[int]
        :rtype: iter
        """

        return enumerate(elements)

    def numVertices(self):
        """
        Returns the number of vertices in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object()).numVertices

    def numEdges(self):
        """
        Returns the number of edges in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object()).numEdges

    def numFaces(self):
        """
        Returns the number of faces in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object()).numPolygons

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
            vertexIndices = iterPolygons.getVertices()

            yield tuple(vertexIndices)

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

    def iterTriangleVertexIndices(self, *args):
        """
        Returns a generator that yields face triangle vertex/point pairs.

        :rtype: iter
        """

        # Evaluate arguments
        #
        faceTriangleIndices = self.faceTriangleIndices()
        triangleFaceIndices = self.triangleFaceIndices()

        numArgs = len(args)

        if numArgs == 0:

            numTriangles = len(triangleFaceIndices)
            args = self.range(numTriangles)

        # Iterate through triangles
        #
        fnMesh = om.MFnMesh(self.object())

        for arg in args:

            faceIndex = triangleFaceIndices[arg]
            localIndex = faceTriangleIndices[faceIndex].index(arg)

            vertexIndices = fnMesh.getPolygonTriangleVertices(faceIndex, localIndex)

            yield tuple(vertexIndices)

    def iterConnectedVertices(self, *args, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :keyword componentType: int
        :rtype: iter
        """

        # Inspect component type
        #
        componentType = kwargs.get('componentType', self.Components.Vertex)

        if componentType == self.Components.Vertex:

            iterVertices = om.MItMeshVertex(self.object())

            for arg in args:

                iterVertices.setIndex(arg)
                connectedVertices = iterVertices.getConnectedVertices()

                for connectedVertex in connectedVertices:

                    yield connectedVertex

        elif componentType == self.Components.Edge:

            iterEdges = om.MItMeshEdge(self.object())

            for arg in args:

                iterEdges.setIndex(arg)

                for edgeVertIndex in range(2):

                    yield iterEdges.vertexId(edgeVertIndex)

        elif componentType == self.Components.Face:

            iterFaces = om.MItMeshPolygon(self.object())

            for arg in args:

                iterFaces.setIndex(arg)
                connectedVertices = iterFaces.getConnectedVertices()

                for connectedVertex in connectedVertices:

                    yield connectedVertex

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
        componentType = kwargs.get('componentType', self.Components.Vertex)

        if componentType == self.Components.Vertex:

            iterVertices = om.MItMeshVertex(self.object())

            for arg in args:

                iterVertices.setIndex(arg)
                connectedEdges = iterVertices.getConnectedEdges()

                for connectedEdge in connectedEdges:

                    yield connectedEdge

        elif componentType == self.Components.Edge:

            iterEdges = om.MItMeshEdge(self.object())

            for arg in args:

                iterEdges.setIndex(arg)
                connectedEdges = iterEdges.getConnectedEdges()

                for connectedEdge in connectedEdges:

                    yield connectedEdge

        elif componentType == self.Components.Face:

            iterFaces = om.MItMeshPolygon(self.object())
            connectedEdges = iterFaces.getConnectedEdges()

            for connectedEdge in connectedEdges:

                yield connectedEdge

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
        componentType = kwargs.get('componentType', self.Components.Vertex)

        if componentType == self.Components.Vertex:

            iterVertices = om.MItMeshVertex(self.object())

            for arg in args:

                iterVertices.setIndex(arg)
                connectedFaces = iterVertices.getConnectedFaces()

                for connectedFace in connectedFaces:

                    yield connectedFace

        elif componentType == self.Components.Edge:

            iterEdges = om.MItMeshEdge(self.object())

            for arg in args:

                iterEdges.setIndex(arg)
                connectedFaces = iterEdges.getConnectedFaces()

                for connectedFace in connectedFaces:

                    yield connectedFace

        elif componentType == self.Components.Face:

            iterFaces = om.MItMeshPolygon(self.object())

            for arg in args:

                iterFaces.setIndex(arg)
                connectedFaces = iterFaces.getConnectedFaces()

                for connectedFace in connectedFaces:

                    yield connectedFace

        else:

            raise TypeError('iterConnectedFaces() expects a valid component type (%s given)' % componentType)
