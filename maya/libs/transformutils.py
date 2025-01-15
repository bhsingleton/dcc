import math

from maya import cmds as mc
from maya.api import OpenMaya as om
from six import string_types
from dcc.maya.decorators import undo
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

        xPlug = plugutils.findPlug(dagPath, 'translateX')
        yPlug = plugutils.findPlug(dagPath, 'translateY')
        zPlug = plugutils.findPlug(dagPath, 'translateZ')

        return om.MVector(
            plugmutators.getValue(xPlug),
            plugmutators.getValue(yPlug),
            plugmutators.getValue(zPlug),
        )


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

    # Check if translateX can be set
    #
    skipTranslate = kwargs.get('skipTranslate', False)
    skipTranslateX = kwargs.get('skipTranslateX', skipTranslate)

    xPlug = plugutils.findPlug(dagPath, 'translateX')

    if not skipTranslateX and not xPlug.isLocked:

        plugmutators.setValue(xPlug, translation.x)

    # Check if translateY can be set
    #
    skipTranslateY = kwargs.get('skipTranslateY', skipTranslate)
    yPlug = plugutils.findPlug(dagPath, 'translateY')

    if not skipTranslateY and not yPlug.isLocked:

        plugmutators.setValue(yPlug, translation.y)

    # Check if translateZ can be set
    #
    skipTranslateZ = kwargs.get('skipTranslateZ', skipTranslate)
    zPlug = plugutils.findPlug(dagPath, 'translateZ')

    if not skipTranslateZ and not zPlug.isLocked:

        plugmutators.setValue(zPlug, translation.z)


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

    # Update translation
    #
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
    Returns the euler angles on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MEulerRotation
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('getEulerRotation() expects a valid dag path!')

    # Get euler angles from node
    #
    xPlug = plugutils.findPlug(dagPath, 'rotateX')
    yPlug = plugutils.findPlug(dagPath, 'rotateY')
    zPlug = plugutils.findPlug(dagPath, 'rotateZ')
    orderPlug = plugutils.findPlug(dagPath, 'rotateOrder')

    return om.MEulerRotation(
        plugmutators.getValue(xPlug, convertUnits=False).asRadians(),
        plugmutators.getValue(yPlug, convertUnits=False).asRadians(),
        plugmutators.getValue(zPlug, convertUnits=False).asRadians(),
        order=plugmutators.getValue(orderPlug)
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

    # Check if rotateX can be set
    #
    skipRotate = kwargs.get('skipRotate', False)
    skipRotateX = kwargs.get('skipRotateX', skipRotate)

    xPlug = plugutils.findPlug(dagPath, 'rotateX')

    if not skipRotateX and not xPlug.isLocked:

        plugmutators.setValue(xPlug, om.MAngle(eulerRotation.x, om.MAngle.kRadians))

    # Check if rotateY can be set
    #
    skipRotateY = kwargs.get('skipRotateY', skipRotate)
    yPlug = plugutils.findPlug(dagPath, 'rotateY')

    if not skipRotateY and not yPlug.isLocked:

        plugmutators.setValue(yPlug, om.MAngle(eulerRotation.y, om.MAngle.kRadians))

    # Check if rotateZ can be set
    #
    skipRotateZ = kwargs.get('skipRotateZ', skipRotate)
    zPlug = plugutils.findPlug(dagPath, 'rotateZ')

    if not skipRotateZ and not zPlug.isLocked:

        plugmutators.setValue(zPlug, om.MAngle(eulerRotation.z, om.MAngle.kRadians))

    # Check if rotate order can be set
    #
    orderPlug = plugutils.findPlug(dagPath, 'rotateOrder')

    if not any([skipRotateX, skipRotateY, skipRotateZ]) and not orderPlug.isLocked:

        plugmutators.setValue(orderPlug, eulerRotation.order)


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

    currentRotationMatrix = getEulerRotation(node).asMatrix()
    newRotationMatrix = difference * currentRotationMatrix

    newEulerRotation = om.MEulerRotation([0.0, 0.0, 0.0], order=getRotationOrder(node))
    newEulerRotation.setValue(newRotationMatrix)

    # Update euler angles
    #
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

    # Check if dag path contains a joint
    #
    if not dagPath.hasFn(om.MFn.kJoint):

        return om.MEulerRotation()

    # Get orientation from joint
    #
    xPlug = plugutils.findPlug(dagPath, 'jointOrientX')
    yPlug = plugutils.findPlug(dagPath, 'jointOrientY')
    zPlug = plugutils.findPlug(dagPath, 'jointOrientZ')

    return om.MEulerRotation(
        plugmutators.getValue(xPlug, convertUnits=False).asRadians(),
        plugmutators.getValue(yPlug, convertUnits=False).asRadians(),
        plugmutators.getValue(zPlug, convertUnits=False).asRadians()
    )


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

    # Check if rotateX can be set
    #
    skipJointOrient = kwargs.get('skipJointOrient', False)
    skipJointOrientX = kwargs.get('skipJointOrientX', skipJointOrient)

    xPlug = plugutils.findPlug(dagPath, 'jointOrientX')

    if not skipJointOrientX and not xPlug.isLocked:

        plugmutators.setValue(xPlug, om.MAngle(orientation.x, om.MAngle.kRadians))

    # Check if rotateY can be set
    #
    skipJointOrientY = kwargs.get('skipJointOrientY', skipJointOrient)
    zPlug = plugutils.findPlug(dagPath, 'jointOrientY')

    if not skipJointOrientY and not zPlug.isLocked:

        plugmutators.setValue(zPlug, om.MAngle(orientation.y, om.MAngle.kRadians))

    # Check if rotateZ can be set
    #
    skipJointOrientZ = kwargs.get('skipJointOrientZ', skipJointOrient)
    zPlug = plugutils.findPlug(dagPath, 'jointOrientZ')

    if not skipJointOrientZ and not zPlug.isLocked:

        plugmutators.setValue(zPlug, om.MAngle(orientation.z, om.MAngle.kRadians))


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
    :rtype: List[float, float, float]
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('getScale() expects a valid dag path!')

    # Get scale values from node
    #
    xPlug = plugutils.findPlug(dagPath, 'scaleX')
    yPlug = plugutils.findPlug(dagPath, 'scaleY')
    zPlug = plugutils.findPlug(dagPath, 'scaleZ')

    return [
        plugmutators.getValue(xPlug),
        plugmutators.getValue(yPlug),
        plugmutators.getValue(zPlug),
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

    # Check if `scaleX` can be set
    #
    skipScale = kwargs.get('skipScale', False)
    skipScaleX = kwargs.get('skipScaleX', skipScale)

    xPlug = plugutils.findPlug(dagPath, 'scaleX')

    if not skipScaleX and not xPlug.isLocked:

        plugmutators.setValue(xPlug, scale[0])

    # Check if `scaleY` can be set
    #
    skipScaleY = kwargs.get('skipScaleY', skipScale)
    yPlug = plugutils.findPlug(dagPath, 'scaleY')

    if not skipScaleY and not yPlug.isLocked:

        plugmutators.setValue(yPlug, scale[1])

    # Check if `scaleZ` can be set
    #
    skipScaleZ = kwargs.get('skipScaleZ', skipScale)
    zPlug = plugutils.findPlug(dagPath, 'scaleZ')

    if not skipScaleZ and not zPlug.isLocked:

        plugmutators.setValue(zPlug, scale[2])


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
    :type scale: Union[Tuple[float, float, float], om.MVector]
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

    # Update scale
    #
    setScale(node, newScale, **kwargs)


@undo.Undo(name='Freeze Pivots')
def freezePivots(node, includeTranslate=True, includeRotate=True, includeScale=False):
    """
    Pushes the transform's local matrix into the pivot.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type includeTranslate: bool
    :type includeRotate: bool
    :type includeScale: bool
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('freezePivots() expects a valid dag path!')

    # Check if translation should be frozen
    #
    isJoint = dagPath.hasFn(om.MFn.kJoint)
    includeTranslate = includeTranslate and not isJoint

    initialMatrix = getMatrix(dagPath)

    if includeTranslate and not isJoint:

        translation = breakMatrix(initialMatrix)[3]

        rotatePivotPlug = plugutils.findPlug(dagPath, 'rotatePivot')
        plugmutators.setValue(rotatePivotPlug, translation)

        scalePivotPlug = plugutils.findPlug(dagPath, 'scalePivot')
        plugmutators.setValue(scalePivotPlug, translation)

        resetTranslation(dagPath)

    # Check if rotation should be frozen
    #
    if includeRotate and isJoint:

        eulerRotation = getEulerRotation(dagPath)
        jointOrientation = getJointOrient(dagPath)
        quaternion = eulerRotation.asQuaternion() * jointOrientation.asQuaternion()

        frozenRotation = om.MEulerRotation()
        frozenRotation.setValue(quaternion)

        setJointOrient(dagPath, frozenRotation)
        resetEulerRotation(dagPath)

    else:

        resetEulerRotation(dagPath)

    # Check if scale should be frozen
    #
    if includeScale:

        resetScale(dagPath)

    # Check if shapes require updating
    #
    if includeTranslate or includeRotate or includeScale:

        frozenMatrix = getMatrix(dagPath)
        matrix = initialMatrix * frozenMatrix.inverse()

        isDeformed = len(dagutils.dependsOn(dagPath.node(), apiType=om.MFn.kGeometryFilt)) > 0
        iterShapes = dagutils.iterIntermediateObjects(dagPath) if isDeformed else dagutils.iterShapes(dagPath)

        for shape in iterShapes:

            if shape.hasFn(om.MFn.kLocator):

                localPositionPlug = plugutils.findPlug(shape, 'localPosition')
                localPositionMatrix = createTranslateMatrix(plugmutators.getValue(localPositionPlug))

                localScalePlug = plugutils.findPlug(shape, 'localScale')
                localScaleMatrix = createScaleMatrix(plugmutators.getValue(localScalePlug))

                localMatrix = localScaleMatrix * localPositionMatrix * matrix
                translation, eulerRotation, scale = decomposeTransformMatrix(localMatrix)

                plugmutators.setValue(localPositionPlug, translation)
                plugmutators.setValue(localScalePlug, scale)

            elif shape.hasFn(om.MFn.kNurbsCurve):

                fnNurbsCurve = om.MFnNurbsCurve(shape)
                controlPoints = [om.MPoint(point) * matrix for point in fnNurbsCurve.cvPositions()]

                fnNurbsCurve.setCVPositions(controlPoints)
                fnNurbsCurve.updateCurve()

            elif shape.hasFn(om.MFn.kNurbsSurface):

                fnNurbsSurface = om.MFnNurbsSurface(shape)
                controlPoints = [om.MPoint(point) * matrix for point in fnNurbsSurface.cvPositions()]

                fnNurbsSurface.setCVPositions(controlPoints)
                fnNurbsSurface.updateSurface()

            elif shape.hasFn(om.MFn.kMesh):

                fnMesh = om.MFnMesh(shape)
                controlPoints = [om.MPoint(point) * matrix for point in fnMesh.getPoints()]

                fnMesh.setPoints(controlPoints)
                fnMesh.updateSurface()

                hasLockedNormals = fnMesh.isNormalLocked(0)

                if hasLockedNormals:

                    normals = [om.MVector(normal) * matrix for normal in fnMesh.getNormals()]
                    fnMesh.setNormals(normals)
                    fnMesh.updateSurface()

            else:

                log.warning(f'Cannot freeze "{shape.apiTypeStr}" shape!')
                continue

        resetScale(dagPath)


@undo.Undo(name='Un-Freeze Pivots')
def unfreezePivots(node):
    """
    Pushes the transform's parent offset matrix back into its matrix.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('freezePivots() expects a valid dag path!')

    # Reset pivots
    #
    initialMatrix = getMatrix(dagPath)

    rotatePivotPlug = plugutils.findPlug(dagPath, 'rotatePivot')
    rotatePivot = om.MVector(plugmutators.getValue(rotatePivotPlug))
    rotatePivotTranslatePlug = plugutils.findPlug(dagPath, 'rotatePivotTranslate')
    rotatePivotTranslate = om.MVector(plugmutators.getValue(rotatePivotTranslatePlug))
    translation = getTranslation(dagPath) + rotatePivot + rotatePivotTranslate

    setTranslation(dagPath, translation)
    resetPivots(dagPath)

    # Reset joint orientation
    #
    isJoint = dagPath.hasFn(om.MFn.kJoint)

    if isJoint:

        eulerRotation = getEulerRotation(dagPath)
        jointOrientation = getJointOrient(dagPath)
        quaternion = eulerRotation.asQuaternion() * jointOrientation.asQuaternion()

        order = getRotationOrder(dagPath)
        unfrozenRotation = om.MEulerRotation(0.0, 0.0, 0.0, order=order)
        unfrozenRotation.setValue(quaternion)

        setEulerRotation(dagPath, unfrozenRotation)
        resetJointOrient(dagPath)

    # Check if shapes require updating
    #
    unfrozenMatrix = getMatrix(dagPath)

    if not initialMatrix.isEquivalent(unfrozenMatrix):

        # Iterate through shapes
        #
        matrix = initialMatrix * unfrozenMatrix.inverse()

        isDeformed = len(dagutils.dependsOn(dagPath.node(), apiType=om.MFn.kGeometryFilt)) > 0
        iterShapes = dagutils.iterIntermediateObjects(dagPath) if isDeformed else dagutils.iterShapes(dagPath)

        for shape in iterShapes:

            if shape.hasFn(om.MFn.kLocator):

                localPositionPlug = plugutils.findPlug(shape, 'localPosition')
                localPositionMatrix = createTranslateMatrix(plugmutators.getValue(localPositionPlug))

                localScalePlug = plugutils.findPlug(shape, 'localScale')
                localScaleMatrix = createScaleMatrix(plugmutators.getValue(localScalePlug))

                localMatrix = localScaleMatrix * localPositionMatrix * matrix
                translation, eulerRotation, scale = decomposeTransformMatrix(localMatrix)

                plugmutators.setValue(localPositionPlug, translation)
                plugmutators.setValue(localScalePlug, scale)

            elif shape.hasFn(om.MFn.kNurbsCurve):

                fnNurbsCurve = om.MFnNurbsCurve(shape)
                controlPoints = [om.MPoint(point) * matrix for point in fnNurbsCurve.cvPositions()]

                fnNurbsCurve.setCVPositions(controlPoints)
                fnNurbsCurve.updateCurve()

            elif shape.hasFn(om.MFn.kNurbsSurface):

                fnNurbsSurface = om.MFnNurbsSurface(shape)
                controlPoints = [om.MPoint(point) * matrix for point in fnNurbsSurface.cvPositions()]

                fnNurbsSurface.setCVPositions(controlPoints)
                fnNurbsSurface.updateSurface()

            elif shape.hasFn(om.MFn.kMesh):

                fnMesh = om.MFnMesh(shape)
                controlPoints = [om.MPoint(point) * matrix for point in fnMesh.getPoints()]

                fnMesh.setPoints(controlPoints)
                fnMesh.updateSurface()

            else:

                log.warning(f'Cannot freeze "{shape.apiTypeStr}" shape!')
                continue


def resetPivots(node):
    """
    Resets all the pivot components for the given dag path.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    node = dagutils.getMDagPath(node)

    for attribute in ('rotatePivot', 'rotatePivotTranslate', 'scalePivot', 'scalePivotTranslate'):

        plug = plugutils.findPlug(node, attribute)
        plugmutators.resetValue(plug)


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

    if not dagPath.isValid() or not isinstance(matrix, (om.MMatrix, om.MTransformationMatrix)):

        raise TypeError('applyTransformMatrix() expects an MDagPath and MMatrix!')

    # Decompose transform matrix
    #
    partialPathName = dagPath.partialPathName()

    log.debug(f'{partialPathName}.matrix = {matrix}')
    translation, eulerRotation, scale = decomposeTransformMatrix(matrix, rotateOrder=getRotationOrder(dagPath))

    # Check if translation should be skipped
    #
    skipTranslate = kwargs.get('skipTranslate', False)

    if not skipTranslate:

        log.debug(f'{partialPathName}.translate = [{translation.x}, {translation.y}, {translation.z}]')
        translateTo(node, translation, **kwargs)

    # Check if rotation should be skipped
    #
    skipRotate = kwargs.get('skipRotate', False)

    if not skipRotate:

        log.debug(f'{partialPathName}.rotate = [{eulerRotation.x}, {eulerRotation.y}, {eulerRotation.z}]')
        rotateTo(node, eulerRotation, **kwargs)

    # Check if scale should be skipped
    #
    skipScale = kwargs.get('skipScale', False)

    if not skipScale:

        log.debug(f'{partialPathName}.scale = [{scale[0]}, {scale[1]}, {scale[2]}]')
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


@undo.Undo(name='Freeze Transform')
def freezeTransform(node, **kwargs):
    """
    Pushes the transform's matrix into the parent offset matrix.

    :type node: Union[str, om.MObject, om.MDagPath]
    :key includeTranslate: bool
    :key includeRotate: bool
    :key includeScale: bool
    :rtype: None
    """

    # Check if translation should be frozen
    #
    includeTranslate = kwargs.get('includeTranslate', True)

    if includeTranslate:

        freezeTranslation(node)

    # Check if rotation should be frozen
    #
    includeRotate = kwargs.get('includeRotate', True)

    if includeRotate:

        freezeRotation(node)

    # Check if scale should be frozen
    #
    includeScale = kwargs.get('includeScale', False)


    if includeScale:

        bakeScale = kwargs.get('bakeScale', True)
        freezeScale(node, bake=bakeScale)


@undo.Undo(name='Un-Freeze Transform')
def unfreezeTransform(node):
    """
    Pushes the transform's parent offset matrix back into its matrix.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Inspect dag path
    #
    dagPath = dagutils.getMDagPath(node)

    if not dagPath.isValid():

        raise TypeError('unfreezeTransform() expects a valid dag path!')

    # Redundancy check
    #
    offsetParentMatrix = getOffsetParentMatrix(dagPath)

    if offsetParentMatrix.isEquivalent(om.MMatrix.kIdentity, tolerance=1e-3):

        log.debug('Transform has already been unfrozen: %s' % dagPath.partialPathName())
        return

    # Cache world matrix and reset offset parent-matrix
    #
    worldMatrix = getWorldMatrix(dagPath)
    resetOffsetParentMatrix(dagPath)

    # Update transform matrix
    #
    applyWorldMatrix(dagPath, worldMatrix, skipScale=True)


def freezeTranslation(node):
    """
    Freezes the translation values on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Get and reset current translation
    #
    dagLocalMatrixPlug = plugutils.findPlug(node, 'dagLocalMatrix')
    dagLocalMatrixData = dagLocalMatrixPlug.asMObject()
    dagLocalMatrix = getMatrixData(dagLocalMatrixData, asTransformationMatrix=True)

    currentTranslation = dagLocalMatrix.translation(om.MSpace.kTransform)
    resetTranslation(node)

    # Calculate new offset parent-matrix
    #
    offsetParentMatrix = getOffsetParentMatrix(node)
    translation, eulerRotation, scale = decomposeTransformMatrix(offsetParentMatrix)

    offsetParentMatrix = composeMatrix(currentTranslation, eulerRotation, scale)

    # Push offset parent-matrix to plug
    #
    setOffsetParentMatrix(node, offsetParentMatrix)


def freezeRotation(node):
    """
    Freezes the rotation values on the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    # Get and reset current rotation
    #
    dagLocalMatrixPlug = plugutils.findPlug(node, 'dagLocalMatrix')
    dagLocalMatrixData = dagLocalMatrixPlug.asMObject()
    dagLocalMatrix = getMatrixData(dagLocalMatrixData, asTransformationMatrix=True)

    currentQuat = dagLocalMatrix.rotation(asQuaternion=True)
    resetEulerRotation(node)

    # Add rotation onto offset parent-matrix
    #
    offsetParentMatrix = getOffsetParentMatrix(node)
    translation, eulerRotation, scale = decomposeTransformMatrix(offsetParentMatrix)

    offsetParentMatrix = composeMatrix(translation, currentQuat, scale)

    # Push offset parent-matrix to plug
    #
    setOffsetParentMatrix(node, offsetParentMatrix)


def freezeScale(node, bake=True):
    """
    Freezes the scale values on the supplied node.
    Unlike translation and rotation, scale cannot be unfrozen.
    Technically we could push the scale into the offsetParentMatrix but scale loves to break shit!

    :type node: Union[str, om.MObject, om.MDagPath]
    :type bake: bool
    :rtype: None
    """

    # Check if scale should be baked
    #
    if bake:

        # Iterate through descendants
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

                log.warning(f'Unable to bake scale into: {child.apiTypeStr} api type!')
                continue

        # Reset scale on transform
        #
        resetScale(node)

    else:

        # Get and reset current translation
        #
        dagLocalMatrixPlug = plugutils.findPlug(node, 'dagLocalMatrix')
        dagLocalMatrixData = dagLocalMatrixPlug.asMObject()
        dagLocalMatrix = getMatrixData(dagLocalMatrixData, asTransformationMatrix=True)

        currentScale = dagLocalMatrix.scale(om.MSpace.kTransform)
        resetScale(node)

        # Calculate new offset parent-matrix
        #
        offsetParentMatrix = getOffsetParentMatrix(node)
        translation, eulerRotation, scale = decomposeTransformMatrix(offsetParentMatrix)

        offsetParentMatrix = composeMatrix(translation, eulerRotation, currentScale)

        # Push offset parent-matrix to plug
        #
        setOffsetParentMatrix(node, offsetParentMatrix)


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

    plug = plugutils.findPlug(node, 'matrix')
    matrixData = plug.asMObject()

    return getMatrixData(matrixData, asTransformationMatrix=asTransformationMatrix)


def getParentMatrix(node, asTransformationMatrix=False):
    """
    Returns the parent matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type asTransformationMatrix: bool
    :rtype: om.MMatrix
    """

    dagPath = dagutils.getMDagPath(node)
    instanceNumber = dagPath.instanceNumber()
    plug = plugutils.findPlug(dagPath, f'parentMatrix[{instanceNumber}]')
    matrixData = plug.asMObject()

    return getMatrixData(matrixData, asTransformationMatrix=asTransformationMatrix)


def getOffsetParentMatrix(node, asTransformationMatrix=False):
    """
    Returns the offset parent matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type asTransformationMatrix: bool
    :rtype: om.MMatrix
    """

    plug = plugutils.findPlug(node, 'offsetParentMatrix')
    offsetParentMatrixData = plug.asMObject()

    return getMatrixData(offsetParentMatrixData, asTransformationMatrix=asTransformationMatrix)


def setOffsetParentMatrix(node, offsetParentMatrix):
    """
    Updates the offset parent matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type offsetParentMatrix: om.MMatrix
    :rtype: None
    """

    plug = plugutils.findPlug(node, 'offsetParentMatrix')
    plugmutators.setValue(plug, offsetParentMatrix)


def resetOffsetParentMatrix(node):
    """
    Resets the offset parent matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: None
    """

    setOffsetParentMatrix(node, om.MMatrix.kIdentity)


def getWorldMatrix(node, asTransformationMatrix=False):
    """
    Returns the world matrix for the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type asTransformationMatrix: bool
    :rtype: om.MMatrix
    """

    dagPath = dagutils.getMDagPath(node)
    instanceNumber = dagPath.instanceNumber()
    plug = plugutils.findPlug(dagPath, f'worldMatrix[{instanceNumber}]')
    matrixData = plug.asMObject()

    return getMatrixData(matrixData, asTransformationMatrix=asTransformationMatrix)


def getMatrixData(matrixData, asTransformationMatrix=False):
    """
    Converts the supplied MObject to an MMatrix.

    :type matrixData: om.MObject
    :type asTransformationMatrix: bool
    :rtype: om.MMatrix
    """

    # Redundancy check
    #
    if isinstance(matrixData, (om.MMatrix, om.MTransformationMatrix)):

        return matrixData

    # Evaluate matrix data type
    #
    fnMatrixData = om.MFnMatrixData(matrixData)

    if fnMatrixData.isTransformation():

        transformationMatrix = fnMatrixData.transformation()

        if asTransformationMatrix:

            return transformationMatrix

        else:

            return transformationMatrix.asMatrix()

    else:

        matrix = fnMatrixData.matrix()

        if asTransformationMatrix:

            return om.MTransformationMatrix(matrix)

        else:

            return matrix


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
    Creates a rotation matrix from the supplied value.
    Any lists will be treated as a degrees and converted to radians!

    :type value: Union[list, tuple, om.MEulerRotation, om.MQuaternion, om.MMatrix]
    :rtype: om.MMatrix
    """

    # Evaluate value type
    #
    if isinstance(value, om.MEulerRotation):

        return value.asMatrix()

    elif isinstance(value, om.MQuaternion):

        return value.asMatrix()

    elif isinstance(value, (list, tuple, om.MVector)):

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
    if isinstance(value, (list, tuple, om.MVector)):

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


def makeMatrix(xAxis, yAxis, zAxis, position):
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


def decomposeTransformNode(node, space=om.MSpace.kTransform):
    """
    Breaks apart the supplied node's matrix into translate, rotate and scale components.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type space: int
    :rtype: Tuple[om.MVector, om.MEulerRotation, list[float, float, float]]
    """

    dagPath = dagutils.getMDagPath(node)
    rotateOrder = getRotationOrder(dagPath)

    if space == om.MSpace.kWorld:

        worldMatrix = dagPath.inclusiveMatrix()
        return decomposeTransformMatrix(worldMatrix, rotateOrder=rotateOrder)

    else:

        matrix = getMatrix(dagPath, asTransformationMatrix=True)
        return decomposeTransformMatrix(matrix)


def decomposeTransformMatrix(matrix, rotateOrder=om.MEulerRotation.kXYZ):
    """
    Breaks apart the supplied matrix into translate, rotate and scale components.
    An optional rotation order can be supplied to convert euler rotations.

    :type matrix: Union[list, tuple, om.MObject, om.MMatrix, om.MTransformationMatrix]
    :type rotateOrder: int
    :rtype: Tuple[om.MVector, om.MEulerRotation, Tuple[float, float, float]]
    """

    # Evaluate matrix type
    #
    if isinstance(matrix, om.MTransformationMatrix):

        # Extract translate, rotate and scale components
        #
        translation = matrix.translation(om.MSpace.kTransform)
        rotation = matrix.rotation(asQuaternion=False)
        scale = matrix.scale(om.MSpace.kTransform)

        return translation, rotation, scale

    elif isinstance(matrix, om.MMatrix):

        return decomposeTransformMatrix(om.MTransformationMatrix(matrix), rotateOrder=rotateOrder)

    elif isinstance(matrix, (list, tuple)):

        return decomposeTransformMatrix(listToMatrix(matrix), rotateOrder=rotateOrder)

    elif isinstance(matrix, om.MObject):

        return decomposeTransformMatrix(getMatrixData(matrix), rotateOrder=rotateOrder)

    else:

        raise TypeError('decomposeMatrix() expects an MMatrix (%s given)!' % type(matrix).__name__)


def composeMatrix(translation, eulerRotation, scale):
    """
    Returns a transform matrix using the supplied axis vectors and position.

    :type translation: om.MVector
    :type eulerRotation: om.MEulerRotation
    :type scale: om.MVector
    :rtype: om.MMatrix
    """

    translateMatrix = createTranslateMatrix(translation)
    rotateMatrix = createRotationMatrix(eulerRotation)
    scaleMatrix = createScaleMatrix(scale)

    return scaleMatrix * rotateMatrix * translateMatrix


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


def reorientMatrix(forwardAxis, upAxis, matrix, forwardAxisSign=1, upAxisSign=1):
    """
    Reorients the supplied matrix to the specified forward and up axes.

    :type forwardAxis: int
    :type upAxis: int
    :type matrix: om.MMatrix
    :type forwardAxisSign: int
    :type upAxisSign: int
    :rtype: om.MMatrix
    """

    forwardVector = om.MVector.kXaxisVector * forwardAxisSign
    upVector = om.MVector.kYaxisVector * upAxisSign
    rotationMatrix = createAimMatrix(forwardAxis, forwardVector, upAxis, upVector)

    return rotationMatrix * matrix


def mirrorVector(vector, normal=om.MVector.kXaxisVector):
    """
    Mirrors the supplied vector across the specified normal.

    :type vector: om.MVector
    :type normal: om.MVector
    :rtype: om.MVector
    """

    return vector - (2.0 * (vector * normal) * normal)


def projectVector(vector, normal):
    """
    Projects the supplied vector onto the specified normal.

    :type vector: om.MVector
    :type normal: om.MVector
    :rtype: om.MVector
    """

    return vector - (normal * (vector * normal))


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
