import pymxs

from collections import defaultdict
from itertools import chain
from dcc.python import stringutils
from dcc.generators.inclusiverange import inclusiveRange
from dcc.max.decorators.coordsysoverride import coordSysOverride
from . import arrayutils, nodeutils, wrapperutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__face_triangles__ = {}


def isEditablePoly(mesh):
    """
    Evaluates if the supplied node is an editable poly.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return wrapperutils.isKindOf(nodeutils.baseObject(mesh), pymxs.runtime.Editable_Poly)


def isEditableMesh(mesh):
    """
    Evaluates if the supplied node is an editable mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return wrapperutils.isKindOf(nodeutils.baseObject(mesh), pymxs.runtime.Editable_Mesh)


def isTriMesh(mesh):
    """
    Evaluates if the supplied object is a tri-mesh data object.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return not wrapperutils.isValidWrapper(mesh) and wrapperutils.isKindOf(mesh, pymxs.runtime.TriMesh)


def getTriMesh(mesh):
    """
    Returns the tri-mesh from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    if isTriMesh(mesh):

        return mesh

    elif isEditableMesh(mesh) or isEditablePoly(mesh):

        return getattr(mesh, 'mesh', None)

    else:

        return None


def vertexCount(mesh):
    """
    Returns the number of vertices from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: int
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
    :rtype: int
    """

    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getNumEdges(mesh)

    else:

        return pymxs.runtime.meshOp.getNumFaces(mesh) * 3  # Whatever you say Max?


def faceCount(mesh):
    """
    Returns the number of faces from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: int
    """

    if isEditablePoly(mesh):

        return pymxs.runtime.polyOp.getNumFaces(mesh)

    else:

        return pymxs.runtime.meshOp.getNumFaces(mesh)


def triCount(mesh):
    """
    Returns the number of triangles from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: int
    """

    triMesh = getTriMesh(mesh)

    if triMesh is not None:

        return pymxs.runtime.meshOp.getNumFaces(triMesh)

    else:

        return 0


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


@coordSysOverride(mode='local')
def iterVertices(mesh, indices=None):
    """
    Returns a generator that yields vertex points.
    If no arguments are supplied then all vertex points will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, vertexCount(mesh), 1)

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for index in indices:

            yield pymxs.runtime.polyOp.getVert(mesh, index)

    else:

        for index in indices:

            yield pymxs.runtime.meshOp.getVert(mesh, index)


@coordSysOverride(mode='local')
def setVertices(mesh, indices, points):
    """
    Updates the vertex positions for the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :type points: List[pymxs.runtime.Point3]
    :rtype: None
    """

    # Evaluate supplied arguments
    #
    numIndices = len(indices)
    numPoints = len(points)

    if not pymxs.runtime.isValidObj(mesh) or numIndices != numPoints:

        raise TypeError('setVertices() expects a valid mesh and matching index-point pairs!')

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for (index, point) in zip(indices, points):

            pymxs.runtime.polyOp.setVert(mesh, index, point)

    else:

        for (index, point) in zip(indices, points):

            pymxs.runtime.meshOp.setVert(mesh, index, point)


@coordSysOverride(mode='local')
def iterVertexNormals(mesh, indices=None):
    """
    Returns a generator that yields vertex normals.
    If no arguments are supplied then all vertex normals will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, vertexCount(mesh), 1)

    # Iterate through vertices
    #
    if isEditablePoly(mesh):

        for index in indices:

            bits = pymxs.runtime.polyOp.getFacesUsingVert(mesh, index)
            normals = [pymxs.runtime.polyOp.getFaceNormal(mesh, x) for x in arrayutils.iterBitArray(bits)]
            normal = sum(normals) / len(normals)

            yield normal

    else:

        for index in indices:

            yield pymxs.runtime.getNormal(mesh, index)


def iterFaceVertexIndices(mesh, indices=None):
    """
    Returns a generator that yields face-vertex indices.
    If no arguments are supplied then all face-vertex indices will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh), 1)

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        # Iterate through indices
        #
        for index in indices:

            vertices = pymxs.runtime.polyOp.getFaceVerts(mesh, index)
            yield tuple(arrayutils.iterElements(vertices))

    else:

        # Iterate through indices
        #
        for index in indices:

            vertices = pymxs.runtime.meshOp.getFace(mesh, index)
            yield int(vertices.x), int(vertices.y), int(vertices.z)  # bruh


@coordSysOverride(mode='local')
def iterFaceVertexNormals(mesh, indices=None):
    """
    Returns a generator that yield face-vertex normals.
    If no arguments are supplied then all face-vertex normals will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh), 1)

    # Check if this is a tri-mesh
    #
    if isTriMesh(mesh):

        # Iterate through indices
        #
        for index in indices:

            normals = pymxs.runtime.meshOp.getFaceRNormals(mesh, index)
            yield normals[0], normals[1], normals[2]

    else:

        # Iterate through indices
        #
        faceTriangleIndices = getFaceTriangleIndices(mesh)
        triMesh = getTriMesh(mesh)

        for index in indices:

            # Collect triangle-vertex normals
            #
            faceVertexIndices = list(iterFaceVertexIndices(mesh, indices=[index]))[0]
            triangleIndices = faceTriangleIndices[index]

            faceVertexNormals = defaultdict(list)

            for triangleIndex in triangleIndices:

                triangleVertexIndices = list(iterFaceVertexIndices(triMesh, indices=[triangleIndex]))[0]
                triangleVertexNormals = list(iterFaceVertexNormals(triMesh, indices=[triangleIndex]))[0]

                for (vertexIndex, vertexNormal) in zip(triangleVertexIndices, triangleVertexNormals):

                    faceVertexNormals[vertexIndex].append(vertexNormal)

            # Yield averaged face-vertex normals
            #
            yield tuple(sum(faceVertexNormals[vertexIndex]) / len(faceVertexNormals[vertexIndex]) for vertexIndex in faceVertexIndices)


@coordSysOverride(mode='local')
def iterFaceCenters(mesh, indices=None):
    """
    Returns a generator that yields face centers.
    If no arguments are supplied then all face centers will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh), 1)

    # Iterate through faces
    #
    if isEditablePoly(mesh):

        # Iterate through indices
        #
        for index in indices:

            yield pymxs.runtime.polyOp.getFaceCenter(mesh, index)

    else:

        # Iterate through indices
        #
        for index in indices:

            yield pymxs.runtime.meshOp.getFaceCenter(mesh, index)


@coordSysOverride(mode='local')
def iterFaceNormals(mesh, indices=None):
    """
    Returns a generator that yields face normals.
    If no arguments are supplied then all face centers will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh), 1)

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        # Iterate through indicies
        #
        for index in indices:

            yield pymxs.runtime.polyOp.getFaceNormal(mesh, index)

    else:

        # Iterate through indicies
        #
        for index in indices:

            normals = pymxs.runtime.meshOp.getFaceRNormals(mesh, index)
            normal = sum(normals) / len(normals)

            yield normal


def getFaceTriangleIndices(mesh):
    """
    Returns a dictionary of face-triangle indices.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: Dict[int, List[int]]
    """

    # Redundancy check
    #
    if isTriMesh(mesh):

        return {i: [i] for i in range(1, faceCount(mesh) + 1, 1)}

    # Check if map has already been generated
    #
    handle = pymxs.runtime.getHandleByAnim(mesh)
    faceTriangleIndices = __face_triangles__.get(handle, {})

    if len(faceTriangleIndices) == faceCount(mesh):

        return faceTriangleIndices

    # Iterate through faces
    #
    faceVertexIndices = list(iterFaceVertexIndices(mesh))
    faceTriangleIndices = {}

    start = 1

    for (faceIndex, vertexIndices) in enumerate(faceVertexIndices, start=start):

        # Get triangle count
        #
        faceVertexCount = len(vertexIndices)
        triangleCount = faceVertexCount - 2

        # Yield triangle range
        #
        end = start + triangleCount
        faceTriangleIndices[faceIndex] = list(range(start, end))

        # Increment start position
        #
        start += triangleCount

    # Store map and return value
    #
    __face_triangles__[handle] = faceTriangleIndices
    return faceTriangleIndices


def getTriangleFaceIndices(mesh):
    """
    Returns the triangle-face indices.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: Dict[int, int]
    """

    # Iterate through face-triangle indices
    #
    faceTriangleIndices = getFaceTriangleIndices(mesh)
    triangleFaceIndices = {}

    for (faceIndex, triangleIndices) in faceTriangleIndices.items():

        # Create reverse lookup for triangle
        #
        for triangleIndex in triangleIndices:

            triangleFaceIndices[triangleIndex] = faceIndex

    return triangleFaceIndices


def getConnectedVerts(mesh, vertices):
    """
    Returns a list of connected vertices.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type vertices: List[int]
    :rtype: List[int]
    """

    edges = pymxs.runtime.polyOp.getEdgesUsingVert(mesh, vertices)
    connectedVerts = set()

    for edge in arrayutils.iterBitArray(edges):

        edgeVerts = pymxs.runtime.polyOp.getEdgeVerts(mesh, edge)
        connectedVerts = connectedVerts.union(set(arrayutils.iterBitArray(edgeVerts)))

    return list(connectedVerts.difference(set(vertices)))


def getConnectedEdges(mesh, edges):
    """
    Returns a list of connected edges.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type edges: List[int]
    :rtype: List[int]
    """

    verts = pymxs.runtime.polyOp.getVertsUsingEdge(mesh, edges)
    connectedEdges = set()

    for vert in arrayutils.iterBitArray(verts):

        vertEdges = pymxs.runtime.polyOp.getEdgesUsingVert(mesh, vert)
        connectedEdges = connectedEdges.union(set(arrayutils.iterBitArray(vertEdges)))

    return list(connectedEdges.difference(set(edges)))


def getConnectedFaces(mesh, faces):
    """
    Returns a list of connected faces.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type faces: List[int]
    :rtype: List[int]
    """

    verts = pymxs.runtime.polyOp.getVertsUsingFace(mesh, faces)
    connectedFaces = set()

    for vert in arrayutils.iterBitArray(verts):

        vertFaces = pymxs.runtime.polyOp.getFacesUsingVert(mesh, vert)
        connectedFaces = connectedFaces.union(set(arrayutils.iterBitArray(vertFaces)))

    return list(connectedFaces.difference(set(faces)))


def decomposeSmoothingGroups(bits):
    """
    Returns the smoothing group indices from the supplied integer value.

    :type bits: int
    :rtype: List[int]
    """

    return [i for i in inclusiveRange(1, 32, 1) if pymxs.runtime.Bit.get(bits, i)]


def iterSmoothingGroups(mesh, indices=None, convertUnits=False):
    """
    Returns a generator that yields face-smoothing indices.
    If no arguments are supplied then all face-smoothing indices will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :type convertUnits: bool
    :rtype: iter
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh), 1)

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        # Iterate through indices
        #
        for index in indices:

            bits = pymxs.runtime.polyOp.getFaceSmoothGroup(mesh, index)

            if convertUnits:

                yield decomposeSmoothingGroups(bits)

            else:

                yield bits

    else:

        # Check if this is an editable mesh modifier
        #
        if isEditableMesh(mesh) and not pymxs.runtime.isValidNode(mesh):

            mesh = wrapperutils.getAssociatedNode(mesh)  # getFace raises an error for Editable_mesh types!

        # Iterate through indices
        #
        for index in indices:

            bits = pymxs.runtime.getFaceSmoothGroup(mesh, index)

            if convertUnits:

                yield decomposeSmoothingGroups(bits)

            else:

                yield bits


def iterEdgeSmoothings(mesh, indices=None):
    """
    Returns a generator that yields edge-smoothings.
    If no arguments are supplied then all edge-smoothings will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: Iterator[bool]
    """

    # Check if this is an editable poly
    #
    if not isEditablePoly(mesh):

        return iter([])

    # Select hard edges
    #
    mesh.selectHardEdges()
    selectedEdges = pymxs.runtime.polyOp.getEdgeSelection(mesh)  # type: pymxs.runtime.BitArray

    # Iterate through indices
    #
    indices = range(edgeCount(mesh)) if stringutils.isNullOrEmpty(indices) else indices

    for index in indices:

        yield not selectedEdges[index]  # Is it smooth?


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

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, mapVertexCount(mesh, channel=channel), 1)

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        # Iterate through indices
        #
        for index in indices:

            yield pymxs.runtime.polyOp.getMapVert(mesh, channel, index)

    else:

        # Iterate through indices
        #
        for index in indices:

            yield pymxs.runtime.meshOp.getMapVert(mesh, channel, index)


def iterMapFaceVertexIndices(mesh, channel=0, indices=None):
    """
    Returns a generator that yields map face-vertex indices.
    If no arguments are supplied then all map vertex points will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type channel: int
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, mapFaceCount(mesh, channel=channel), 1)

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        for index in indices:

            vertices = pymxs.runtime.polyOp.getMapFace(mesh, channel, index)
            yield tuple(arrayutils.iterElements(vertices))

    else:

        for index in indices:

            vertices = pymxs.runtime.meshOp.getMapFace(mesh, channel, index)
            yield int(vertices.x), int(vertices.y), int(vertices.z)  # bruh


def iterFaceMaterialIndices(mesh, indices=None):
    """
    Returns a generator that yields face-material indices.
    If no arguments are supplied then all face-material indices will be yielded.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: iter
    """

    # Check if any vertex indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, faceCount(mesh), 1)

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        # Iterate through indices
        #
        for index in indices:

            index = pymxs.runtime.polyOp.getFaceMatID(mesh, index)
            yield int(index)

    else:

        # Iterate through indices
        #
        for index in indices:

            index = pymxs.runtime.meshOp.getFaceMatID(mesh, index)
            yield int(index)


def iterVertexColors(mesh):
    """
    Returns a generator that yields the vertex colours from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: Iterator[pymxs.runtime.Color]
    """

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        mesh = getTriMesh(mesh)

    # Evaluate colours per-vertex
    #
    numColors = mesh.numCPVVerts

    for i in inclusiveRange(1, numColors, 1):

        yield pymxs.runtime.getVertColor(mesh, i)


def iterFaceVertexColorIndices(mesh, indices=None):
    """
    Returns a generator that yields face-vertex color indices.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: Union[List[int], None]
    :rtype: Iterator[List[int]]
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = list(inclusiveRange(1, faceCount(mesh), 1))

    # Check if this is tri-mesh
    #
    if isTriMesh(mesh):

        # Iterate through indices
        #
        for index in indices:

            faceIndices = pymxs.runtime.getVCFace(mesh, index)
            yield tuple(map(int, faceIndices))

    else:

        # Remap triangle-vertex indices
        #
        triMesh = getTriMesh(mesh)

        faceTriangleIndices = getFaceTriangleIndices(mesh)
        faceVertexIndices = list(iterFaceVertexIndices(mesh, indices=indices))

        for (localIndex, globalIndex) in enumerate(indices):

            triangleIndices = faceTriangleIndices[globalIndex]
            triangleVertexIndices = tuple(chain(*[tuple(map(int, pymxs.runtime.meshOp.getFace(triMesh, triangleIndex))) for triangleIndex in triangleIndices]))
            triangleVertexColorIndices = tuple(chain(*[tuple(map(int, pymxs.runtime.getVCFace(triMesh, triangleIndex))) for triangleIndex in triangleIndices]))

            vertexIndices = faceVertexIndices[localIndex]
            faceVertexColorIndices = [None] * len(vertexIndices)

            for (i, vertexIndex) in enumerate(vertexIndices):

                position = triangleVertexIndices.index(vertexIndex)
                faceVertexColorIndices[i] = triangleVertexColorIndices[position]

            yield faceVertexColorIndices
