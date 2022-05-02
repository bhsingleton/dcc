import pymxs

from dcc.python import stringutils
from dcc.generators.inclusiverange import inclusiveRange
from dcc.max.decorators import coordsysoverride
from . import arrayutils, nodeutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isEditablePoly(mesh):
    """
    Evaluates if the supplied node is an editable poly.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isKindOf(nodeutils.baseObject(mesh), pymxs.runtime.Editable_Poly)


def isEditableMesh(mesh):
    """
    Evaluates if the supplied node is an editable mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isKindOf(nodeutils.baseObject(mesh), pymxs.runtime.Editable_Mesh)


def vertexCount(mesh):
    """
    Returns the number of vertices from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Evaluate if mesh is editable poly
    #
    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getNumVerts(mesh)

    else:

        return pymxs.runtime.meshOp.getNumVerts(mesh)


def edgeCount(mesh):
    """
    Returns the number of edges from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getNumEdges(mesh)

    else:

        return pymxs.runtime.meshOp.getNumFaces(mesh) * 3  # Whatever you say Max?


def faceCount(mesh):
    """
    Returns the number of faces from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getNumFaces(mesh)

    else:

        return pymxs.runtime.meshOp.getNumFaces(mesh)


def mapCount(mesh):
    """
    Returns the number of available map channels from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getNumMaps(mesh)

    else:

        return pymxs.runtime.meshOp.getNumMaps(mesh)


def mapVertexCount(mesh, channel=0):
    """
    Returns the number of vertices from the specified map channel.

    :type mesh: pymxs.MXSWrapperBase
    :type channel: int
    :rtype: bool
    """

    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getNumMapVerts(mesh, channel)

    else:

        return pymxs.runtime.meshOp.getNumMapVerts(mesh, channel)


def mapFaceCount(mesh, channel=0):
    """
    Returns the number of faces from the specified map channel.

    :type mesh: pymxs.MXSWrapperBase
    :type channel: int
    :rtype: bool
    """

    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getNumMapFaces(mesh, channel)

    else:

        return pymxs.runtime.meshOp.getNumMapFaces(mesh, channel)


@coordsysoverride.coordSysOverride(mode='local')
def iterVertices(mesh, indices=None):
    """
    Returns a generator that yields vertex points.
    If no arguments are supplied then all vertex points will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any vertex indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, vertexCount(mesh))

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for index in indices:

            point = pymxs.runtime.polyOp.getVert(mesh, index)
            yield point.x, point.y, point.z

    else:

        for index in indices:

            point = pymxs.runtime.meshOp.getVert(mesh, index)
            yield point.x, point.y, point.z


@coordsysoverride.coordSysOverride(mode='local')
def iterVertexNormals(mesh, indices=None):
    """
    Returns a generator that yields vertex normals.
    If no arguments are supplied then all vertex normals will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any vertex indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, vertexCount(mesh))

    # Iterate through vertices
    #
    if isEditablePoly(mesh):

        for index in indices:

            bits = pymxs.runtime.polyOp.getFacesUsingVert(mesh, index)
            normals = [pymxs.runtime.polyOp.getFaceNormal(mesh, x) for x in arrayutils.iterBitArray(bits)]
            normal = sum(normals) / len(normals)

            yield normal.x, normal.y, normal.z

    else:

        for index in indices:

            normal = pymxs.runtime.getNormal(mesh, index)
            yield normal.x, normal.y, normal.z


def iterFaceVertexIndices(mesh, indices=None):
    """
    Returns a generator that yields face vertex indices.
    If no arguments are supplied then all face vertex indices will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any face indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh))

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for index in indices:

            vertices = pymxs.runtime.polyOp.getFaceVerts(mesh, index)
            yield tuple(arrayutils.iterElements(vertices))

    else:

        for index in indices:

            indices = pymxs.runtime.getFace(mesh, index)
            yield tuple(arrayutils.iterElements(indices))


@coordsysoverride.coordSysOverride(mode='local')
def iterFaceCenters(mesh, indices=None):
    """
    Returns a generator that yields face centers.
    If no arguments are supplied then all face centers will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any face indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh))

    # Iterate through faces
    #
    if isEditablePoly(mesh):

        for index in indices:

            point = pymxs.runtime.polyOp.getFaceCenter(mesh, index)
            yield point.x, point.y, point.z

    else:

        for index in indices:

            point = pymxs.runtime.meshOp.getFaceCenter(mesh, index)
            yield point.x, point.y, point.z


@coordsysoverride.coordSysOverride(mode='local')
def iterFaceNormals(mesh, indices=None):
    """
    Returns a generator that yields face normals.
    If no arguments are supplied then all face centers will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any face indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh))

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for index in indices:

            normal = pymxs.runtime.polyOp.getFaceNormal(mesh, index)
            yield normal.x, normal.y, normal.z

    else:

        for index in indices:

            normals = pymxs.runtime.meshOp.getFaceRNormals(mesh, index)
            normal = sum(normals) / len(normals)
            yield normal.x, normal.y, normal.z


def getSelectedVertices(mesh):
    """
    Returns a list of selected vertex indices.

    :rtype: list[int]
    """

    mesh = nodeutils.baseObject(mesh)

    if isEditablePoly(mesh):

        bitArray = mesh.getSelection(pymxs.runtime.Name('vertex'))
        return list(arrayutils.iterBitArray(bitArray))

    else:

        bitArray = pymxs.runtime.getVertSelection(mesh)
        return list(arrayutils.iterBitArray(bitArray))


def getSelectedEdges(mesh):
    """
    Returns a list of selected edge indices.

    :rtype: list[int]
    """

    mesh = nodeutils.baseObject(mesh)

    if isEditablePoly(mesh):

        bitArray = mesh.getSelection(pymxs.runtime.Name('edge'))
        return list(arrayutils.iterBitArray(bitArray))

    else:

        bitArray = pymxs.runtime.getEdgeSelection(mesh)
        return list(arrayutils.iterBitArray(bitArray))


def getSelectedFaces(mesh):
    """
    Returns a list of selected face indices.

    :rtype: list[int]
    """

    mesh = nodeutils.baseObject(mesh)

    if isEditablePoly(mesh):

        bitArray = mesh.getSelection(pymxs.runtime.Name('face'))
        return list(arrayutils.iterBitArray(bitArray))

    else:

        bitArray = pymxs.runtime.getFaceSelection(mesh)
        return list(arrayutils.iterBitArray(bitArray))


def getConnectedVerts(mesh, vertices):
    """
    Returns a list of connected vertices.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type vertices: List[int]
    :rtype: List[int]
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
    :type edges: List[int]
    :rtype: List[int]
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
    :type faces: List[int]
    :rtype: List[int]
    """

    verts = pymxs.runtime.polyOp.getVertsUsingFace(mesh, faces)
    connectedFaces = []

    for vert in arrayutils.iterBitArray(verts):

        faces = pymxs.runtime.polyOp.getFacesUsingVert(mesh, vert)
        connectedFaces.extend([x for x in arrayutils.iterBitArray(faces) if x not in faces])

    return connectedFaces


def iterSmoothingGroups(mesh, indices=None):
    """
    Returns a generator that yields face-smoothing indices.
    If no arguments are supplied then all face-smoothing indices will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any face indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh))

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for index in indices:

            yield pymxs.runtime.polyOp.getFaceSmoothGroup(mesh, index)

    else:

        for index in indices:

            yield pymxs.runtime.getFaceSmoothGroup(mesh, index)


def isMapSupported(mesh, channel):
    """
    Evaluates if the specified map channel is supported.

    :type mesh: pymxs.MXSWrapperBase
    :type channel: int
    :rtype: bool
    """

    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getMapSupport(mesh, channel)

    else:

        return pymxs.runtime.meshOp.getMapSupport(mesh, channel)


def iterMapVertices(mesh, channel=0, indices=None):
    """
    Returns a generator that yields map vertex points.
    If no arguments are supplied then all map vertex points will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type channel: int
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any vertex indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, mapVertexCount(mesh, channel=channel))

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for index in indices:

            point = pymxs.runtime.polyOp.getMapVert(mesh, channel, index)
            yield point.x, point.y, point.z

    else:

        for index in indices:

            point = pymxs.runtime.meshOp.getMapVert(mesh, channel, index)
            yield point.x, point.y, point.z


def iterMapFaceVertexIndices(mesh, channel=0, indices=None):
    """
    Returns a generator that yields map face-vertex indices.
    If no arguments are supplied then all map vertex points will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type channel: int
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any vertex indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, mapFaceCount(mesh, channel=channel))

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for index in indices:

            vertices = pymxs.runtime.polyOp.getMapFace(mesh, channel, index)
            yield tuple(arrayutils.iterElements(vertices))

    else:

        for index in indices:

            vertices = pymxs.runtime.meshOp.getMapFace(mesh, channel, index)
            yield vertices.x, vertices.y, vertices.z  # bruh?
