import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.maya.libs import dagutils, attributeutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def package(counts, indices):
    """
    Returns a generator that yields groups of indices based on the associated counts.

    :type counts: List[int]
    :type indices: List[int]
    :rtype: iter
    """

    position = 0

    for count in counts:

        yield indices[position:(position + count)]
        position += count


def nullMeshData():
    """
    Returns a null mesh data object.

    :rtype: om.MObject
    """

    fnMeshData = om.MFnMeshData()
    meshData = fnMeshData.create()

    fnMesh = om.MFnMesh()
    fnMesh.create([], [], [], parent=meshData)

    return meshData


def triangulateMeshData(mesh):
    """
    Returns a triangulated mesh data object from the supplied mesh.

    :type mesh: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MObject
    """

    # Get internal triangles from mesh
    #
    mesh = dagutils.getMDagPath(mesh)
    fnMesh = om.MFnMesh(mesh)

    faceTriangleCounts, triangleConnects = fnMesh.getTriangles()

    # Build triangle counts
    #
    numTriangles = sum(faceTriangleCounts)
    triangleCounts = [3] * numTriangles

    vertices = fnMesh.getPoints()

    # Create triangulate mesh data object
    #
    fnMeshData = om.MFnMeshData()
    meshData = fnMeshData.create()

    fnMesh.create(vertices, triangleCounts, triangleConnects, parent=meshData)  # Do not return this value!
    return meshData


def initializeTriMeshAttribute(mesh):
    """
    Initializes the ".triMesh" extension attribute for the supplied mesh.
    Be aware that accessing null mesh data will crash Maya!

    :type mesh: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MObject
    """

    # Initialize the attribute extension
    #
    filePath = os.path.join(attributeutils.ATTRIBUTES_PATH, 'trimesh.json')
    attribute = attributeutils.applyAttributeExtensionTemplate('mesh', filePath)[0]

    # Cache triangulated mesh
    #
    mesh = dagutils.getMObject(mesh)
    meshData = triangulateMeshData(mesh)

    plug = om.MPlug(mesh, attribute)
    plug.setMObject(meshData)

    return attribute


def getTriMeshData(mesh):
    """
    Returns the cached triangulated mesh data object from the supplied mesh.

    :type mesh: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MObject
    """

    # Get ".triMesh" plug
    #
    mesh = dagutils.getMDagPath(mesh)
    fnMesh = om.MFnMesh(mesh)

    attribute = fnMesh.attribute('triMesh')

    if attribute.isNull():

        attribute = initializeTriMeshAttribute(fnMesh)

    # Evaluate mesh data
    #
    plug = om.MPlug(mesh.node(), attribute)

    meshData = plug.asMObject()
    fnMeshData = om.MFnMesh(meshData)

    if fnMesh.numVertices == fnMeshData.numVertices:

        return meshData

    else:

        meshData = triangulateMeshData(mesh)
        plug.setMObject(meshData)

        return meshData
