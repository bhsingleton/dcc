"""
Python module dedicated to manipulating transform data.
This module uses the Maya python API 2.0
"""
import math

from maya import cmds as mc
from maya.api import OpenMaya as om
from six import string_types
from dcc.maya.decorators import undo
from dcc.maya.libs import dagutils, plugutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


EULER_ROTATE_ORDER = {
    0: om.MEulerRotation.kXYZ,
    1: om.MEulerRotation.kYZX,
    2: om.MEulerRotation.kZXY,
    3: om.MEulerRotation.kXZY,
    4: om.MEulerRotation.kYXZ,
    5: om.MEulerRotation.kZYX
}


TRANSFORM_ROTATE_ORDER = {
    0: om.MTransformationMatrix.kXYZ,
    1: om.MTransformationMatrix.kYZX,
    2: om.MTransformationMatrix.kZXY,
    3: om.MTransformationMatrix.kXZY,
    4: om.MTransformationMatrix.kYXZ,
    5: om.MTransformationMatrix.kZYX
}


def getTranslation(dagPath, space=om.MSpace.kTransform, context=om.MDGContext.kNormal):
    """
    Returns the translation values from the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type space: int
    :type context: om.MDGContext
    :rtype: om.MVector
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('getTranslation() expects a valid dag path!')

    # Inspect transform space
    #
    if space == om.MSpace.kWorld:

        return decomposeTransformMatrix(dagPath.inclusiveMatrix())[0]

    else:

        # Get translate values from plugs
        #
        fnTransform = om.MFnTransform(dagPath)

        translation = om.MVector(
            fnTransform.findPlug('translateX', False).asFloat(context=context),
            fnTransform.findPlug('translateY', False).asFloat(context=context),
            fnTransform.findPlug('translateZ', False).asFloat(context=context)
        )

        return translation


def setTranslation(dagPath, translation, **kwargs):
    """
    Updates the translation values on the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type translation: om.MVector
    :key space: int
    :key skipTranslate: bool
    :key skipTranslateX: bool
    :key skipTranslateY: bool
    :key skipTranslateZ: bool
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('setTranslation() expects a valid dag path!')

    # Inspect transform space
    #
    space = kwargs.get('space', om.MSpace.kTransform)

    if space == om.MSpace.kWorld:

        translation *= dagPath.exclusiveMatrixInverse()

    # Initialize transform function set
    #
    fnTransform = om.MFnTransform(dagPath)
    skipTranslate = kwargs.get('skipTranslate', False)

    # Check if translateX can be set
    #
    skipTranslateX = kwargs.get('skipTranslateX', skipTranslate)
    translateXPlug = fnTransform.findPlug('translateX', True)

    if not skipTranslateX and not translateXPlug.isLocked:

        translateXPlug.setDouble(translation.x)

    # Check if translateY can be set
    #
    skipTranslateY = kwargs.get('skipTranslateY', skipTranslate)
    translateYPlug = fnTransform.findPlug('translateY', True)

    if not skipTranslateY and not translateYPlug.isLocked:

        translateYPlug.setDouble(translation.y)

    # Check if translateZ can be set
    #
    skipTranslateZ = kwargs.get('skipTranslateZ', skipTranslate)
    translateZPlug = fnTransform.findPlug('translateZ', True)

    if not skipTranslateZ and not translateZPlug.isLocked:

        translateZPlug.setDouble(translation.z)


def resetTranslation(dagPath):
    """
    Resets the translation values on the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setTranslation(dagPath, om.MVector.kZeroVector)


def getRotationOrder(dagPath, context=om.MDGContext.kNormal):
    """
    Returns the rotation order from the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type context: om.MDGContext
    :rtype: int
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('getEulerRotation() expects a valid dag path!')

    # Get euler values from plugs
    #
    fnTransform = om.MFnTransform(dagPath)
    rotateOrder = fnTransform.findPlug('rotateOrder', False).asInt(context=context)

    return rotateOrder


def getEulerRotation(dagPath, context=om.MDGContext.kNormal):
    """
    Updates the euler angles on the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type context: om.MDGContext
    :rtype: om.MEulerRotation
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('getEulerRotation() expects a valid dag path!')

    # Get euler values from plugs
    #
    fnTransform = om.MFnTransform(dagPath)
    rotateOrder = getRotationOrder(dagPath)

    return om.MEulerRotation(
        fnTransform.findPlug('rotateX', False).asMAngle(context=context).asRadians(),
        fnTransform.findPlug('rotateY', False).asMAngle(context=context).asRadians(),
        fnTransform.findPlug('rotateZ', False).asMAngle(context=context).asRadians(),
        order=rotateOrder
    )


def setEulerRotation(dagPath, rotation, **kwargs):
    """
    Updates the euler angles on the supplied node.

    :type dagPath: om.MDagPath
    :type rotation: om.MEulerRotation
    :key skipRotate: bool
    :key skipRotateX: bool
    :key skipRotateY: bool
    :key skipRotateZ: bool
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('setEulerRotation() expects a valid dag path!')

    # Initialize transform function set
    #
    fnTransform = om.MFnTransform(dagPath)
    skipRotate = kwargs.get('skipRotate', False)

    # Check if rotateX can be set
    #
    skipRotateX = kwargs.get('skipRotateX', skipRotate)
    rotateXPlug = fnTransform.findPlug('rotateX', True)

    if not skipRotateX and not rotateXPlug.isLocked:

        rotateXPlug.setMAngle(om.MAngle(rotation.x, om.MAngle.kRadians))

    # Check if rotateY can be set
    #
    skipRotateY = kwargs.get('skipRotateY', skipRotate)
    rotateYPlug = fnTransform.findPlug('rotateY', True)

    if not skipRotateY and not rotateYPlug.isLocked:

        rotateYPlug.setMAngle(om.MAngle(rotation.y, om.MAngle.kRadians))

    # Check if rotateZ can be set
    #
    skipRotateZ = kwargs.get('skipRotateZ', skipRotate)
    rotateZPlug = fnTransform.findPlug('rotateZ', True)

    if not skipRotateZ and not rotateZPlug.isLocked:

        rotateZPlug.setMAngle(om.MAngle(rotation.z, om.MAngle.kRadians))


def resetEulerRotation(dagPath):
    """
    Resets the euler angles on the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setEulerRotation(dagPath, om.MEulerRotation.kIdentity)


def getJointOrient(dagPath, context=om.MDGContext.kNormal):
    """
    Returns the joint orient angles from the supplied node.
    If the node is not derived from a joint then a zero euler rotation is returned.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type context: om.MDGContext
    :rtype: om.MEulerRotation
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('getJointOrient() expects a valid dag path!')

    # Get euler values from plugs
    #
    fnTransform = om.MFnTransform(dagPath)
    jointOrient = om.MEulerRotation()

    if dagPath.hasFn(om.MFn.kJoint):

        return om.MEulerRotation(
            fnTransform.findPlug('jointOrientX', False).asMAngle(context=context).asRadians(),
            fnTransform.findPlug('jointOrientY', False).asMAngle(context=context).asRadians(),
            fnTransform.findPlug('jointOrientZ', False).asMAngle(context=context).asRadians()
        )

    return jointOrient


def setJointOrient(dagPath, jointOrient):
    """
    Updates the joint orient angles on the supplied joint.
    If the node is not derived from a joint then no changes are made.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type jointOrient: om.MEulerRotation
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('setJointOrient() expects a valid dag path!')

    # Update joint orient plugs
    #
    fnTransform = om.MFnTransform(dagPath)

    if dagPath.hasFn(om.MFn.kJoint):

        fnTransform.findPlug('jointOrientX', False).setMAngle(om.MAngle(jointOrient.x, om.MAngle.kRadians))
        fnTransform.findPlug('jointOrientY', False).setMAngle(om.MAngle(jointOrient.y, om.MAngle.kRadians))
        fnTransform.findPlug('jointOrientZ', False).setMAngle(om.MAngle(jointOrient.z, om.MAngle.kRadians))


def resetJointOrient(dagPath):
    """
    Resets the joint orient angles on the supplied joint.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setJointOrient(dagPath, om.MEulerRotation.kIdentity)


def getScale(dagPath, context=om.MDGContext.kNormal):
    """
    Returns the scale values from the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type context: om.MDGContext
    :rtype: list[float, float, float]
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('getScale() expects a valid dag path!')

    # Get scale values from plugs
    #
    fnTransform = om.MFnTransform(dagPath)

    return [
        fnTransform.findPlug('scaleX', False).asFloat(context=context),
        fnTransform.findPlug('scaleY', False).asFloat(context=context),
        fnTransform.findPlug('scaleZ', False).asFloat(context=context)
    ]


def setScale(dagPath, scale, **kwargs):
    """
    Updates the scale values on the supplied node.

    :type dagPath: om.MDagPath
    :type scale: list[float, float, float]
    :key skipScale: bool
    :key skipScaleX: bool
    :key skipScaleY: bool
    :key skipScaleZ: bool
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('setScale() expects a valid dag path!')

    # Initialize transform function set
    #
    fnTransform = om.MFnTransform(dagPath)
    skipScale = kwargs.get('skipScale', False)

    # Check if scaleX can be set
    #
    skipScaleX = kwargs.get('skipScaleX', skipScale)
    scaleXPlug = fnTransform.findPlug('scaleX', True)

    if not skipScaleX and not scaleXPlug.isLocked:

        scaleXPlug.setDouble(scale[0])

    # Check if scaleY can be set
    #
    skipScaleY = kwargs.get('skipScaleY', skipScale)
    scaleYPlug = fnTransform.findPlug('scaleY', True)

    if not skipScaleY and not scaleYPlug.isLocked:

        scaleYPlug.setDouble(scale[1])

    # Check if scaleZ can be set
    #
    skipScaleZ = kwargs.get('skipScaleZ', skipScale)
    scaleZPlug = fnTransform.findPlug('scaleZ', True)

    if not skipScaleZ and not scaleZPlug.isLocked:

        scaleZPlug.setDouble(scale[2])


def resetScale(dagPath):
    """
    Resets the scale values on the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setScale(dagPath, [1.0, 1.0, 1.0])


def resetPivots(dagPath):
    """
    Resets all of the pivot components for the given dag path.

    :type dagPath: om.MDagPath
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('resetPivot() expects a valid dag path!')

    # Initialize function set
    #
    fnTransform = om.MFnTransform(dagPath)

    # Reset rotation pivot
    #
    fnTransform.setRotatePivot(om.MPoint.kOrigin, om.MSpace.kTransform, False)
    fnTransform.setRotatePivotTranslation(om.MVector.kZeroVector, om.MSpace.kTransform)

    # Reset scale pivot
    #
    fnTransform.setScalePivot(om.MPoint.kOrigin, om.MSpace.kTransform, False)
    fnTransform.setScalePivotTranslation(om.MVector.kZeroVector, om.MSpace.kTransform)


def getBoundingBox(dagPath):
    """
    Returns the bounding box for the given dag path.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MBoundingBox
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('getBoundingBox() expects a valid dag path!')

    # Return bounding box
    #
    return om.MFnDagNode(dagPath).boundingBox


@undo.undo(name='Apply Transform Matrix')
def applyTransformMatrix(dagPath, matrix, **kwargs):
    """
    Applies the transform matrix to the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type matrix: om.MMatrix
    :key skipTranslateX: bool
    :key skipTranslateY: bool
    :key skipTranslateZ: bool
    :key skipRotateX: bool
    :key skipRotateY: bool
    :key skipRotateZ: bool
    :key preserveChildren: bool
    :rtype: None
    """

    # Check argument types
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid() or not isinstance(matrix, om.MMatrix):

        raise TypeError('applyTransformMatrix() expects a MDagPath and MMatrix!')

    # Initialize transformation matrix
    #
    partialPathName = dagPath.partialPathName()
    transformationMatrix = om.MTransformationMatrix(matrix)

    rotateOrder = getRotationOrder(dagPath)
    transformationMatrix.reorderRotation(rotateOrder + 1)  # MTransformationMatrix rotation orders are off by 1...

    # Set translation
    #
    translate = transformationMatrix.translation(om.MSpace.kTransform)
    setTranslation(dagPath, translate, **kwargs)

    log.debug('%s.translate = [%s, %s, %s]' % (partialPathName, translate.x, translate.y, translate.z))

    # Check if dag path belongs to a joint
    # If it does then we need to compensate for any joint orientations
    #
    if dagPath.hasFn(om.MFn.kJoint):

        jointOrient = getJointOrient(dagPath)
        transformationMatrix.rotateBy(jointOrient.inverse(), om.MSpace.kTransform)

    # Set euler rotation
    #
    rotate = transformationMatrix.rotation(asQuaternion=False)
    setEulerRotation(dagPath, rotate, **kwargs)

    log.debug('%s.rotate = [%s, %s, %s]' % (partialPathName, rotate.x, rotate.y, rotate.z))

    # Check if scale should be skipped
    #
    scale = transformationMatrix.scale(om.MSpace.kTransform)
    setScale(dagPath, scale, **kwargs)

    log.debug('%s.scale = [%s, %s, %s]' % (partialPathName, scale[0], scale[1], scale[2]))


def applyWorldMatrix(dagPath, worldMatrix, **kwargs):
    """
    Applies the world transformation matrix to the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type worldMatrix: om.MMatrix
    :key skipTranslateX: bool
    :key skipTranslateY: bool
    :key skipTranslateZ: bool
    :key skipRotateX: bool
    :key skipRotateY: bool
    :key skipRotateZ: bool
    :key preserveChildren: bool
    :rtype: None
    """

    # Check argument types
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid() or not isinstance(worldMatrix, om.MMatrix):

        raise TypeError('applyWorldMatrix() expects a MDagPath and MMatrix!')

    # Convert world matrix to parent space
    #
    parentInverseMatrix = dagPath.exclusiveMatrixInverse()
    matrix = worldMatrix * parentInverseMatrix

    applyTransformMatrix(dagPath, matrix)


def copyTransform(*args, **kwargs):
    """
    Copies the transform matrix from one node to another.
    This method only accepts two arguments, the source and then target node.

    :rtype: None
    """

    # Check number of arguments
    #
    numArgs = len(args)

    if numArgs != 2:

        raise TypeError('copyTransform() expects 2 arguments (%s given)!' % numArgs)

    # Check argument types
    #
    copyFrom = dagutils.getMDagPath(args[0])
    copyTo = dagutils.getMDagPath(args[1])

    if not copyFrom.isValid() and not copyTo.isValid():

        raise TypeError('copyTransform() expects 2 valid dag paths!')

    # Get position matrices
    #
    fnTransform = om.MFnTransform(copyFrom)

    translation = fnTransform.translation(om.MSpace.kTransform)
    rotatePivot = fnTransform.rotatePivot(om.MSpace.kTransform)
    rotatePivotTranslate = fnTransform.rotatePivotTranslation(om.MSpace.kTransform)
    scalePivot = fnTransform.scalePivot(om.MSpace.kTransform)
    scalePivotTranslate = fnTransform.scalePivotTranslation(om.MSpace.kTransform)

    translateMatrix = createTranslateMatrix(translation)
    rotatePivotMatrix = createTranslateMatrix(rotatePivot)
    rotatePivotTranslateMatrix = createTranslateMatrix(rotatePivotTranslate)
    scalePivotMatrix = createTranslateMatrix(scalePivot)
    scalePivotTranslateMatrix = createTranslateMatrix(scalePivotTranslate)

    # Get rotation matrices
    #
    rotation = fnTransform.rotation(asQuaternion=False)
    orientation = fnTransform.rotateOrientation(om.MSpace.kTransform)

    rotationMatrix = rotation.asMatrix()
    orientationMatrix = orientation.asMatrix()

    # Get joint orient matrix
    #
    jointOrientMatrix = om.MMatrix.kIdentity

    if copyFrom.hasFn(om.MFn.kJoint):

        jointOrientMatrix = getJointOrient(copyFrom).asMatrix()

    # Get scale matrix
    #
    scale = fnTransform.scale()
    scaleMatrix = createScaleMatrix(scale)

    # Get parent matrices
    #
    parentMatrix = copyFrom.exclusiveMatrix()
    parentInverseMatrix = copyTo.exclusiveMatrixInverse()

    # Compose local matrix
    #
    matrix = scalePivotMatrix * scaleMatrix * scalePivotTranslateMatrix * rotatePivotMatrix * rotationMatrix * jointOrientMatrix * rotatePivotTranslateMatrix * translateMatrix
    worldMatrix = matrix * parentMatrix

    log.debug('Composed world matrix: %s' % worldMatrix)
    newMatrix = worldMatrix * parentInverseMatrix

    # Apply matrix to target
    #
    applyTransformMatrix(copyTo, newMatrix, **kwargs)


def freezeTransform(dagPath, includeTranslate=True, includeRotate=True, includeScale=False):
    """
    Pushes the transform's local matrix into the parent offset matrix.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type includeTranslate: bool
    :type includeRotate: bool
    :type includeScale: bool
    :rtype: None
    """

    # Check if translation should be frozen
    #
    if includeTranslate:

        freezeTranslation(dagPath)

    # Check if rotation should be frozen
    #
    if includeRotate:

        freezeRotation(dagPath)

    # Check if scale should be frozen
    #
    if includeScale:

        freezeScale(dagPath)


def unfreezeTransform(dagPath):
    """
    Pushes the transform's parent offset matrix into the local matrix.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('unfreezeTransform() expects a valid dag path!')

    # Get the offset parent matrix
    #
    fnTransform = om.MFnTransform(dagPath)
    plug = fnTransform.findPlug('offsetParentMatrix', True)

    offsetParentMatrixData = plug.asMObject()
    offsetParentMatrix = getMatrixData(offsetParentMatrixData)

    # Check for redundancy
    #
    if offsetParentMatrix == om.MMatrix.kIdentity:

        log.debug('Transform has already been unfrozen: %s' % fnTransform.partialPathName())
        return

    # Get local matrix
    # If there is transform data then we need to compound it
    #
    matrixData = fnTransform.findPlug('matrix', False).asMObject()
    matrix = getMatrixData(matrixData)

    if matrix != om.MMatrix.kIdentity:

        offsetParentMatrix *= matrix

    # Decompose offset parent matrix
    #
    rotateOrder = getRotationOrder(dagPath)
    translate, rotate, scale = decomposeTransformMatrix(offsetParentMatrix, rotateOrder=rotateOrder)

    # Commit transform components to node
    #
    setTranslation(dagPath, translate)
    setEulerRotation(dagPath, rotate)
    setScale(dagPath, scale)

    # Reset offset parent matrix plug
    #
    plug.setMObject(identityMatrixData())


def freezeTranslation(dagPath):
    """
    Freezes the translation values on the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Create translation matrix
    #
    translateMatrix = createTranslateMatrix(dagPath)
    resetTranslation(dagPath)

    # Check if offset requires compounding
    #
    offsetParentMatrix = getOffsetParentMatrix(dagPath)

    if offsetParentMatrix != om.MMatrix.kIdentity:

        translateMatrix *= offsetParentMatrix

    # Commit offset parent matrix to plug
    #
    updateOffsetParentMatrix(dagPath, translateMatrix)


def freezeRotation(dagPath):
    """
    Freezes the rotation values on the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Create rotation matrix
    #
    rotateMatrix = createRotationMatrix(dagPath)
    resetEulerRotation(dagPath)

    # Check if offset requires compounding
    #
    offsetParentMatrix = getOffsetParentMatrix(dagPath)

    if offsetParentMatrix != om.MMatrix.kIdentity:

        rotateMatrix *= offsetParentMatrix

    # Commit offset parent matrix to plug
    #
    updateOffsetParentMatrix(dagPath, rotateMatrix)


def freezeScale(dagPath):
    """
    Bakes the transform's scale matrix into all of the transform's child descendants.
    Unlike translation and rotation, scale cannot be unfrozen.
    Technically we could push the scale into the offsetParentMatrix but scale loves to break shit!

    :type dagPath: om.MDagPath
    :rtype: None
    """

    # Iterate through all descendants
    #
    dagPath = dagutils.getMDagPath(dagPath)
    scaleMatrix = createScaleMatrix(dagPath)

    for child in dagutils.iterDescendants(dagPath):

        # Check api type
        #
        if child.hasFn(om.MFn.kTransform):

            # Scale node's translation
            #
            translation = getTranslation(child)
            translation *= scaleMatrix

            setTranslation(child, translation)

        elif child.hasFn(om.MFn.kNurbsCurve):

            # Scale control points
            #
            fnMesh = om.MFnNurbsCurve(child)
            controlPoints = fnMesh.cvPositions()

            for i in range(fnMesh.numCVs):
                controlPoints[i] *= scaleMatrix

            fnMesh.setCVPositions(controlPoints)

        elif child.hasFn(om.MFn.kNurbsSurface):

            # Scale control points
            #
            fnMesh = om.MFnNurbsCurve(child)
            controlPoints = fnMesh.cvPositions()

            for i in range(fnMesh.numCVs):
                controlPoints[i] *= scaleMatrix

            fnMesh.setCVPositions(controlPoints)

        elif child.hasFn(om.MFn.kLocator):

            # Initialize function set
            #
            fnDagNode = om.MFnDagNode(child)

            # Scale local position
            #
            plug = fnDagNode.findPlug('localPosition', True)

            localPosition = om.MVector(plugutils.getValue(plug))
            localPosition *= scaleMatrix

            plugutils.setValue(plug, localPosition)

            # Scale local scale
            #
            plug = fnDagNode.findPlug('localScale', True)

            localScale = om.MVector(plugutils.getValue(plug))
            localScale *= scaleMatrix

            plugutils.setValue(plug, localScale)

        elif child.hasFn(om.MFn.kMesh):

            # Scale control points
            #
            fnMesh = om.MFnMesh(child)
            controlPoints = fnMesh.getPoints()

            for i in range(fnMesh.numVertices):
                controlPoints[i] *= scaleMatrix

            fnMesh.setPoints(controlPoints)

        else:

            log.warning('Unable to bake scale into: %s api type!' % child.apiTypStr)
            continue

    # Reset scale on transform
    #
    resetScale(dagPath)


def matrixToList(matrix):
    """
    Converts the supplied value to a matrix list comprised of 16 float values.

    :type matrix: Union[om.MMatrix, om.MTransformationMatrix and om.MFnMatrixData]
    :rtype: tuple[float, float, float, float, float, float, float, float, float, float, float, float]
    """

    # Query variable type
    #
    if not isinstance(matrix, om.MMatrix):

        raise TypeError('matrixToList() expects an MMatrix (%s given)!' % type(matrix).__name__)

    # Extract each row into a list
    #
    matrixList = (
        matrix.getElement(0, 0), matrix.getElement(0, 1), matrix.getElement(0, 2), 0.0,
        matrix.getElement(1, 0), matrix.getElement(1, 1), matrix.getElement(1, 2), 0.0,
        matrix.getElement(2, 0), matrix.getElement(2, 1), matrix.getElement(2, 2), 0.0,
        matrix.getElement(3, 0), matrix.getElement(3, 1), matrix.getElement(3, 2), 1.0,
    )

    return matrixList


def listToMatrix(matrixList):
    """
    Converts a list of values into a matrix.

    :type matrixList: list[float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]
    :rtype: om.MMatrix
    """

    # Check value type
    #
    if not isinstance(matrixList, (list, tuple)):

        raise TypeError('listToMatrix() expects a list (%s given)!' % type(matrixList).__name__)

    # Check if there are enough items
    #
    numItems = len(matrixList)

    if numItems == 16:

        return om.MMatrix(
            [
                (matrixList[0], matrixList[1], matrixList[2], matrixList[3]),
                (matrixList[4], matrixList[5], matrixList[6], matrixList[7]),
                (matrixList[8], matrixList[9], matrixList[10], matrixList[11]),
                (matrixList[12], matrixList[13], matrixList[14], matrixList[15])
            ]
        )

    elif numItems == 4:

        return om.MMatrix(matrixList)

    else:

        raise TypeError('listToMatrix() expects either 4 or 16 items (%s given)!' % numItems)


def getMatrix(dagPath, context=om.MDGContext.kNormal):
    """
    Returns the transform matrix for the given node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type context: om.MDGContext
    :rtype: om.MMatrix
    """

    # Get matrix plug
    #
    dagPath = dagutils.getMDagPath(dagPath)
    fnTransform = om.MFnTransform(dagPath)

    plug = fnTransform.findPlug('matrix', True)
    matrixData = plug.asMObject(context=context)

    # Convert matrix data
    #
    return getMatrixData(matrixData)


def getOffsetParentMatrix(dagPath, context=om.MDGContext.kNormal):
    """
    Returns the offset parent matrix for the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type context: om.MDGContext
    :rtype: om.MMatrix
    """

    # Get offset parent matrix plug
    #
    dagPath = dagutils.getMDagPath(dagPath)
    fnTransform = om.MFnTransform(dagPath)

    plug = fnTransform.findPlug('offsetParentMatrix', True)
    offsetParentMatrixData = plug.asMObject(context=context)

    # Convert matrix data
    #
    return getMatrixData(offsetParentMatrixData)


def updateOffsetParentMatrix(dagPath, offsetParentMatrix):
    """
    Updates the offset parent matrix for the supplied node.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type offsetParentMatrix: om.MMatrix
    :rtype: None
    """

    # Get offset parent matrix plug
    #
    dagPath = dagutils.getMDagPath(dagPath)
    fnTransform = om.MFnTransform(dagPath)

    plug = fnTransform.findPlug('offsetParentMatrix', True)
    offsetParentMatrixData = createMatrixData(offsetParentMatrix)

    # Assign matrix data to plug
    #
    plug.setMObject(offsetParentMatrixData)


def getMatrixData(matrixData):
    """
    Converts the given MObject to an MMatrix.

    :type matrixData: om.MObject
    :rtype: om.MMatrix
    """

    # Check for redundancy
    #
    if isinstance(matrixData, om.MMatrix):

        return matrixData

    else:

        return om.MFnMatrixData(matrixData).matrix()


def createMatrixData(matrix):
    """
    Converts the given matrix to an MObject.

    :type matrix: om.MMatrix
    :rtype: om.MObject
    """

    # Check for redundancy
    #
    if isinstance(matrix, om.MObject):

        return matrix

    # Create new matrix data object
    #
    fnMatrixData = om.MFnMatrixData()
    matrixData = fnMatrixData.create()

    # Update matrix value
    #
    fnMatrixData.set(matrix)

    return matrixData


def identityMatrixData():
    """
    Returns an identity matrix in the form of an MObject.
    This is useful for resetting plug values.

    :rtype: om.MObject
    """

    return createMatrixData(om.MMatrix.kIdentity)


def createTranslateMatrix(value):
    """
    Creates a position matrix based on the supplied value.

    :type value: Union[str, list, tuple, om.MMatrix, om.MVector, om.MPoint]
    :rtype: om.MMatrix
    """

    # Check value type
    #
    if isinstance(value, (om.MPoint, om.MVector)):

        # Compose new matrix
        #
        return om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (value.x, value.y, value.z, 1.0)
            ]
        )

    elif isinstance(value, (list, tuple)):

        return createTranslateMatrix(om.MVector(value))

    elif isinstance(value, om.MMatrix):

        return createTranslateMatrix([value.getElement(3, 0), value.getElement(3, 1), value.getElement(3, 2)])

    elif isinstance(value, om.MTransformationMatrix):

        return createTranslateMatrix(value.asMatrix())

    elif isinstance(value, string_types) or isinstance(value, (om.MObject, om.MDagPath)):

        return createTranslateMatrix(getTranslation(value))

    elif isinstance(value, (om.MObject, om.MDagPath)):

        return createTranslateMatrix(getTranslation(value))

    else:

        raise TypeError('createTranslateMatrix() expects an MVector (%s given)!' % type(value).__name__)


def createRotationMatrix(value):
    """
    Creates a rotation matrix based on the supplied value.
    Degrees should not be used for any of these methods!

    :type value: Union[str, list, tuple, om.MEulerRotation, om.MMatrix, om.MTransformationMatrix]
    :rtype: om.MMatrix
    """

    # Check variable type
    #
    if isinstance(value, om.MEulerRotation):

        # Compose rotation components
        #
        rotateXMatrix = om.MMatrix(
            [
                (1.0, 0.0, 0.0, 0.0),
                (0.0, math.cos(value.x), math.sin(value.x), 0.0),
                (0.0, -math.sin(value.x), math.cos(value.x), 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

        rotateYMatrix = om.MMatrix(
            [
                (math.cos(value.y), 0.0, -math.sin(value.y), 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (math.sin(value.y), 0.0, math.cos(value.y), 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

        rotateZMatrix = om.MMatrix(
            [
                (math.cos(value.z), math.sin(value.z), 0.0, 0.0),
                (-math.sin(value.z), math.cos(value.z), 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

        # Multiply components based on rotation order
        #
        rotateMatrix = om.MMatrix.kIdentity

        if value.order == om.MEulerRotation.kXYZ:  # xyz

            rotateMatrix = rotateXMatrix * rotateYMatrix * rotateZMatrix

        elif value.order == om.MEulerRotation.kYZX:  # yzx

            rotateMatrix = rotateYMatrix * rotateZMatrix * rotateXMatrix

        elif value.order == om.MEulerRotation.kZXY:  # zxy

            rotateMatrix = rotateZMatrix * rotateXMatrix * rotateYMatrix

        elif value.order == om.MEulerRotation.kXZY:  # xzy

            rotateMatrix = rotateXMatrix * rotateZMatrix * rotateYMatrix

        elif value.order == om.MEulerRotation.kYXZ:  # yxz

            rotateMatrix = rotateYMatrix * rotateXMatrix * rotateZMatrix

        elif value.order == om.MEulerRotation.kZYX:  # zyx

            rotateMatrix = rotateZMatrix * rotateYMatrix * rotateXMatrix

        else:

            raise TypeError('createRotationMatrix() expects a valid rotation order (%s given)!' % value.order)

        return rotateMatrix

    elif isinstance(value, om.MQuaternion):

        return value.asMatrix()

    elif isinstance(value, om.MMatrix):

        return om.MMatrix(
            [
                (value.getElement(0, 0), value.getElement(0, 1), value.getElement(0, 2), 0.0),
                (value.getElement(1, 0), value.getElement(1, 1), value.getElement(1, 2), 0.0),
                (value.getElement(2, 0), value.getElement(2, 1), value.getElement(2, 2), 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

    elif isinstance(value, om.MTransformationMatrix):

        return createRotationMatrix(value.asMatrix())

    elif isinstance(value, (list, tuple)):

        return createRotationMatrix(om.MEulerRotation([math.radians(x) for x in value], EULER_ROTATE_ORDER[0]))

    elif isinstance(value, string_types) or isinstance(value, (om.MObject, om.MDagPath)):

        return createRotationMatrix(getEulerRotation(value))

    else:

        raise TypeError('createRotationMatrix() expects an MEulerRotation (%s given)!' % type(value).__name__)


def createAimMatrix(forwardAxis, forwardVector, upAxis, upVector, startPoint=om.MPoint.kOrigin, forwardAxisSign=1, upAxisSign=1):
    """
    Creates an aim matrix based on the supplied values.

    :type forwardAxis: int
    :type forwardVector: om.MVector
    :type upAxis: int
    :type upVector: om.MVector
    :type startPoint: Union[om.MVector, om.MPoint]
    :type forwardAxisSign: int
    :type upAxisSign: int
    :rtype: om.MMatrix
    """

    # Check which forward axis is selected
    #
    xAxis = om.MVector.kXaxisVector  # type: om.MVector
    yAxis = om.MVector.kYaxisVector  # type: om.MVector
    zAxis = om.MVector.kZaxisVector  # type: om.MVector

    if forwardAxis == 0:

        xAxis = forwardVector * forwardAxisSign

        if upAxis == 1:

            zAxis = xAxis ^ (upVector * upAxisSign)
            yAxis = zAxis ^ xAxis

        elif upAxis == 2:

            yAxis = (upVector * upAxisSign) ^ xAxis
            zAxis = xAxis ^ yAxis

        else:

            raise TypeError('createAimMatrix() expects a unique up axis (%s given)!' % upAxis)

    elif forwardAxis == 1:

        yAxis = forwardVector * forwardAxisSign

        if upAxis == 0:

            zAxis = (upVector * upAxisSign) ^ yAxis
            xAxis = yAxis ^ zAxis

        elif upAxis == 2:

            xAxis = yAxis ^ (upVector * upAxisSign)
            zAxis = xAxis ^ yAxis

        else:

            raise TypeError('createAimMatrix() expects a unique up axis (%s given)!' % upAxis)

    elif forwardAxis == 2:

        zAxis = forwardVector * forwardAxisSign

        if upAxis == 0:

            yAxis = zAxis ^ (upVector * upAxisSign)
            xAxis = yAxis ^ zAxis

        elif upAxis == 1:

            xAxis = (upVector * upAxisSign) ^ zAxis
            yAxis = zAxis ^ xAxis

        else:

            raise TypeError('createAimMatrix() expects a unique up axis (%s given)!' % upAxis)

    else:

        raise TypeError('createAimMatrix() expects a valid forward axis (%s given)!' % forwardAxis)

    # Normalize axis vectors
    #
    xAxis.normalize()
    yAxis.normalize()
    zAxis.normalize()

    # Compose aim matrix from axis vectors
    #
    return om.MMatrix(
        [
            (xAxis.x, xAxis.y, xAxis.z, 0.0),
            (yAxis.x, yAxis.y, yAxis.z, 0.0),
            (zAxis.x, zAxis.y, zAxis.z, 0.0),
            (startPoint.x, startPoint.y, startPoint.z, 1.0)
        ]
    )


def createAxisMatrix(axis):
    """
    Creates a rotation matrix to get to the given axis vector.

    :type axis: om.MVector
    :rtype: om.MMatrix
    """

    return om.MVector.kXaxisVector.rotateTo(axis).asMatrix()


def createScaleMatrix(value):
    """
    Creates a scale matrix based on the supplied value.

    :type value: Union[str, list, tuple, om.MMatrix, om.MVector]
    :rtype: om.MMatrix
    """

    # Check value type
    #
    if isinstance(value, (list, tuple)):

        # Check number of items
        #
        numItems = len(value)

        if numItems != 3:

            raise TypeError('createScaleMatrix() expects 3 values (%s given)!' % numItems)

        # Compose scale matrix
        #
        return om.MMatrix(
            [
                (value[0], 0.0, 0.0, 0.0),
                (0.0, value[1], 0.0, 0.0),
                (0.0, 0.0, value[2], 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

    elif isinstance(value, om.MMatrix):

        x, y, z, p = decomposeMatrix(value)
        return createScaleMatrix([x.length(), y.length(), z.length()])

    elif isinstance(value, om.MTransformationMatrix):

        return createScaleMatrix(value.asMatrix())

    elif isinstance(value, string_types) or isinstance(value, (om.MObject, om.MDagPath)):

        return createScaleMatrix(getScale(value))

    elif isinstance(value, (int, float)):

        return createScaleMatrix([value, value, value])

    else:

        raise TypeError('createScaleMatrix() expects a list (%s given)!' % type(value).__name__)


def decomposeTransformNode(dagPath, space=om.MSpace.kTransform):
    """
    Decomposes a node's transformation matrix into separate translate, rotate and scale components.

    :type dagPath: Union[str, om.MObject, om.MDagPath]
    :type space: int
    :rtype: om.MVector, om.MEulerRotation, list[float, float, float]
    """

    dagPath = dagutils.getMDagPath(dagPath)
    rotateOrder = getRotationOrder(dagPath)

    if space == om.MSpace.kWorld:

        worldMatrix = dagPath.inclusiveMatrix()
        return decomposeTransformMatrix(worldMatrix, rotateOrder=rotateOrder)

    else:

        translation = getTranslation(dagPath)
        rotation = getEulerRotation(dagPath)
        scale = getScale(dagPath)

        return translation, rotation, scale


def decomposeTransformMatrix(matrix, rotateOrder=om.MEulerRotation.kXYZ):
    """
    Breaks apart the matrix into its individual translate, rotate and scale components.
    A rotation order must be supplied in order to be resolved correctly.

    :type matrix: Union[str, list, tuple, om.MMatrix, om.MObject]
    :type rotateOrder: int
    :rtype: om.MVector, om.MEulerRotation, list[float, float, float]
    """

    # Check value type
    #
    if isinstance(matrix, om.MMatrix):

        # Reorder rotations
        #
        transformationMatrix = om.MTransformationMatrix(matrix)
        transformationMatrix.reorderRotation(TRANSFORM_ROTATE_ORDER[rotateOrder])

        # Get translate, rotate, and scale components
        #
        translation = transformationMatrix.translation(om.MSpace.kTransform)
        rotation = transformationMatrix.rotation(asQuaternion=False)
        scale = transformationMatrix.scale(om.MSpace.kTransform)

        return translation, rotation, scale

    elif isinstance(matrix, (list, tuple)):

        return decomposeTransformMatrix(listToMatrix(matrix), rotateOrder=rotateOrder)

    elif isinstance(matrix, om.MObject):

        return decomposeTransformMatrix(getMatrixData(matrix), rotateOrder=rotateOrder)

    else:

        raise TypeError('decomposeMatrix() expects an MMatrix (%s given)!' % type(matrix).__name__)


def decomposeMatrix(value, normalize=False):
    """
    Breaks apart value into axis vectors and a position.

    :type value: Union[str, list, tuple, om.MTransformationMatrix, om.MFnMatrixData, om.MMatrix]
    :type normalize: bool
    :rtype: om.MVector, om.MVector, om.MVector, om.MPoint
    """

    # Check value type
    #
    if isinstance(value, om.MMatrix):

        # Extract rows
        #
        x = om.MVector([value.getElement(0, 0), value.getElement(0, 1), value.getElement(0, 2)])
        y = om.MVector([value.getElement(1, 0), value.getElement(1, 1), value.getElement(1, 2)])
        z = om.MVector([value.getElement(2, 0), value.getElement(2, 1), value.getElement(2, 2)])
        p = om.MPoint([value.getElement(3, 0), value.getElement(3, 1), value.getElement(3, 2), value.getElement(3, 3)])

        # Check if vectors should be normalized
        #
        if normalize:

            return x.normal(), y.normal(), z.normal(), p

        else:

            return x, y, z, p

    if isinstance(value, string_types):

        return decomposeMatrix(om.MMatrix(mc.getAttr('%s.worldMatrix[0]' % value)))

    elif isinstance(value, (list, tuple)):

        return decomposeMatrix(om.MMatrix(value))

    elif isinstance(value, om.MTransformationMatrix):

        return decomposeMatrix(value.asMatrix())

    elif isinstance(value, om.MFnMatrixData):

        return decomposeMatrix(value.matrix())

    else:

        raise ValueError('getAxisVectors() expects an MMatrix (%s given)!' % type(value).__name__)


def getMeshComponentCenter(dagPath, component, space=om.MSpace.kTransform):
    """
    Returns the averaged center of all of the supplied mesh components.
    TODO: Implement support for face-vertices!

    :type dagPath: om.MDagPath
    :type component: om.MObject
    :type space: int
    :rtype: om.MPoint
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(dagPath)

    if not dagPath.isValid():

        raise TypeError('getMeshComponentCenter() expects a valid dag path!')

    # Inspect component type
    #
    center = om.MPoint()

    if component.hasFn(om.MFn.kMeshVertComponent):

        # Iterate through vertices
        #
        iterVertices = om.MItMeshVertex(dagPath, component)
        weight = 1.0 / iterVertices.count()

        while not iterVertices.isDone():

            center += iterVertices.position() * weight
            iterVertices.next()

    elif component.hasFn(om.MFn.kMeshEdgeComponent):

        # Iterate through edges
        #
        iterEdges = om.MItMeshEdge(dagPath, component)
        weight = 1.0 / iterEdges.count()

        while not iterEdges.isDone():

            center += iterEdges.center() * weight
            iterEdges.next()

    elif component.hasFn(om.MFn.kMeshPolygonComponent):

        # Iterate through polygons
        #
        iterPolygons = om.MItMeshPolygon(dagPath, component)
        weight = 1.0 / iterPolygons.count()

        while not iterPolygons.isDone():

            center += iterPolygons.center() * weight
            iterPolygons.next()

    else:

        log.warning('getMeshComponentCenter() expects a valid component type (%s given)' % component.apiTypeStr)

    # Inspect transform space
    #
    if space == om.MSpace.kWorld:

        center *= dagPath.exclusiveMatrix()

    return center
