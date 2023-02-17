import math

from maya import cmds as mc
from maya.api import OpenMaya as om
from six import string_types
from dcc.maya.decorators.undo import undo
from dcc.maya.libs import dagutils, plugutils, plugmutators

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


def getTranslation(node, space=om.MSpace.kTransform):
    """
    Returns the translation values from the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type space: int
    :rtype: om.MVector
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

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
            fnTransform.findPlug('translateX', False).asFloat(),
            fnTransform.findPlug('translateY', False).asFloat(),
            fnTransform.findPlug('translateZ', False).asFloat()
        )

        return translation


def setTranslation(node, translation, **kwargs):
    """
    Updates the translation values on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
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
    dagPath = dagutils.getMDagPath(node)

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

        plugmutators.setValue(translateXPlug, translation.x)

    # Check if translateY can be set
    #
    skipTranslateY = kwargs.get('skipTranslateY', skipTranslate)
    translateYPlug = fnTransform.findPlug('translateY', True)

    if not skipTranslateY and not translateYPlug.isLocked:

        plugmutators.setValue(translateYPlug, translation.y)

    # Check if translateZ can be set
    #
    skipTranslateZ = kwargs.get('skipTranslateZ', skipTranslate)
    translateZPlug = fnTransform.findPlug('translateZ', True)

    if not skipTranslateZ and not translateZPlug.isLocked:

        plugmutators.setValue(translateZPlug, translation.z)


def resetTranslation(node):
    """
    Resets the translation values on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setTranslation(node, om.MVector.kZeroVector)


def translateTo(node, position, **kwargs):
    """
    Translates this node to the specified position.
    Unlike `setTranslation`, this method adds the translational difference to the current transform matrix.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type position: om.MVector
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('translateTo() expects a valid dag path!')

    # Calculate translation difference
    #
    currentPosition = getMatrix(dagPath, asTransformationMatrix=True).translation(om.MSpace.kTransform)
    difference = position - currentPosition
    translation = getTranslation(dagPath) + difference

    setTranslation(dagPath, translation, **kwargs)


def getRotationOrder(node):
    """
    Returns the rotation order from the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: int
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('getRotationOrder() expects a valid dag path!')

    # Get euler values from plugs
    #
    fnTransform = om.MFnTransform(dagPath)
    rotateOrder = fnTransform.findPlug('rotateOrder', False).asInt()

    return rotateOrder


def getEulerRotation(node):
    """
    Updates the euler angles on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MEulerRotation
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('getEulerRotation() expects a valid dag path!')

    # Get euler values from plugs
    #
    fnTransform = om.MFnTransform(dagPath)
    rotateOrder = getRotationOrder(dagPath)

    return om.MEulerRotation(
        fnTransform.findPlug('rotateX', False).asMAngle().asRadians(),
        fnTransform.findPlug('rotateY', False).asMAngle().asRadians(),
        fnTransform.findPlug('rotateZ', False).asMAngle().asRadians(),
        order=rotateOrder
    )


def setEulerRotation(node, eulerRotation, **kwargs):
    """
    Updates the euler angles on the supplied node.

    :type node: om.MDagPath
    :type eulerRotation: om.MEulerRotation
    :key skipRotate: bool
    :key skipRotateX: bool
    :key skipRotateY: bool
    :key skipRotateZ: bool
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('setEulerRotation() expects a valid dag path!')

    # Initialize transform function set
    # Update rotate order
    #
    fnTransform = om.MFnTransform(dagPath)

    rotateOrderPlug = fnTransform.findPlug('rotateOrder', True)
    rotateOrderPlug.setInt(eulerRotation.order)

    # Check if rotateX can be set
    #
    skipRotate = kwargs.get('skipRotate', False)
    skipRotateX = kwargs.get('skipRotateX', skipRotate)
    rotateXPlug = fnTransform.findPlug('rotateX', True)

    if not skipRotateX and not rotateXPlug.isLocked:

        plugmutators.setValue(rotateXPlug, om.MAngle(eulerRotation.x, om.MAngle.kRadians))

    # Check if rotateY can be set
    #
    skipRotateY = kwargs.get('skipRotateY', skipRotate)
    rotateYPlug = fnTransform.findPlug('rotateY', True)

    if not skipRotateY and not rotateYPlug.isLocked:

        plugmutators.setValue(rotateYPlug, om.MAngle(eulerRotation.y, om.MAngle.kRadians))

    # Check if rotateZ can be set
    #
    skipRotateZ = kwargs.get('skipRotateZ', skipRotate)
    rotateZPlug = fnTransform.findPlug('rotateZ', True)

    if not skipRotateZ and not rotateZPlug.isLocked:

        plugmutators.setValue(rotateZPlug, om.MAngle(eulerRotation.z, om.MAngle.kRadians))


def resetEulerRotation(node):
    """
    Resets the euler angles on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setEulerRotation(node, om.MEulerRotation.kIdentity)


def rotateTo(node, eulerRotation, **kwargs):
    """
    Rotates this node to the specified orientation.
    Unlike `setEulerRotation`, this method adds the rotational difference to the current transform matrix.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type eulerRotation: om.MEulerRotation
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('rotateTo() expects a valid dag path!')

    # Calculate rotation difference
    #
    rotationMatrix = eulerRotation.asMatrix()
    currentMatrix = getMatrix(node)
    difference = rotationMatrix * currentMatrix.inverse()

    currentEulerRotation = getEulerRotation(node)
    newRotationMatrix = difference * currentEulerRotation.asMatrix()

    newEulerRotation = om.MEulerRotation([0.0, 0.0, 0.0], order=getRotationOrder(node))
    newEulerRotation.setValue(newRotationMatrix)

    setEulerRotation(node, newEulerRotation, **kwargs)


def getJointOrient(joint):
    """
    Returns the joint orient angles from the supplied node.
    If the node is not derived from a joint then a zero euler rotation is returned.

    :type joint: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MEulerRotation
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(joint)

    if not dagPath.isValid():

        raise TypeError('getJointOrient() expects a valid dag path!')

    # Get euler values from plugs
    #
    fnTransform = om.MFnTransform(dagPath)

    if dagPath.hasFn(om.MFn.kJoint):

        return om.MEulerRotation(
            fnTransform.findPlug('jointOrientX', False).asMAngle().asRadians(),
            fnTransform.findPlug('jointOrientY', False).asMAngle().asRadians(),
            fnTransform.findPlug('jointOrientZ', False).asMAngle().asRadians()
        )

    else:

        return om.MEulerRotation()


def setJointOrient(joint, orientation, **kwargs):
    """
    Updates the joint orient angles on the supplied joint.
    If the node is not derived from a joint then no changes are made.

    :type joint: Union[str, om.MObject, om.MDagPath]
    :type orientation: om.MEulerRotation
    :key skipJointOrient: bool
    :key skipJointOrientX: bool
    :key skipJointOrientY: bool
    :key skipJointOrientZ: bool
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(joint)

    if not dagPath.isValid():

        raise TypeError('setJointOrient() expects a valid dag path!')

    # Check if dag path contains a joint
    #
    if not dagPath.hasFn(om.MFn.kJoint):

        raise TypeError('setJointOrient() expects a valid joint!')

    # Initialize transform function set
    # Update rotate order
    #
    fnTransform = om.MFnTransform(dagPath)

    rotateOrderPlug = fnTransform.findPlug('rotateOrder', True)
    orientation.reorderIt(rotateOrderPlug.asInt())

    # Check if rotateX can be set
    #
    skipJointOrient = kwargs.get('skipJointOrient', False)
    skipJointOrientX = kwargs.get('skipJointOrientX', skipJointOrient)
    jointOrientXPlug = fnTransform.findPlug('jointOrientX', True)

    if not skipJointOrientX and not jointOrientXPlug.isLocked:

        plugmutators.setValue(jointOrientXPlug, om.MAngle(orientation.x, om.MAngle.kRadians))

    # Check if rotateY can be set
    #
    skipJointOrientY = kwargs.get('skipJointOrientY', skipJointOrient)
    jointOrientYPlug = fnTransform.findPlug('jointOrientY', True)

    if not skipJointOrientY and not jointOrientYPlug.isLocked:

        plugmutators.setValue(jointOrientYPlug, om.MAngle(orientation.y, om.MAngle.kRadians))

    # Check if rotateZ can be set
    #
    skipJointOrientZ = kwargs.get('skipJointOrientZ', skipJointOrient)
    jointOrientZPlug = fnTransform.findPlug('jointOrientZ', True)

    if not skipJointOrientZ and not jointOrientZPlug.isLocked:

        plugmutators.setValue(jointOrientZPlug, om.MAngle(orientation.z, om.MAngle.kRadians))


def resetJointOrient(joint):
    """
    Resets the joint orient angles on the supplied joint.

    :type joint: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setJointOrient(joint, om.MEulerRotation.kIdentity)


def getScale(node):
    """
    Returns the scale values from the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: list[float, float, float]
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('getScale() expects a valid dag path!')

    # Get scale values from plugs
    #
    fnTransform = om.MFnTransform(dagPath)

    return [
        fnTransform.findPlug('scaleX', False).asFloat(),
        fnTransform.findPlug('scaleY', False).asFloat(),
        fnTransform.findPlug('scaleZ', False).asFloat()
    ]


def setScale(node, scale, **kwargs):
    """
    Updates the scale values on the supplied node.

    :type node: om.MDagPath
    :type scale: Tuple[float, float, float]
    :key skipScale: bool
    :key skipScaleX: bool
    :key skipScaleY: bool
    :key skipScaleZ: bool
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

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

        plugmutators.setValue(scaleXPlug, scale[0])

    # Check if scaleY can be set
    #
    skipScaleY = kwargs.get('skipScaleY', skipScale)
    scaleYPlug = fnTransform.findPlug('scaleY', True)

    if not skipScaleY and not scaleYPlug.isLocked:

        plugmutators.setValue(scaleYPlug, scale[1])

    # Check if scaleZ can be set
    #
    skipScaleZ = kwargs.get('skipScaleZ', skipScale)
    scaleZPlug = fnTransform.findPlug('scaleZ', True)

    if not skipScaleZ and not scaleZPlug.isLocked:

        plugmutators.setValue(scaleZPlug, scale[2])


def resetScale(node):
    """
    Resets the scale values on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setScale(node, [1.0, 1.0, 1.0])


def scaleTo(node, scale, **kwargs):
    """
    Scales this node to the specified size.
    Unlike `setScale`, this method adds the scalar difference to the current transform matrix.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type scale: Union[List[float, float, float], om.MVector]
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('scaleTo() expects a valid dag path!')

    # Calculate scale difference
    #
    currentScale = getMatrix(dagPath, asTransformationMatrix=True).scale(om.MSpace.kTransform)
    difference = om.MVector(scale) - om.MVector(currentScale)
    newScale = om.MVector(getScale(dagPath)) + difference

    setScale(node, newScale, **kwargs)


def resetPivots(node):
    """
    Resets all the pivot components for the given dag path.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

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


def getBoundingBox(node):
    """
    Returns the bounding box for the given dag path.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MBoundingBox
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('getBoundingBox() expects a valid dag path!')

    # Return bounding box
    #
    return om.MFnDagNode(dagPath).boundingBox


@undo(name='Apply Transform Matrix')
def applyTransformMatrix(node, matrix, **kwargs):
    """
    Applies the transform matrix to the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type matrix: om.MMatrix
    :key skipTranslate: bool
    :key skipRotate: bool
    :key skipScale: bool
    :key preserveChildren: bool
    :rtype: None
    """

    # Check argument types
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid() or not isinstance(matrix, om.MMatrix):

        raise TypeError('applyTransformMatrix() expects an MDagPath and MMatrix!')

    # Decompose transform matrix
    #
    partialPathName = dagPath.partialPathName()
    translation, eulerRotation, scale = decomposeTransformMatrix(matrix, rotateOrder=getRotationOrder(dagPath))

    log.debug('%s.translate = [%s, %s, %s]' % (partialPathName, translation.x, translation.y, translation.z))
    translateTo(node, translation, **kwargs)

    log.debug('%s.rotate = [%s, %s, %s]' % (partialPathName, eulerRotation.x, eulerRotation.y, eulerRotation.z))
    rotateTo(node, eulerRotation, **kwargs)

    log.debug('%s.scale = [%s, %s, %s]' % (partialPathName, scale[0], scale[1], scale[2]))
    scaleTo(node, scale, **kwargs)

    # Freeze transform
    #
    freeze = kwargs.get('freezeTransform', False)

    if freeze:

        freezeTransform(node, **kwargs)


def applyWorldMatrix(node, worldMatrix, **kwargs):
    """
    Applies the world transformation matrix to the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
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
    dagPath = dagutils.getMDagPath(node)

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
    matrix = scalePivotMatrix * scaleMatrix * scalePivotTranslateMatrix * rotatePivotMatrix * orientationMatrix * rotationMatrix * jointOrientMatrix * rotatePivotTranslateMatrix * translateMatrix
    worldMatrix = matrix * parentMatrix

    log.debug('Composed world matrix: %s' % worldMatrix)
    newMatrix = worldMatrix * parentInverseMatrix

    # Apply matrix to target
    #
    applyTransformMatrix(copyTo, newMatrix, **kwargs)


@undo(name='Freeze Transform')
def freezeTransform(node, includeTranslate=True, includeRotate=True, includeScale=False):
    """
    Pushes the transform's local matrix into the parent offset matrix.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type includeTranslate: bool
    :type includeRotate: bool
    :type includeScale: bool
    :rtype: None
    """

    # Check if translation should be frozen
    #
    if includeTranslate:

        freezeTranslation(node)

    # Check if rotation should be frozen
    #
    if includeRotate:

        freezeRotation(node)

    # Check if scale should be frozen
    #
    if includeScale:

        freezeScale(node)


def unfreezeTransform(node):
    """
    Pushes the transform's parent offset matrix into the local matrix.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

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


def freezeTranslation(node):
    """
    Freezes the translation values on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Create translation matrix
    #
    translation = getTranslation(node)
    translateMatrix = createTranslateMatrix(translation)

    resetTranslation(node)

    # Check if offset requires compounding
    #
    offsetParentMatrix = getOffsetParentMatrix(node)

    if not offsetParentMatrix.isEquivalent(om.MMatrix.kIdentity):

        translateMatrix *= offsetParentMatrix

    # Commit offset parent matrix to plug
    #
    setOffsetParentMatrix(node, translateMatrix)


def freezeRotation(node):
    """
    Freezes the rotation values on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Create rotation matrix
    #
    eulerRotation = getEulerRotation(node)
    rotateMatrix = createRotationMatrix(eulerRotation)

    resetEulerRotation(node)

    # Check if offset requires compounding
    #
    offsetParentMatrix = getOffsetParentMatrix(node)

    if not offsetParentMatrix.isEquivalent(om.MMatrix.kIdentity):

        rotateMatrix *= offsetParentMatrix

    # Commit offset parent matrix to plug
    #
    setOffsetParentMatrix(node, rotateMatrix)


def freezeScale(node):
    """
    Freezes the scale values on the supplied node.
    Unlike translation and rotation, scale cannot be unfrozen.
    Technically we could push the scale into the offsetParentMatrix but scale loves to break shit!

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Iterate through all descendants
    #
    scale = getScale(node)
    scaleMatrix = createScaleMatrix(scale)

    for child in dagutils.iterDescendants(node):

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

            localPosition = om.MVector(plugmutators.getValue(plug))
            localPosition *= scaleMatrix

            plugmutators.setValue(plug, localPosition)

            # Scale local scale
            #
            plug = fnDagNode.findPlug('localScale', True)

            localScale = om.MVector(plugmutators.getValue(plug))
            localScale *= scaleMatrix

            plugmutators.setValue(plug, localScale)

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
    resetScale(node)


def matrixToList(matrix):
    """
    Converts the supplied matrix to a list of 16 float values.

    :type matrix: om.MMatrix
    :rtype: Tuple[float, float, float, float, float, float, float, float, float, float, float, float]
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
    Converts the supplied list into a matrix.

    :type matrixList: Tuple[float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]
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


def getMatrix(node, asTransformationMatrix=False):
    """
    Returns the transform matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type asTransformationMatrix: bool
    :rtype: om.MMatrix
    """

    # Get matrix plug
    #
    dagPath = dagutils.getMDagPath(node)
    fnDagNode = om.MFnDagNode(dagPath)

    plug = fnDagNode.findPlug('matrix', True)
    matrixData = plug.asMObject()

    # Convert matrix data
    #
    if asTransformationMatrix:

        return getTransformData(matrixData)

    else:

        return getMatrixData(matrixData)


def getParentMatrix(node, asTransformationMatrix=False):
    """
    Returns the parent matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type asTransformationMatrix: bool
    :rtype: om.MMatrix
    """

    # Get matrix plug
    #
    dagPath = dagutils.getMDagPath(node)
    fnDagNode = om.MFnDagNode(dagPath)

    plug = fnDagNode.findPlug('parentMatrix', True)
    element = plug.elementByLogicalIndex(dagPath.instanceNumber())

    matrixData = element.asMObject()

    # Convert matrix data
    #
    if asTransformationMatrix:

        return getTransformData(matrixData)

    else:

        return getMatrixData(matrixData)


def getOffsetParentMatrix(node, asTransformationMatrix=False):
    """
    Returns the offset parent matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type asTransformationMatrix: bool
    :rtype: om.MMatrix
    """

    # Get offset parent matrix plug
    #
    dagPath = dagutils.getMDagPath(node)
    fnTransform = om.MFnTransform(dagPath)

    plug = fnTransform.findPlug('offsetParentMatrix', True)
    offsetParentMatrixData = plug.asMObject()

    # Convert matrix data
    #
    if asTransformationMatrix:

        return getTransformData(offsetParentMatrixData)

    else:

        return getMatrixData(offsetParentMatrixData)


def setOffsetParentMatrix(node, offsetParentMatrix):
    """
    Updates the offset parent matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type offsetParentMatrix: om.MMatrix
    :rtype: None
    """

    # Get offset parent matrix plug
    #
    dagPath = dagutils.getMDagPath(node)
    fnTransform = om.MFnTransform(dagPath)

    plug = fnTransform.findPlug('offsetParentMatrix', True)
    offsetParentMatrixData = createMatrixData(offsetParentMatrix)

    # Assign matrix data to plug
    #
    plug.setMObject(offsetParentMatrixData)


def getWorldMatrix(node, asTransformationMatrix=False):
    """
    Returns the world matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type asTransformationMatrix: bool
    :rtype: om.MMatrix
    """

    # Get matrix plug
    #
    dagPath = dagutils.getMDagPath(node)
    fnDagNode = om.MFnDagNode(dagPath)

    plug = fnDagNode.findPlug('worldMatrix', True)
    element = plug.elementByLogicalIndex(dagPath.instanceNumber())

    matrixData = element.asMObject()

    # Convert matrix data
    #
    if asTransformationMatrix:

        return getTransformData(matrixData)

    else:

        return getMatrixData(matrixData)


def getMatrixData(matrixData):
    """
    Converts the supplied MObject to an MMatrix.

    :type matrixData: om.MObject
    :rtype: om.MMatrix
    """

    # Redundancy check
    #
    if isinstance(matrixData, om.MMatrix):

        return matrixData

    # Evaluate matrix data type
    #
    fnMatrixData = om.MFnMatrixData(matrixData)

    if fnMatrixData.isTransformation():

        return fnMatrixData.transformation().asMatrix()

    else:

        return fnMatrixData.matrix()


def getTransformData(matrixData):
    """
    Converts the supplied MObject to an MTransformationMatrix.

    :type matrixData: om.MObject
    :rtype: om.MTransformationMatrix
    """

    # Redundancy check
    #
    if isinstance(matrixData, om.MTransformationMatrix):

        return matrixData

    # Evaluate matrix data type
    #
    fnMatrixData = om.MFnMatrixData(matrixData)

    if fnMatrixData.isTransformation():

        return fnMatrixData.transformation()

    else:

        return om.MTransformationMatrix(fnMatrixData.matrix())


def createMatrixData(matrix):
    """
    Converts the given matrix to an MObject.

    :type matrix: Union[om.MMatrix, om.MTransformationMatrix]
    :rtype: om.MObject
    """

    # Redundancy check
    #
    if isinstance(matrix, om.MObject):

        return matrix

    # Create matrix data object
    #
    fnMatrixData = om.MFnMatrixData()
    matrixData = fnMatrixData.create()

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
    Creates a translation matrix based on the supplied value.

    :type value: Union[str, list, tuple, om.MVector, om.MPoint, om.MMatrix]
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

    else:

        raise TypeError('createTranslateMatrix() expects an MVector (%s given)!' % type(value).__name__)


def createRotationMatrix(value):
    """
    Creates a rotation matrix based on the supplied value.
    Degrees should not be used for any of these methods!

    :type value: Union[list, tuple, om.MEulerRotation, om.MQuaternion, om.MMatrix]
    :rtype: om.MMatrix
    """

    # Evaluate value type
    #
    if isinstance(value, om.MEulerRotation):

        return value.asMatrix()

    elif isinstance(value, om.MQuaternion):

        return value.asMatrix()

    elif isinstance(value, (list, tuple)):

        radians = [math.radians(x) for x in value]
        eulerRotation = om.MEulerRotation(radians, order=EULER_ROTATE_ORDER[0])

        return eulerRotation.asMatrix()

    elif isinstance(value, om.MMatrix):

        return om.MMatrix(
            [
                (value.getElement(0, 0), value.getElement(0, 1), value.getElement(0, 2), 0.0),
                (value.getElement(1, 0), value.getElement(1, 1), value.getElement(1, 2), 0.0),
                (value.getElement(2, 0), value.getElement(2, 1), value.getElement(2, 2), 0.0),
                (0.0, 0.0, 0.0, 1.0)
            ]
        )

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
    Returns a rotation matrix to the specified axis vector.

    :type axis: om.MVector
    :rtype: om.MMatrix
    """

    return om.MVector.kXaxisVector.rotateTo(axis).asMatrix()


def createTwistMatrix(twist, axis=om.MVector.kXaxis):
    """
    Returns a twist matrix around the specified axis.
    The twist is expected to be in degrees!

    :type twist: float
    :type axis: int
    :rtype: om.MMatrix
    """

    # Evaluate twist axis
    #
    if axis == om.MVector.kXaxis:

        return createRotationMatrix([twist, 0.0, 0.0])

    elif axis == om.MVector.kYaxis:

        return createRotationMatrix([0.0, twist, 0.0])

    elif axis == om.MVector.kZaxis:

        return createRotationMatrix([0.0, 0.0, twist])

    else:

        raise TypeError('createTwistMatrix() expects a valid axis (%s given)!' % axis)


def createScaleMatrix(value):
    """
    Returns a scale matrix based on the supplied value.

    :type value: Union[str, list, tuple, om.MVector, om.MMatrix]
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

        x, y, z, p = breakMatrix(value)
        return createScaleMatrix([x.length(), y.length(), z.length()])

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

    :type matrix: Union[list, tuple, om.MMatrix, om.MObject]
    :type rotateOrder: int
    :rtype: Tuple[om.MVector, om.MEulerRotation, Tuple[float, float, float]]
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


def composeMatrix(xAxis, yAxis, zAxis, position):
    """
    Returns a transform matrix using the supplied axis vectors and position.

    :type xAxis: om.MVector
    :type yAxis: om.MVector
    :type zAxis: om.MVector
    :type position: Union[om.MVector, om.MPoint]
    :rtype: om.MMatrix
    """

    return om.MMatrix(
        [
            (xAxis.x, xAxis.y, xAxis.z, 0.0),
            (yAxis.x, yAxis.y, yAxis.z, 0.0),
            (zAxis.x, zAxis.y, zAxis.z, 0.0),
            (position.x, position.y, position.z, 1.0)
        ]
    )


def breakMatrix(matrix, normalize=False):
    """
    Returns the axis vectors and position from the supplied matrix.

    :type matrix: Union[str, list, tuple, om.MObject, om.MMatrix]
    :type normalize: bool
    :rtype: om.MVector, om.MVector, om.MVector, om.MPoint
    """

    # Check value type
    #
    if isinstance(matrix, om.MMatrix):

        # Extract rows
        #
        x = om.MVector([matrix.getElement(0, 0), matrix.getElement(0, 1), matrix.getElement(0, 2)])
        y = om.MVector([matrix.getElement(1, 0), matrix.getElement(1, 1), matrix.getElement(1, 2)])
        z = om.MVector([matrix.getElement(2, 0), matrix.getElement(2, 1), matrix.getElement(2, 2)])
        p = om.MPoint([matrix.getElement(3, 0), matrix.getElement(3, 1), matrix.getElement(3, 2), matrix.getElement(3, 3)])

        # Check if vectors should be normalized
        #
        if normalize:

            return x.normal(), y.normal(), z.normal(), p

        else:

            return x, y, z, p

    if isinstance(matrix, string_types):

        return breakMatrix(om.MMatrix(mc.getAttr('%s.matrix' % matrix)))

    elif isinstance(matrix, (list, tuple)):

        return breakMatrix(om.MMatrix(matrix))

    elif isinstance(matrix, om.MObject):

        return breakMatrix(om.MFnMatrixData(matrix).matrix())

    else:

        raise ValueError('getAxisVectors() expects an MMatrix (%s given)!' % type(matrix).__name__)


def lerpMatrix(matrix, otherMatrix, weight=0.5):
    """
    Lerps the two transform matrices by the specified amount.

    :type matrix: om.MMatrix
    :type otherMatrix: om.MMatrix
    :type weight: float
    :rtype: om.MMatrix
    """

    # Linearly interpolate position and scale components
    #
    position, eulerRotation, scale = decomposeTransformMatrix(matrix)
    otherPosition, otherEulerRotation, otherScale = decomposeTransformMatrix(otherMatrix)

    lerpPos = (position * weight) + (otherPosition * (1.0 - weight))
    lerpScale = (om.MVector(scale) * weight) + (om.MVector(otherScale) * (1.0 - weight))

    # Spherically interpolate rotation component
    #
    quat = om.MQuaternion().setValue(matrix)
    otherQuat = om.MQuaternion().setValue(otherMatrix)

    slerpQuat = om.MQuaternion.slerp(quat, otherQuat, weight)

    # Compose interpolated matrix
    #
    positionMatrix = createTranslateMatrix(lerpPos)
    rotateMatrix = slerpQuat.asMatrix()
    scaleMatrix = createScaleMatrix(lerpScale)

    return scaleMatrix * rotateMatrix * positionMatrix


def mirrorVector(vector, normal=om.MVector.kXaxisVector):
    """
    Mirrors the supplied vector across the specified normal.

    :type vector: om.MVector
    :type normal: om.MVector
    :rtype: om.MVector
    """

    return vector - (2.0 * (vector * normal) * normal)


def isArray(value):
    """
    Evaluates if the supplied value is an array.

    :type value: Any
    :rtype: bool
    """

    return hasattr(value, '__getitem__') and hasattr(value, '__len__')


def isClose(value, otherValue, rel_tol=0.0, abs_tol=1e-3):
    """
    Evaluates if the two values are close.

    :type value: Union[int, float, list, om.MVector, om.MPoint, om.MMatrix]
    :type otherValue: Union[int, float, list, om.MVector, om.MPoint, om.MMatrix]
    :type rel_tol: float
    :type abs_tol: float
    :rtype: bool
    """

    # Evaluate value types
    #
    if isinstance(value, (int, float)) and isinstance(otherValue, (int, float)):

        return abs(value - otherValue) <= max(rel_tol * max(abs(value), abs(otherValue)), abs_tol)

    elif isArray(value) and isArray(otherValue):

        return all([isClose(x, y, rel_tol=rel_tol, abs_tol=abs_tol) for (x, y) in zip(value, otherValue)])

    else:

        raise TypeError('isClose() expects either a float or an array!')


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
