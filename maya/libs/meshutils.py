from maya import cmds as mc, mel
from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.maya.libs import dagutils, plugutils

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


def transferAttributes(source, destination):
    """
    Transfers the attributes from the source to the destination node.

    :type source: Union[str, om.MObject, om.MDagPath]
    :type destination: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Evaluate node types
    #
    source = dagutils.getMObject(source)
    destination = dagutils.getMObject(destination)

    if source.apiTypeStr != destination.apiTypeStr:

        raise TypeError('transferAttributes() expects matching node types!')

    # Iterate through top-level plugs
    #
    fnAttribute = om.MFnAttribute()

    for plug in plugutils.iterTopLevelPlugs(source):

        # Get other plug
        #
        plugPath = plug.partialName(includeNodeName=False, useFullAttributePath=True, useLongNames=True)

        otherPlug = plugutils.findPlug(destination, plugPath)
        log.info(f'Transferring attributes: {plug.info} > {otherPlug.info}')

        # Check if plug are writable
        #
        fnAttribute.setObject(otherPlug.attribute())

        isWritable = fnAttribute.readable and (fnAttribute.writable and fnAttribute.storable) and not fnAttribute.hidden
        isFreeToChange = otherPlug.isFreeToChange(checkChildren=True) == om.MPlug.kFreeToChange
        isDefault = plug.isDefaultValue()

        if isDefault or not (isWritable and isFreeToChange):

            continue

        # Copy data handles
        #
        handle, otherHandle = None, None

        try:

            handle = plug.asMDataHandle()
            otherHandle = otherPlug.asMDataHandle()

            otherHandle.copyWritable(handle)
            otherPlug.setMDataHandle(otherHandle)

        except RuntimeError as exception:

            log.debug(exception)

        finally:

            plug.destructHandle(handle)
            otherPlug.destructHandle(otherHandle)


def clearShaders(mesh):
    """
    Removes all shaders from the supplied mesh.

    :type mesh: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Evaluate node type
    #
    mesh = dagutils.getMObject(mesh)

    if not mesh.hasFn(om.MFn.kMesh):

        raise TypeError(f'transferShaders() expects a mesh ({mesh.apiTypeStr} given)!')

    # Get connected shaders
    #
    dagPath = dagutils.getMDagPath(mesh)
    instanceNumber = dagPath.instanceNumber()

    fnMesh = om.MFnMesh(dagPath)
    shaders, connections = fnMesh.getConnectedShaders(instanceNumber)

    # Remove shaders from mesh components
    #
    fnSet = om.MFnSet()
    fnComponent = om.MFnSingleIndexedComponent()

    component = None
    selection = om.MSelectionList()

    for (i, shader) in enumerate(shaders):

        fnSet.setObject(shader)
        faceIndices = [faceIndex for (faceIndex, shaderIndex) in enumerate(connections) if shaderIndex == i]

        component = fnComponent.create(om.MFn.kMeshPolygonComponent)
        fnComponent.addElements(faceIndices)

        selection.add((dagPath, component))
        fnSet.removeMembers(selection)
        selection.clear()


def transferShaders(source, destination):
    """
    Transfers the shaders from the source to the destination mesh.

    :type source: Union[str, om.MObject, om.MDagPath]
    :type destination: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Evaluate node types
    #
    source = dagutils.getMObject(source)
    destination = dagutils.getMObject(destination)

    if not (source.hasFn(om.MFn.kMesh) and destination.hasFn(om.MFn.kMesh)):

        raise TypeError(f'transferShaders() expects 2 meshes ({source.apiTypeStr} and {destination.apiTypeStr} given)!')

    # Get connected shaders
    #
    instanceNumber = dagutils.getMDagPath(source).instanceNumber()

    fnSource = om.MFnMesh(source)
    shaders, connections = fnSource.getConnectedShaders(instanceNumber)

    # Copy connected shaders
    #
    clearShaders(destination)

    fnSet = om.MFnSet()
    fnComponent = om.MFnSingleIndexedComponent()

    dagPath = dagutils.getMDagPath(destination)
    component = None
    selection = om.MSelectionList()

    for (i, shader) in enumerate(shaders):

        fnSet.setObject(shader)
        faceIndices = [faceIndex for (faceIndex, shaderIndex) in enumerate(connections) if shaderIndex == i]

        component = fnComponent.create(om.MFn.kMeshPolygonComponent)
        fnComponent.addElements(faceIndices)

        selection.add((dagPath, component))
        fnSet.addMembers(selection)
        selection.clear()


def triangulate(mesh):
    """
    Returns a triangulated mesh that won't be written on file save.

    :type mesh: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MObject
    """

    # Check if intermediate object exists
    #
    mesh = dagutils.getMObject(mesh)
    transform = dagutils.getParent(mesh)

    intermediates = tuple(dagutils.iterIntermediateObjects(transform, apiType=om.MFn.kMesh))
    numIntermediates = len(intermediates)

    intermediate = None

    if numIntermediates == 0:

        intermediate = mesh

    else:

        intermediate = intermediates[0]

    # Copy mesh to intermediate object
    #
    parentName = dagutils.getNodeName(transform)
    newName = f'{parentName}ShapeTri'
    exists = mc.objExists(newName)

    fnMesh = om.MFnMesh()
    newMesh = None

    if exists:

        newMesh = dagutils.getMObject(newName)
        fnMesh.setObject(newMesh)
        fnMesh.copyInPlace(intermediate)

    else:

        newMesh = fnMesh.copy(intermediate, parent=transform)

    fnMesh.setName(newName)
    fnMesh.setDoNotWrite(True)
    fnMesh.isIntermediateObject = True

    transferShaders(mesh, newMesh)

    # Triangulate intermediate object
    #
    newFullPathName = dagutils.getMDagPath(newMesh).fullPathName()

    mc.polyTriangulate(newFullPathName)
    mc.bakePartialHistory(newFullPathName, prePostDeformers=True)

    return newMesh
