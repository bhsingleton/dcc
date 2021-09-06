import pymxs

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def iterBitArray(bits):
    """
    Returns a generator that yields the elements from a bit array.

    :type bits: pymxs.runtime.MXSWrapperBase
    :rtype: iter
    """

    for i in range(bits.count):

        bit = bits[i]

        if bit:

            yield i + 1

        else:

            continue


def bitArrayToList(bits):
    """
    Converts the supplied bit arrray to a list.

    :type bits: pymxs.runtime.MXSWrapperBase
    :rtype: list[int]
    """

    return list(iterBitArray(bits))


def getConnectedVerts(mesh, vertices):
    """
    Returns a list of connected vertices.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type vertices: list[int]
    :rtype: list[int]
    """

    edges = pymxs.runtime.polyOp.getEdgesUsingVert(mesh, vertices)
    connectedVerts = []

    for edge in iterBitArray(edges):

        edgeVerts = pymxs.runtime.polyOp.getEdgeVerts(mesh, edge)
        connectedVerts.extend([x for x in edgeVerts if x not in vertices])

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

    for face in iterBitArray(faces):

        faceEdges = pymxs.runtime.polyOp.getFaceEdges(mesh, face)
        connectedEdges.extend([x for x in faceEdges if x not in edges])

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

    for vert in iterBitArray(verts):

        connectedFaces.extend([x for x in pymxs.runtime.polyOp.getFacesUsingVert(mesh, vert) if x not in faces])

    return connectedFaces
