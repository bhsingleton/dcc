import pymxs

from collections import defaultdict
from dcc.python import stringutils
from dcc.generators.inclusiverange import inclusiveRange
from dcc.max.decorators import coordsysoverride
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


@coordsysoverride.coordSysOverride(mode='local')
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


@coordsysoverride.coordSysOverride(mode='local')
def setVertices(mesh, indices, points):
    """
    Updates the vertex positions for the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :type points: List[pymxs.runtime.Point3]
    :rtype: None
    """

    # Check if this is an editable poly
    #
    if isEditablePoly(mesh):

        pymxs.runtime.polyOp.setVert(mesh, indices, points)

    else:

        pymxs.runtime.meshOp.setVert(mesh, indices, points)


@coordsysoverride.coordSysOverride(mode='local')
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


@coordsysoverride.coordSysOverride(mode='local')
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

                    faceVertexNormals[vertexNormal].append(vertexNormal)

            # Average vertex normals
            #
            vertexNormals = tuple([sum(faceVertexNormals[vertexIndex]) / len(faceVertexNormals[vertexNormal]) for vertexIndex in faceVertexIndices])
            yield vertexNormals


@coordsysoverride.coordSysOverride(mode='local')
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


@coordsysoverride.coordSysOverride(mode='local')
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


def computeTangentAndBinormal(points, mapPoints, normal):
    """
    Computes the tangent and binormal from the supplied triangle points and normal.

    :type points: List[pymxs.runtime.Point3]
    :type mapPoints: List[pymxs.runtime.Point3]
    :type normal: pymxs.runtime.Point3
    :rtype: Tuple[pymxs.runtime.Point3, pymxs.runtime.Point3]
    """

    # Calculate edge vectors
    #
    tangent = pymxs.runtime.Point3(0.0, 0.0, 0.0)
    binormal = pymxs.runtime.Point3(0.0, 0.0, 0.0)

    edge1 = pymxs.runtime.normalize(points[1] - points[0])
    edge2 = pymxs.runtime.normalize(points[2] - points[0])

    mapEdge1 = pymxs.runtime.normalize(mapPoints[1] - mapPoints[0])
    mapEdge2 = pymxs.runtime.normalize(mapPoints[2] - mapPoints[0])

    # Evaluate face area
    #
    det = (mapEdge1.x * mapEdge2.y) - (mapEdge1.y * mapEdge2.x)

    if abs(det) < 1e-3:

        tangent.x = 1.0
        binormal.y = 1.0

    else:

        det = 1.0 / det

        tangent.x = (mapEdge2.y * edge1.x - mapEdge1.y * edge2.x) * det
        tangent.y = (mapEdge2.y * edge1.y - mapEdge1.y * edge2.y) * det
        tangent.z = (mapEdge2.y * edge1.z - mapEdge1.y * edge2.z) * det

        binormal.x = (-mapEdge2.x * edge1.x + mapEdge1.x * edge2.x) * det
        binormal.y = (-mapEdge2.x * edge1.y + mapEdge1.x * edge2.y) * det
        binormal.z = (-mapEdge2.x * edge1.z + mapEdge1.x * edge2.z) * det

        tangent = pymxs.runtime.normalize(tangent)
        binormal = pymxs.runtime.normalize(binormal)

    # Check if binormal requires inversing
    #
    b = pymxs.runtime.cross(normal, tangent)
    dot = pymxs.runtime.dot(b, binormal)
    w = -1.0 if dot < 0.0 else 1.0

    binormal = b * w

    return tangent, binormal


def computeTangentsAndBinormals(mesh, channel=0):
    """
    Computes the tangents and binormals from the supplied tri-mesh object.

    :type mesh: pymxs.MXSWrapperBase
    :type channel: int
    :rtype: Tuple[list, list]
    """

    # Inspect supplied mesh
    #
    if not isTriMesh(mesh):

        mesh = getTriMesh(mesh)

    # Iterate through faces
    #
    faceNormals = list(iterFaceNormals(mesh))
    faceVertexIndices = list(iterFaceVertexIndices(mesh))
    faceVertexNormals = list(iterFaceVertexNormals(mesh))

    numFaces = len(faceNormals)
    faceVertexTangents = [None] * numFaces
    faceVertexBinormals = [None] * numFaces

    for (faceIndex, (vertexIndices, vertexNormals)) in enumerate(zip(faceVertexIndices, faceVertexNormals), start=1):

        # Get triangle-vertex points
        #
        points = list(iterVertices(mesh, indices=vertexIndices))
        normal = faceNormals[faceIndex]

        mapFaceVertexIndices = list(iterMapFaceVertexIndices(mesh, channel=channel, indices=[faceIndex]))[0]
        mapPoints = list(iterMapVertices(mesh, channel=channel, indices=mapFaceVertexIndices))

        # Calculate tangent and binormal
        #
        tangent, binormal = computeTangentAndBinormal(points, mapPoints, normal)

        # Apply vectors to triangle-vertex normals
        #
        faceVertexBinormals[faceIndex] = [pymxs.runtime.cross(normal, tangent) for normal in faceVertexNormals[faceIndex]]
        faceVertexTangents[faceIndex] = [pymxs.runtime.cross(binormal, normal) for normal in faceVertexNormals[faceIndex]]

    return faceVertexTangents, faceVertexBinormals


def getTangentsAndBinormals(mesh, channel=0):
    """
    Returns the tangents and binormals from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :type channel: int
    :rtype:
    """

    pass


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
        connectedVerts = connectedVerts.union(set(arrayutils.iterElements(edgeVerts)))

    return list(connectedVerts)


def getConnectedEdges(mesh, edges):
    """
    Returns a list of connected edges.

    :type mesh: pymxs.runtime.MXSWrapperBase
    :type edges: List[int]
    :rtype: List[int]
    """

    faces = pymxs.runtime.polyOp.getFacesUsingEdge(mesh, edges)
    connectedEdges = set()

    for face in arrayutils.iterBitArray(faces):

        faceEdges = pymxs.runtime.polyOp.getFaceEdges(mesh, face)
        connectedEdges = connectedEdges.union(set(arrayutils.iterElements(faceEdges)))

    return list(connectedEdges)


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

        faces = pymxs.runtime.polyOp.getFacesUsingVert(mesh, vert)
        connectedFaces = connectedFaces.union(set(arrayutils.iterBitArray(faces)))

    return list(connectedFaces)


def decomposeSmoothingGroups(bits):
    """
    Returns the smoothing group indices from the supplied integer value.

    :type bits: int
    :rtype: List[int]
    """

    return [i for i in inclusiveRange(1, 32, 1) if pymxs.runtime.Bit.get(bits, i)]


def iterSmoothingGroups(mesh, indices=None):
    """
    Returns a generator that yields face-smoothing indices.
    If no arguments are supplied then all face-smoothing indices will be yielded.

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

            bits = pymxs.runtime.polyOp.getFaceSmoothGroup(mesh, index)
            yield decomposeSmoothingGroups(bits)

    else:

        # Check if this is an editable mesh modifier
        #
        if isEditableMesh(mesh) and not pymxs.runtime.isValidNode(mesh):

            mesh = wrapperutils.getAssociatedNode(mesh)  # getFace raises an error for Editable_mesh types!

        # Iterate through indices
        #
        for index in indices:

            bits = pymxs.runtime.getFaceSmoothGroup(mesh, index)
            yield decomposeSmoothingGroups(bits)


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

            point = pymxs.runtime.polyOp.getMapVert(mesh, channel, index)
            yield point.x, point.y, point.z

    else:

        # Iterate through indices
        #
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

