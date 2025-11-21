"""
This module is designed to explicitly work alongside the `Edit_Normals` modifier rather than the `PolyOp` interface!
As far as I'm aware this is the only way to access face-vertex normal information from poly mesh objects via maxscript.
"""
import pymxs

from . import modifierutils, meshutils, arrayutils
from ...python import stringutils
from ...dataclasses.vector import Vector
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def hasEditNormalsModifier(mesh):
    """
    Evaluates if the supplied mesh has an edit normals modifier.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return modifierutils.hasModifier(mesh, pymxs.runtime.Edit_Normals)


def findEditNormalsModifier(mesh, create=False):
    """
    Returns the edit normals modifier for the supplied mesh.
    By enabling create the function will create the modifier in case it doesn't exist!

    :type mesh: pymxs.MXSWrapperBase
    :rtype: pymxs.runtime.Edit_Normals
    """

    modifiers = modifierutils.getModifierByClass(mesh, pymxs.runtime.Edit_Normals, all=True)
    numModifiers = len(modifiers)

    if numModifiers == 0:

        if create:

            modifier = pymxs.runtime.Edit_Normals()
            pymxs.runtime.addModifier(mesh, modifier, before=1)

            return modifier

        else:

            return None

    elif numModifiers == 1:

        return modifiers[0]

    else:

        return TypeError(f'findEditNormalsModifier() expects 1 edit normals modifier ({numModifiers} found)!')


def hasExplicitNormals(mesh):
    """
    Evaluates if the supplied mesh has explicit normals.
    This is synonymous with user or custom normals for developers coming from Maya.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: bool
    """

    modifier = findEditNormalsModifier(mesh, create=True)

    numNormals = modifier.getNumNormals(node=mesh)
    isExplicit = all(modifier.getNormalExplicit(i, node=mesh) for i in inclusiveRange(1, numNormals, 1))

    return isExplicit


def iterFaceVertexNormalIndices(mesh, indices=None):
    """
    Returns a generator that yields face-vertex normal indices from the specified face indices.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: Iterator[List[int]]
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, meshutils.faceCount(mesh), 1)

    # Iterate through face indices
    #
    modifier = findEditNormalsModifier(mesh, create=True)

    for index in indices:

        numCorners = modifier.getFaceDegree(index, node=mesh)
        normalIndices = [modifier.getNormalID(index, corner, node=mesh) for corner in inclusiveRange(1, numCorners, 1)]

        yield normalIndices


def iterFaceVertexNormals(mesh, indices=None):
    """
    Returns a generator that yields face-vertex normals from the specified face indices.

    :type mesh: pymxs.MXSWrapperBase
    :type indices: List[int]
    :rtype: Iterator[List[pymxs.runtime.Point3]]
    """

    # Check if any indices were supplied
    #
    if stringutils.isNullOrEmpty(indices):

        indices = inclusiveRange(1, meshutils.faceCount(mesh), 1)

    # Iterate through face indices
    #
    modifier = findEditNormalsModifier(mesh, create=True)

    for normalIndices in iterFaceVertexNormalIndices(mesh, indices=indices):

        numNormals = len(normalIndices)
        normals = [None] * numNormals

        for (i, normalIndex) in enumerate(normalIndices):

            normal = modifier.getNormal(normalIndex, node=mesh)
            normals[i] = pymxs.runtime.copy(normal)

        yield normals


def requiresExplicitNormals(mesh):
    """
    Evaluates if the supplied mesh requires explicit normals.
    This evaluation consists of testing the equivalency of the normals assigned to each vertex.
    Returns a boolean and a complete list of vertex normal averages if successful.

    :type mesh: pymxs.MXSWrapperBase
    :rtype: Tuple[bool, List[Vector]]
    """

    # Evaluate mesh for explicit normals
    #
    isExplicit = hasExplicitNormals(mesh)

    if not isExplicit:

        return False, []

    # Iterate through vertex indices
    #
    modifier = findEditNormalsModifier(mesh, create=True)

    faceVertexIndices = list(meshutils.iterFaceVertexIndices(mesh))
    faceVertexNormalIndices = list(iterFaceVertexNormalIndices(mesh))

    vertexCount = meshutils.vertexCount(mesh)
    vertexNormals = [None] * vertexCount

    requires = False

    for vertexIndex in inclusiveRange(1, vertexCount, 1):

        # Iterate through connected faces
        #
        normalizedVertexIndex = vertexIndex - 1
        faceIndices = arrayutils.convertBitArray(pymxs.runtime.polyOp.getFacesUsingVert(mesh, [vertexIndex]))

        normalIndices = set()

        for faceIndex in faceIndices:

            normalizedFaceIndex = faceIndex - 1
            vertexIndices = faceVertexIndices[normalizedFaceIndex]
            vertexPosition = vertexIndices.index(vertexIndex)

            normalIndex = faceVertexNormalIndices[normalizedFaceIndex][vertexPosition]
            normalIndices.add(normalIndex)

        # Evaluate number of normals assigned to vertex
        #
        numNormals = len(normalIndices)

        if numNormals == 1:

            normal = modifier.getNormal(normalIndices[0], node=mesh)
            vertexNormals[normalizedVertexIndex] = Vector(normal.x, normal.y, normal.z)

            continue

        # Evaluate normal equivalency
        #
        normals = [modifier.getNormal(normalIndex, node=mesh) for normalIndex in normalIndices]

        vectors = list(map(lambda normal: Vector(normal.x, normal.y, normal.z), normals))
        averagedVector = sum(vectors, start=Vector.zero) / len(vectors)

        isEquivalent = all(averagedVector.isEquivalent(vector) for vector in vectors)

        if isEquivalent:

            vertexNormals[normalizedVertexIndex] = averagedVector
            continue

        else:

            requires = True
            break

    return requires, vertexNormals


def resetExplicitNormals(mesh, tolerance=0.15):
    """
    Attempts to safely remove any explicit normals from the supplied mesh.

    :type mesh: pymxs.MXSWrapperBase
    :type tolerance: float
    :rtype: bool
    """

    # Evaluate mesh for explicit normals
    #
    isExplicit = hasExplicitNormals(mesh)

    if not isExplicit:

        log.info('Mesh contains no explicit normals!')
        return True

    # Evaluate if mesh requires explicit normals
    #
    requiresExplicit, vertexExplicitNormals = requiresExplicitNormals(mesh)

    if requiresExplicit:

        log.warning(f'Explicit normals are required for {mesh.name} mesh!')
        return False

    # Unify face-vertex normals
    #
    modifier = findEditNormalsModifier(mesh, create=True)

    selection = arrayutils.convertToBitArray(list(inclusiveRange(1, modifier.getNumNormals(node=mesh), 1)))
    modifier.setSelection(selection, node=mesh)

    success = modifier.unify(node=mesh)

    if not success:

        log.warning(f'Unable to unify normals on {mesh.name} mesh via edit-normals modifier!')
        return True

    # Evaluate unify results
    #
    faceVertexIndices = list(meshutils.iterFaceVertexIndices(mesh))
    success = True

    for (faceIndex, vertexIndices) in enumerate(faceVertexIndices, start=1):

        # Compare new normals to original normals
        #
        numCorners = modifier.getFaceDegree(faceIndex, node=mesh)
        normalIndices = [modifier.getNormalID(faceIndex, corner, node=mesh) for corner in inclusiveRange(1, numCorners, 1)]

        areEquivalent = [None] * numCorners

        for (i, (vertexIndex, normalIndex)) in enumerate(zip(vertexIndices, normalIndices)):

            normal = modifier.getNormal(normalIndex, node=mesh)
            vector = Vector(normal.x, normal.y, normal.z)

            normalizedVertexIndex = vertexIndex - 1
            originalVector = vertexExplicitNormals[normalizedVertexIndex]

            isEquivalent = vector.isEquivalent(originalVector, tolerance=tolerance)
            areEquivalent[i] = isEquivalent

            if not isEquivalent:

                log.warning(f'Unified normal mismatch found @ {mesh.name}.vtxFace[{faceIndex}][{vertexIndex}]: {vector} != {originalVector}!')

        # Evaluate normal equivalencies
        #
        if all(areEquivalent):

            continue

        else:

            success = False
            break

    # Cleanup modifier stack
    #
    if success:

        log.info(f'Successfully removed explicit normals from {mesh.name} mesh!')
        pymxs.runtime.collapseStack(mesh)

    else:

        log.warning(f'Unable to remove explicit normals from {mesh.name} mesh!')
        pymxs.runtime.deleteModifier(mesh, modifier)

    return success
