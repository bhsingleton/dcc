import pymxs

from . import arrayutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getConnectedVerts(mesh, vertices):
    """
    Returns a list of connected vertices.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type vertices: list[int]
    :rtype: list[int]
    """

    edges = pymxs.runtime.polyOp.getEdgesUsingVert(mesh, vertices)
    connectedVerts = []

    for edge in arrayutils.iterBitArray(edges):

        edgeVerts = pymxs.runtime.polyOp.getEdgeVerts(mesh, edge)
        connectedVerts.extend([x for x in arrayutils.iterElements(edgeVerts) if x not in vertices])

    return connectedVerts


def getConnectedEdges(mesh, edges):
    """
    Returns a list of connected edges.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type edges: list[int]
    :rtype: list[int]
    """

    faces = pymxs.runtime.polyOp.getFacesUsingEdge(mesh, edges)
    connectedEdges = []

    for face in arrayutils.iterBitArray(faces):

        faceEdges = pymxs.runtime.polyOp.getFaceEdges(mesh, face)
        connectedEdges.extend([x for x in arrayutils.iterElements(faceEdges) if x not in edges])

    return connectedEdges


def getConnectedFaces(mesh, faces):
    """
    Returns a list of connected faces.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type faces: list[int]
    :rtype: list[int]
    """

    verts = pymxs.runtime.polyOp.getVertsUsingFace(mesh, faces)
    connectedFaces = []

    for vert in arrayutils.iterBitArray(verts):

        faces = pymxs.runtime.polyOp.getFacesUsingVert(mesh, vert)
        connectedFaces.extend([x for x in arrayutils.iterBitArray(faces) if x not in faces])

    return connectedFaces
