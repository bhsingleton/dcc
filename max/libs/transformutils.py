import pymxs

from . import controllerutils, wrapperutils
from ...naming import namingutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__quat_to_matrix3__ = pymxs.runtime.execute('fn quatToMatrix3 quaternion = ( quaternion as Matrix3 );')
__euler_to_matrix3__ = pymxs.runtime.execute('fn eulerAnglesToMatrix3 angles = ( angles as Matrix3 );')


def getTranslation(node):
    """
    Returns the translation values from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.runtime.Point3
    """

    # Inspect transform controller
    #
    transformController = controllerutils.getPRSController(node)

    if not wrapperutils.isKindOf(transformController, pymxs.runtime.PRS):

        return getMatrix(node).translationPart

    # Get position controller
    #
    positionController = pymxs.runtime.getPropertyController(node, pymxs.runtime.Name('Position'))

    if controllerutils.isXYZController(positionController) or controllerutils.isBezierController(positionController):

        return pymxs.runtime.copy(positionController.value)

    elif wrapperutils.isKindOf(positionController, pymxs.runtime.Position_List):

        active = positionController.getActive() - 1
        subController = positionController[active].controller

        return pymxs.runtime.copy(subController.value)

    else:

        return getMatrix(node).translationPart


def setTranslation(node, translation, **kwargs):
    """
    Updates the translation values for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :type translation: pymxs.runtime.Point3
    :key skipTranslate: bool
    :key skipTranslateX: bool
    :key skipTranslateY: bool
    :key skipTranslateZ: bool
    :rtype: None
    """

    # Get transform controller
    #
    transformController = controllerutils.getPRSController(node)

    if pymxs.runtime.classOf(transformController) != pymxs.runtime.PRS:

        log.warning('setTranslation() expects a PRS controller (%s given)!' % pymxs.runtime.classOf(transformController))
        return

    # Check if this is a position list
    #
    positionController = pymxs.runtime.getPropertyController(transformController, 'Position')

    if controllerutils.isListController(positionController):

        currentIndex = positionController.getActive() - 1
        positionController = positionController[currentIndex].controller

    # Check controller type
    #
    skipTranslate = kwargs.get('skipTranslate', False)
    skipTranslateX = kwargs.get('skipTranslateX', skipTranslate)
    skipTranslateY = kwargs.get('skipTranslateY', skipTranslate)
    skipTranslateZ = kwargs.get('skipTranslateZ', skipTranslate)

    if controllerutils.isXYZController(positionController):

        # Check if x-axis should be skipped
        #
        if not skipTranslateX:

            positionController['X_Position'].controller.value = translation.x

        # Check if y-axis should be skipped
        #
        if not skipTranslateY:

            positionController['Y_Position'].controller.value = translation.y

        # Check if z-axis should be skipped
        #
        if not skipTranslateZ:

            positionController['Z_Position'].controller.value = translation.z

    elif controllerutils.isBezierController(positionController):

        # Check which axes should be skipped
        #
        currentTranslation = pymxs.runtime.copy(positionController.value)
        filteredTranslation = [currentTranslation[i] if skip else translation[i] for (i, skip) in enumerate([skipTranslateX, skipTranslateY, skipTranslateZ])]

        positionController.value = pymxs.runtime.Point3(*filteredTranslation)

    else:

        log.warning('setTranslation() expects a XYZ controller (%s given)!' % pymxs.runtime.classOf(positionController))


def resetTranslation(node, **kwargs):
    """
    Resets the translation values for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: None
    """

    setTranslation(node, pymxs.runtime.Point3(0.0, 0.0, 0.0))


def translateTo(node, position, **kwargs):
    """
    Translates this node to the specified position.
    Unlike `setTranslation`, this method adds the translational difference to the current transform matrix.

    :type node: pymxs.MXSWrapperBase
    :type position: pymxs.runtime.Point3
    :rtype: None
    """

    currentPosition = getMatrix(node).translationPart
    difference = position - currentPosition
    translation = getTranslation(node) + difference

    setTranslation(node, translation, **kwargs)


def getRotationOrder(node):
    """
    Returns the rotation order for the supplied node.
    Please be aware that not all controllers have an axis order property!

    :type node: pymxs.MXSWrapperBase
    :rtype: int
    """

    # Get transform controller
    #
    transformController = pymxs.runtime.getTMController(node)

    if pymxs.runtime.classOf(transformController) != pymxs.runtime.PRS:

        return 1

    # Check if this is a rotation list
    #
    rotationController = pymxs.runtime.getPropertyController(transformController, 'Rotation')

    if controllerutils.isListController(rotationController):

        currentIndex = rotationController.getActive() - 1
        rotationController = rotationController[currentIndex].controller

    # Get axis order property
    #
    if pymxs.runtime.isProperty(rotationController, 'axisOrder'):

        return rotationController.axisOrder

    else:

        return 1


def getEulerRotation(node):
    """
    Returns the euler angles from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.runtime.EulerAngles
    """

    # Inspect transform controller
    #
    transformController = controllerutils.getPRSController(node)
    rotationOrder = getRotationOrder(node)

    if not wrapperutils.isKindOf(transformController, pymxs.runtime.PRS):

        return pymxs.runtime.quatToEuler(getMatrix(node).rotationPart, order=rotationOrder)

    # Get position controller
    #
    rotationController = pymxs.runtime.getPropertyController(node, pymxs.runtime.Name('Rotation'))

    if controllerutils.isXYZController(rotationController):

        return pymxs.runtime.EulerAngles(*[subAnim.value for subAnim in controllerutils.iterSubAnims(rotationController)])

    elif controllerutils.isBezierController(rotationController):

        return pymxs.runtime.quatToEuler(rotationController.value, order=rotationOrder)

    elif wrapperutils.isKindOf(rotationController, pymxs.runtime.Rotation_List):

        active = rotationController.getActive() - 1
        subController = rotationController[active].controller

        return pymxs.runtime.quatToEuler(subController.value, order=rotationOrder)

    else:

        return pymxs.runtime.quatToEuler(getMatrix(node).rotationPart, order=getRotationOrder(node))


def setEulerRotation(node, eulerAngles, **kwargs):
    """
    Updates the euler angles for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :type eulerAngles: pymxs.runtime.EulerAngles
    :key skipRotate: bool
    :key skipRotateX: bool
    :key skipRotateY: bool
    :key skipRotateZ: bool
    :rtype: None
    """

    # Get transform controller
    #
    transformController = controllerutils.getPRSController(node)

    if pymxs.runtime.classOf(transformController) != pymxs.runtime.PRS:

        log.warning('setEulerRotation() expects a PRS controller (%s given)!' % pymxs.runtime.classOf(transformController))
        return

    # Check if this is a rotation list
    #
    rotationController = pymxs.runtime.getPropertyController(transformController, 'Rotation')

    if controllerutils.isListController(rotationController):

        currentIndex = rotationController.getActive() - 1
        rotationController = rotationController[currentIndex].controller

    # Check controller type
    #
    skipRotate = kwargs.get('skipRotate', False)
    skipRotateX = kwargs.get('skipRotateX', skipRotate)
    skipRotateY = kwargs.get('skipRotateY', skipRotate)
    skipRotateZ = kwargs.get('skipRotateZ', skipRotate)

    if controllerutils.isXYZController(rotationController):

        # Check if x-axis should be skipped
        #
        if not skipRotateX:

            rotationController['X_Rotation'].controller.value = eulerAngles.x

        # Check if y-axis should be skipped
        #
        if not skipRotateY:

            rotationController['Y_Rotation'].controller.value = eulerAngles.y

        # Check if z-axis should be skipped
        #
        if not skipRotateZ:

            rotationController['Z_Rotation'].controller.value = eulerAngles.z

    elif controllerutils.isBezierController(rotationController):

        # Check which axes should be skipped
        #
        currentAngles = pymxs.runtime.quatToEuler(rotationController.value)
        filteredAngles = [currentAngles[i] if skip else eulerAngles[i] for (i, skip) in enumerate([skipRotateX, skipRotateY, skipRotateZ])]

        rotationController.value = pymxs.runtime.EulerAngles(*filteredAngles)

    else:

        log.warning('setRotation() expects a XYZ controller (%s given)!' % pymxs.runtime.classOf(rotationController))


def resetEulerRotation(node, **kwargs):
    """
    Updates the euler angles for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: None
    """

    setEulerRotation(node, pymxs.runtime.EulerAngles(0.0, 0.0, 0.0))


def rotateTo(node, eulerAngles, **kwargs):
    """
    Rotates this node to the specified orientation.
    Unlike `setEulerRotation`, this method adds the rotational difference to the current transform matrix.

    :type node: pymxs.MXSWrapperBase
    :type eulerAngles: pymxs.runtime.EulerAngles
    :rtype: None
    """

    rotationMatrix = eulerAnglesToMatrix3(eulerAngles)
    currentMatrix = getMatrix(node)
    difference = rotationMatrix * pymxs.runtime.inverse(currentMatrix)

    currentEulerAngles = getEulerRotation(node)
    newRotationMatrix = difference * eulerAnglesToMatrix3(currentEulerAngles)
    newEulerRotation = pymxs.runtime.quatToEuler(newRotationMatrix.rotationPart, order=getRotationOrder(node))

    setEulerRotation(node, newEulerRotation, **kwargs)


def getScale(node):
    """
    Returns the scale value from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: list[float, float, float]
    """

    # Inspect transform controller
    #
    transformController = controllerutils.getPRSController(node)

    if not wrapperutils.isKindOf(transformController, pymxs.runtime.PRS):

        return getMatrix(node).scalePart

    # Get position controller
    #
    scaleController = pymxs.runtime.getPropertyController(node, pymxs.runtime.Name('Scale'))

    if controllerutils.isXYZController(scaleController) or controllerutils.isBezierController(scaleController):

        return pymxs.runtime.copy(scaleController.value)

    elif wrapperutils.isKindOf(scaleController, pymxs.runtime.Scale_List):

        active = scaleController.getActive() - 1
        subController = scaleController[active].controller

        return pymxs.runtime.copy(subController.value)

    else:

        return getMatrix(node).scalePart


def setScale(node, scale, **kwargs):
    """
    Updates the scale values for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :type scale: list[float, float, float]
    :key skipScale: bool
    :key skipScaleX: bool
    :key skipScaleY: bool
    :key skipScaleZ: bool
    :rtype: None
    """

    # Get transform controller
    #
    transformController = controllerutils.getPRSController(node)

    if pymxs.runtime.classOf(transformController) != pymxs.runtime.PRS:

        log.warning('setScale() expects a PRS controller (%s given)!' % pymxs.runtime.classOf(transformController))
        return

    # Check if this is a scale list
    #
    scaleController = pymxs.runtime.getPropertyController(transformController, 'Scale')

    if controllerutils.isListController(scaleController):

        currentIndex = scaleController.getActive() - 1
        scaleController = scaleController[currentIndex].controller

    # Check controller type
    #
    skipScale = kwargs.get('skipScale', False)
    skipScaleX = kwargs.get('skipScaleX', skipScale)
    skipScaleY = kwargs.get('skipScaleY', skipScale)
    skipScaleZ = kwargs.get('skipScaleZ', skipScale)

    if controllerutils.isXYZController(scaleController):

        # Check if the x-axis should be skipped
        #
        if not skipScaleX:

            scaleController['X_Scale'].controller.value = scale[0]

        # Check if the y-axis should be skipped
        #
        if not skipScaleY:

            scaleController['Y_Scale'].controller.value = scale[1]

        # Check if the z-axis should be skipped
        #
        if not skipScaleZ:

            scaleController['Z_Scale'].controller.value = scale[2]

    elif controllerutils.isBezierController(scaleController):

        # Check which axes should be skipped
        #
        currentScale = pymxs.runtime.copy(scaleController.value)
        filteredScale = [currentScale[i] if skip else scale[i] for (i, skip) in enumerate([skipScaleX, skipScaleY, skipScaleX])]

        scaleController.value = pymxs.runtime.Point3(*filteredScale)

    else:

        log.warning('setScale() expects a XYZ controller (%s given)!' % pymxs.runtime.classOf(scaleController))


def resetScale(node, **kwargs):
    """
    Updates the scale values for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: None
    """

    setScale(node, [1.0, 1.0, 1.0])


def scaleTo(node, scale, **kwargs):
    """
    Scales this node to the specified size.
    Unlike `setScale`, this method adds the scalar difference to the current transform matrix.

    :type node: pymxs.MXSWrapperBase
    :type scale: Union[List[float, float, float], pymxs.runtime.Point3]
    :rtype: None
    """

    currentScale = getMatrix(node).scalePart
    difference = pymxs.runtime.Point3(*scale) - pymxs.runtime.Point3(*currentScale)
    newScale = getScale(node) + difference

    setScale(node, newScale, **kwargs)


def getBoundingBox(node):
    """
    Returns the bounding box for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: list[pymxs.runtime.Point3, pymxs.runtime.Point3]
    """

    # Check if property exist
    #
    minPoint = pymxs.runtime.Point3(0.0, 0.0, 0.0)
    maxPoint = pymxs.runtime.Point3(0.0, 0.0, 0.0)

    if pymxs.runtime.isProperty(node, 'min') and pymxs.runtime.isProperty(node, 'max'):

        minPoint = pymxs.runtime.Point3(node.min.x, node.min.y, node.min.z)
        maxPoint = pymxs.runtime.Point3(node.max.x, node.max.y, node.max.z)

    return minPoint, maxPoint


def isOrthogonal(matrix):
    """
    Evaluates if the supplied transform is orthogonal.

    :type matrix: pymxs.runtime.Matrix3
    :rtype: bool
    """

    xAxis = pymxs.runtime.copy(matrix.row1)
    yAxis = pymxs.runtime.copy(matrix.row2)
    zAxis = pymxs.runtime.copy(matrix.row3)
    cross = pymxs.runtime.cross(xAxis, yAxis)

    return pymxs.runtime.dot(zAxis, cross) > 0.0


def getMatrix(node):
    """
    Returns the transform matrix for the given node.
    It's not safe to access the matrix from the transform controller.
    Any constraints in the controller stack will force the transform into world space!

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.runtime.Matrix3
    """

    worldMatrix = getWorldMatrix(node)
    parentMatrix = getParentMatrix(node)

    return worldMatrix * pymxs.runtime.inverse(parentMatrix)


def getParentMatrix(node):
    """
    Returns the parent matrix for the given node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.runtime.Matrix3
    """

    parent = getattr(node, 'parent', None)

    if parent is not None:

        return getWorldMatrix(parent)

    else:

        return pymxs.runtime.Matrix3(1)


def getParentInverseMatrix(node):
    """
    Returns the parent inverse-matrix for the given node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.runtime.Matrix3
    """

    return pymxs.runtime.inverse(getParentMatrix(node))


def getWorldMatrix(node):
    """
    Returns the world matrix for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.runtime.Matrix3
    """

    matrix = getattr(node, 'transform', pymxs.runtime.Matrix3(1))
    return pymxs.runtime.copy(matrix)


def getWorldInverseMatrix(node):
    """
    Returns the world inverse-matrix for the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.runtime.Matrix3
    """

    return pymxs.runtime.inverse(getWorldMatrix(node))


def applyTransformMatrix(node, matrix, **kwargs):
    """
    Applies the transformation matrix to the supplied node.
    Frozen transforms have a bizarre behaviour.
    The position channel transforms in parent space whereas the rotation channel is in local space?

    :type node: pymxs.runtime.Node
    :type matrix: pymxs.runtime.Matrix3
    :rtype: None
    """

    # Check if node is valid
    # Otherwise, the undo statement will silently error!
    #
    if not pymxs.runtime.isValidNode(node):

        raise TypeError('applyTransformMatrix() expects a valid node!')

    # Define undo chunk
    #
    with pymxs.undo(True, 'Apply Transform Matrix'):

        # Decompose transform matrix
        #
        translation, eulerAngles, scale = decomposeTransformMatrix(matrix, rotateOrder=getRotationOrder(node))

        log.debug('%s.translate = [%s, %s, %s]' % (node.name, translation.x, translation.y, translation.z))
        translateTo(node, translation, **kwargs)

        log.debug('%s.rotate = [%s, %s, %s]' % (node.name, eulerAngles.x, eulerAngles.y, eulerAngles.z))
        rotateTo(node, eulerAngles, **kwargs)

        log.debug('%s.scale = [%s, %s, %s]' % (node.name, scale[0], scale[1], scale[2]))
        scaleTo(node, scale, **kwargs)

        # Freeze transform
        #
        freeze = kwargs.get('freezeTransform', False)

        if freeze:

            freezeTransform(node, **kwargs)


def applyWorldMatrix(node, worldMatrix, **kwargs):
    """
    Applies the world matrix to the supplied node.

    :type node: pymxs.runtime.Node
    :type worldMatrix: pymxs.runtime.Matrix3
    :rtype: None
    """

    parentMatrix = getParentMatrix(node)
    matrix = worldMatrix * pymxs.runtime.inverse(parentMatrix)

    applyTransformMatrix(node, matrix, **kwargs)


def copyTransform(copyFrom, copyTo, **kwargs):
    """
    Copies the transform matrix from one node to another.

    :rtype: None
    """

    worldMatrix = pymxs.runtime.copy(copyFrom.transform)
    applyWorldMatrix(copyTo, worldMatrix, **kwargs)


def freezeTransform(node, **kwargs):
    """
    Freezes the transform values on the supplied node.

    :type node: pymxs.runtime.Node
    :key includeTranslate: bool
    :key includeRotate: bool
    :key includeScale: bool
    :rtype: None
    """

    # Check if translation should be frozen
    #
    includeTranslate = kwargs.get('includeTranslate', True)

    if includeTranslate:

        freezeTranslation(node, **kwargs)

    # Check if rotation should be frozen
    #
    includeRotate = kwargs.get('includeRotate', True)

    if includeRotate:

        freezeRotation(node, **kwargs)

    # Check if scale should be frozen
    #
    includeScale = kwargs.get('includeScale', False)

    if includeScale:

        freezeScale(node, **kwargs)


def unfreezeTransform(node):
    """
    Unfreezes the transform values on the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    # Get transform controller
    #
    transformController = controllerutils.getPRSController(node)

    if not pymxs.runtime.isKindOf(transformController, pymxs.runtime.PRS):

        return

    # Copy transform components
    #
    matrix = pymxs.runtime.copy(transformController.value)

    position = pymxs.runtime.copy(matrix.translationPart)
    rotation = pymxs.runtime.copy(matrix.rotationPart)
    scale = pymxs.runtime.copy(matrix.scalePart)

    # Reset position controller
    #
    positionController = pymxs.runtime.getPropertyController(transformController, 'Position')

    if not pymxs.runtime.isKindOf(positionController, pymxs.runtime.Position_XYZ):

        positionController = pymxs.runtime.Position_XYZ()
        positionController.value = position

        pymxs.runtime.setPropertyController(transformController, 'Position', positionController)

    # Reset rotation controller
    #
    rotationController = pymxs.runtime.getPropertyController(transformController, 'Rotation')

    if not pymxs.runtime.isKindOf(rotationController, pymxs.runtime.Euler_XYZ):

        rotationController = pymxs.runtime.Euler_XYZ()
        rotationController.value = rotation

        pymxs.runtime.setPropertyController(transformController, 'Rotation', rotationController)

    # Reset rotation controller
    #
    scaleController = pymxs.runtime.getPropertyController(transformController, 'Scale')

    if not pymxs.runtime.isKindOf(scaleController, pymxs.runtime.Bezier_Scale):

        scaleController = pymxs.runtime.Bezier_Scale()
        scaleController.value = scale

        pymxs.runtime.setPropertyController(transformController, 'Scale', scaleController)


def freezeTranslation(node, **kwargs):
    """
    Freezes the translation on the supplied node.
    If no position list is found then a new one is created!
    By default, controllers that are constrained are ignored!

    :type node: pymxs.MXSWrapperBase
    :key ignoreConstraints: bool
    :rtype: None
    """

    # Check if position-list exists
    #
    transformController = controllerutils.getPRSController(node)
    positionController = controllerutils.decomposePRSController(transformController)[0]

    matrix = getMatrix(node)

    if controllerutils.isListController(positionController):

        # Ensure sub-controllers have the correct names
        #
        success = controllerutils.ensureFrozenNames(positionController)

        if not success:

            log.warning('Unable to freeze $%s[#position].controller!' % node.name)
            return

        # Check if constraints should be skipped
        #
        ignoreConstraints = kwargs.get('ignoreConstraints', False)
        isConstrained = controllerutils.isConstrained(positionController)

        if (not ignoreConstraints) and isConstrained:

            log.debug('Skipping constrained $%s[#position].controller!' % node.name)
            return

        # Check if frozen position requires updating
        #
        frozenController = pymxs.runtime.getPropertyController(positionController, 'Frozen_Position')
        zeroController = pymxs.runtime.getPropertyController(positionController, 'Zero_Pos_XYZ')

        isFrozen = isClose(frozenController.value, matrix.translationPart)
        isZero = isClose(zeroController.value, pymxs.runtime.Point3(0.0, 0.0, 0.0))

        if not isFrozen or not isZero:

            log.info('Freezing $%s[#position].controller!' % node.name)
            frozenController.value = matrix.translationPart
            zeroController.value = pymxs.runtime.Point3(0.0, 0.0, 0.0)

        else:

            log.debug('Skipping "$%s.position" controller!' % node.name)

    else:

        # Create new position-list
        # This will append the current controller to the new list!
        #
        log.info('Freezing $%s[#position].controller!' % node.name)

        positionController = pymxs.runtime.Position_List()
        pymxs.runtime.setPropertyController(transformController, 'Position', positionController)

        controllerutils.clearListController(positionController)  # Removes pre-existing sub-controllers

        # Add frozen position sub-controller
        #
        frozenController = pymxs.runtime.Bezier_Position()
        frozenController.value = matrix.translationPart

        pymxs.runtime.setPropertyController(positionController, 'Available', frozenController)
        positionController.setName(1, 'Frozen Position')

        # Add zero position sub-controller
        #
        zeroController = pymxs.runtime.Position_XYZ()
        zeroController.value = pymxs.runtime.Point3(0.0, 0.0, 0.0)

        pymxs.runtime.setPropertyController(positionController, 'Available', zeroController)
        positionController.setName(2, 'Zero Pos XYZ')

        # Update active controller
        #
        positionController.setActive(2)


def freezeRotation(node, **kwargs):
    """
    Freezes the rotation on the supplied node.
    If no rotation list is found then a new one is created!
    By default, controllers that are constrained are ignored!

    :type node: pymxs.MXSWrapperBase
    :key ignoreConstraints: bool
    :rtype: None
    """

    # Check if position-list exists
    #
    transformController = controllerutils.getPRSController(node)
    rotationController = controllerutils.decomposePRSController(transformController)[1]

    matrix = getMatrix(node)

    if controllerutils.isListController(rotationController):

        # Ensure sub-controllers have the correct names
        #
        success = controllerutils.ensureFrozenNames(rotationController)

        if not success:

            log.warning('Unable to freeze $%s[#rotation].controller!' % node.name)
            return

        # Check if constraints should be skipped
        #
        ignoreConstraints = kwargs.get('ignoreConstraints', False)
        isConstrained = controllerutils.isConstrained(rotationController)

        if (not ignoreConstraints) and isConstrained:

            log.debug('Skipping constrained $%s[#rotation].controller!' % node.name)
            return

        # Check if frozen rotation requires updating
        #
        frozenController = pymxs.runtime.getPropertyController(rotationController, 'Frozen_Rotation')
        zeroController = pymxs.runtime.getPropertyController(rotationController, 'Zero_Euler_XYZ')

        isFrozen = isClose(frozenController.value, matrix.rotationPart)
        isZero = isClose(zeroController.value, pymxs.runtime.Quat(1))

        if not isFrozen or not isZero:

            log.info('Freezing $%s[#rotation].controller!' % node.name)
            frozenController.value = matrix.rotationPart
            zeroController.value = pymxs.runtime.Quat(1)

        else:

            log.debug('Skipping $%s[#rotation].controller!' % node.name)

    else:

        # Create new rotation-list
        # This will append the current controller to the new list!
        #
        log.info('Freezing $%s[#rotation].controller!' % node.name)

        rotationController = pymxs.runtime.Rotation_List()
        pymxs.runtime.setPropertyController(transformController, 'Rotation', rotationController)

        controllerutils.clearListController(rotationController)  # Removes pre-existing sub-controllers

        # Add frozen rotation sub-controller
        #
        frozenController = pymxs.runtime.Euler_XYZ()
        frozenController.value = matrix.rotationPart

        pymxs.runtime.setPropertyController(rotationController, 'Available', frozenController)
        rotationController.setName(1, 'Frozen Rotation')

        # Add zero rotation sub-controller
        #
        zeroController = pymxs.runtime.Euler_XYZ()
        zeroController.value = pymxs.runtime.Quat(1)

        pymxs.runtime.setPropertyController(rotationController, 'Available', zeroController)
        rotationController.setName(2, 'Zero Euler XYZ')

        # Update active controller
        #
        rotationController.setActive(2)


def freezeScale(node, **kwargs):
    """
    Freezes the scale on the supplied node.
    If no scale list is found then a new one is created!

    :type node: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Check if position-list exists
    #
    transformController = controllerutils.getPRSController(node)
    scaleController = controllerutils.decomposePRSController(transformController)[2]

    matrix = getMatrix(node)

    if controllerutils.isListController(scaleController):

        # Ensure sub-controllers have the correct names
        #
        success = controllerutils.ensureFrozenNames(scaleController)

        if not success:

            log.warning('Unable to freeze $%s[#scale].controller!' % node.name)
            return

        # Check if frozen scale requires updating
        #
        frozenController = pymxs.runtime.getPropertyController(scaleController, 'Frozen_Scale')
        zeroController = pymxs.runtime.getPropertyController(scaleController, 'Zero_Scale_XYZ')

        isFrozen = isClose(frozenController.value, matrix.scalePart)
        isZero = isClose(zeroController.value, pymxs.runtime.Point3(1.0, 1.0, 1.0))

        if not isFrozen or not isZero:

            log.info('Freezing $%s[#scale].controller!' % node.name)
            frozenController.value = matrix.scalePart
            zeroController.value = pymxs.runtime.Point3(1.0, 1.0, 1.0)

        else:

            log.debug('Skipping $%s[#scale].controller!' % node.name)

    else:

        # Create new scale-list
        # This will append the current controller to the new list!
        #
        log.info('Freezing $%s[#scale].controller!' % node.name)

        scaleController = pymxs.runtime.Scale_List()
        pymxs.runtime.setPropertyController(transformController, 'Scale', scaleController)

        controllerutils.clearListController(scaleController)  # Removes pre-existing sub-controllers

        # Add frozen scale sub-controller
        #
        frozenController = pymxs.runtime.Bezier_Scale()
        frozenController.value = matrix.scalePart

        pymxs.runtime.setPropertyController(scaleController, 'Available', frozenController)
        scaleController.setName(1, 'Frozen Scale')

        # Add zero scale sub-controller
        #
        zeroController = pymxs.runtime.Scale_XYZ()
        zeroController.value = pymxs.runtime.Point3(1.0, 1.0, 1.0)

        pymxs.runtime.setPropertyController(scaleController, 'Available', zeroController)
        scaleController.setName(2, 'Zero Scale XYZ')

        # Update active controller
        #
        scaleController.setActive(2)


def requiresFreezing(obj):
    """
    Evaluates if the supplied object requires freezing.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Evaluate transform controller
    # Only PRS controllers can be frozen!
    #
    node, controller = controllerutils.decomposeController(obj)
    prs = controllerutils.findControllerByClass(controller, pymxs.runtime.PRS)

    if not pymxs.runtime.isKindOf(prs, pymxs.runtime.PRS):

        return False

    # Decompose PRS controller
    #
    positionController, rotationController, scaleController = controllerutils.decomposePRSController(prs)

    # Evaluate position controller
    #
    positionList = controllerutils.findControllerByClass(positionController, pymxs.runtime.Position_List)
    success = controllerutils.ensureFrozenNames(positionList)

    matrix = getMatrix(node)

    if controllerutils.isListController(positionList) and success:

        # Evaluate frozen sub-controller
        #
        frozenController = pymxs.runtime.getPropertyController(positionList, 'Frozen_Position')

        if not isClose(frozenController.value, matrix.translationPart, tolerance=1e-2):

            log.debug('$%s[#position] : %s != %s' % (node.name, frozenController.value, matrix.translationPart))
            return True

    else:

        return True

    # Evaluate rotation controller
    #
    rotationList = controllerutils.findControllerByClass(rotationController, pymxs.runtime.Rotation_List)
    success = controllerutils.ensureFrozenNames(rotationList)

    if controllerutils.isListController(rotationList) and success:

        # Evaluate frozen sub-controller
        #
        frozenController = pymxs.runtime.getPropertyController(rotationList, 'Frozen_Rotation')

        if not isClose(frozenController.value, matrix.rotationPart, tolerance=1e-2):

            log.debug('$%s[#rotation] : %s != %s' % (node.name, frozenController.value, matrix.rotationPart))
            return True

    else:

        return True

    return False


def freezePreferredRotation(controller):
    """
    Freezes the preferred angles on the supplied IK controller.

    :type controller: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Check if this is an ik-controller
    #
    if not pymxs.runtime.isKindOf(controller, pymxs.runtime.IKControl):

        raise TypeError('freezePreferredRotation() expects an IKControl!')

    # Get euler rotation
    #
    node = pymxs.runtime.refs.dependentNodes(controller, firstOnly=True)
    matrix = getMatrix(node)

    eulerAngles = pymxs.runtime.quatToEuler(matrix.rotationPart)

    # Update preferred rotation
    #
    log.info('Freezing "%s" ik-control\'s preferred rotation!' % node.name)

    controller.preferred_rotation_x = eulerAngles.x
    controller.preferred_rotation_y = eulerAngles.y
    controller.preferred_rotation_z = eulerAngles.z


def isArray(value):
    """
    Evaluates if the supplied value is an array.

    :type value: Any
    :rtype: bool
    """

    return hasattr(value, '__getitem__') and hasattr(value, '__len__')


def isClose(value, otherValue, tolerance=1e-3):
    """
    Evaluates if the two values are close.

    :type value: Union[int, float, pymxs.MXSWrapperBase]
    :type otherValue: Union[int, float, pymxs.MXSWrapperBase]
    :type tolerance: float
    :rtype: bool
    """

    # Ensure values are the same type
    #
    if pymxs.runtime.classOf(value) != pymxs.runtime.classOf(otherValue):

        raise TypeError('isClose() expects two values of the same type!')

    # Evaluate value type
    #
    if isinstance(value, (int, float)):

        return abs(value - otherValue) <= tolerance

    elif wrapperutils.isKindOf(value, pymxs.runtime.Point3):

        return all(
            [
                isClose(value.x, otherValue.x, tolerance=tolerance),
                isClose(value.y, otherValue.y, tolerance=tolerance),
                isClose(value.z, otherValue.z, tolerance=tolerance)
            ]
        )

    elif wrapperutils.isKindOf(value, pymxs.runtime.EulerAngles):

        return isClose(eulerAnglesToMatrix3(value), eulerAnglesToMatrix3(otherValue), tolerance=tolerance)

    elif wrapperutils.isKindOf(value, pymxs.runtime.Quat):

        return isClose(quatToMatrix3(value), quatToMatrix3(otherValue), tolerance=tolerance)

    elif wrapperutils.isKindOf(value, pymxs.runtime.Matrix3):

        return all(
            [
                isClose(value.row1, otherValue.row1, tolerance=tolerance),
                isClose(value.row2, otherValue.row2, tolerance=tolerance),
                isClose(value.row3, otherValue.row3, tolerance=tolerance),
                isClose(value.row4, otherValue.row4, tolerance=tolerance)
            ]
        )

    else:

        raise TypeError('isClose() expects a pair of numerical values!')


def resetTransform(node):
    """
    Resets the transform controller on the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: None
    """

    transformController = pymxs.runtime.getTMController(node)
    transformController.value = pymxs.runtime.Matrix3(1)


def resetObjectTransform(node):
    """
    Resets the object transform on the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: None
    """

    node.objectOffsetPos = pymxs.runtime.Point3(0.0, 0.0, 0.0)
    node.objectOffsetRot = pymxs.runtime.Quat(1)
    node.objectOffsetScale = pymxs.runtime.Point3(1.0, 1.0, 1.0)


def decomposeTransformNode(node, worldSpace=False):
    """
    Breaks the node's transform matrix down into the translate, rotate and scale components.

    :type node: pymxs.runtime.Node
    :type worldSpace: bool
    :rtype: pymxs.runtime.Point3, pymxs.runtime.EulerAngles, list[float, float, float]
    """

    rotateOrder = getRotationOrder(node)

    if worldSpace:

        worldMatrix = getWorldMatrix(node)
        return decomposeTransformMatrix(worldMatrix, rotateOrder=rotateOrder)

    else:

        translation = getTranslation(node)
        rotation = getEulerRotation(node)
        scale = getScale(node)

        return translation, rotation, scale


def decomposeTransformMatrix(matrix, rotateOrder=1):
    """
    Breaks the transform matrix down into its translate, rotate and scale components.

    :type matrix: pymxs.runtime.Matrix3
    :type rotateOrder: int
    :rtype: pymxs.runtime.Point3, pymxs.runtime.EulerAngles, list[float, float, float]
    """

    translation = pymxs.runtime.copy(matrix.row4)
    eulerRotation = pymxs.runtime.quatToEuler(matrix.rotationPart, order=rotateOrder)
    scale = [pymxs.runtime.length(matrix.row1), pymxs.runtime.length(matrix.row2), pymxs.runtime.length(matrix.row3)]

    return translation, eulerRotation, scale


def breakMatrix(matrix, normalize=False):
    """
    Breaks the matrix down into the XYZ axis vectors.

    :type matrix: pymxs.runtime.Matrix3
    :type normalize: bool
    :rtype: pymxs.runtime.Point3, pymxs.runtime.Point3, pymxs.runtime.Point3, pymxs.runtime.Point3
    """

    row1 = pymxs.runtime.copy(matrix.row1)
    row2 = pymxs.runtime.copy(matrix.row2)
    row3 = pymxs.runtime.copy(matrix.row3)
    row4 = pymxs.runtime.copy(matrix.row4)

    if normalize:

        row1 = pymxs.runtime.normalize(row1)
        row2 = pymxs.runtime.normalize(row2)
        row3 = pymxs.runtime.normalize(row3)

    return row1, row2, row3, row4


def mirrorVector(vector, normal):
    """
    Returns a mirrored vector across the supplied normal.

    :type vector: pymxs.runtime.Point3
    :type normal: pymxs.runtime.Point3
    :rtype: pymxs.runtime.Point3
    """

    return vector - (2.0 * (pymxs.runtime.dot(vector, normal)) * normal)


def mirrorMatrix(matrix, normal):
    """
    Returns a mirrored matrix across the supplied normal.

    :type matrix: pymxs.runtime.Matrix3
    :type normal: pymxs.runtime.Point3
    :rtype: pymxs.runtime.Matrix3
    """

    row1 = mirrorVector(pymxs.runtime.copy(matrix.row1), normal)
    row2 = mirrorVector(pymxs.runtime.copy(matrix.row2), normal)
    row3 = pymxs.runtime.cross(row1, row2)  # Ensures matrix is orthogonal!
    row4 = mirrorVector(pymxs.runtime.copy(matrix.row4), normal)

    return pymxs.runtime.Matrix3(row1, row2, row3, row4)


def mirrorNode(node, normal, offsetMatrix=None):
    """
    Mirrors the node's transform matrix, across the supplied normal, to the opposite node.
    If no mirror pair is found then nothing happens.

    :type node: pymxs.runtime.Node
    :type normal: pymxs.runtime.Point3
    :type offsetMatrix: pymxs.runtime.Matrix3
    :rtype: None
    """

    # Mirror world matrix
    #
    matrix = getWorldMatrix(node)
    newMatrix = mirrorMatrix(matrix, normal)

    if offsetMatrix is not None:

        newMatrix = (offsetMatrix * newMatrix)

    # Locate opposite node
    #
    otherName = namingutils.mirrorName(node.name)
    otherNode = pymxs.runtime.getNodeByName(otherName)

    if otherNode is not None:

        applyWorldMatrix(otherNode, newMatrix)

    else:

        log.error('Unable to locate mirror pair: %s => %s' % (node.name, otherName))


def quatToMatrix3(quat):
    """
    Converts the supplied quaternion to a rotation matrix.

    :type quat: pymxs.runtime.Quat
    :rtype: pymxs.runtime.Matrix3
    """

    return __quat_to_matrix3__(quat)


def eulerAnglesToMatrix3(eulerAngles):
    """
    Converts the supplied euler angles to a rotation matrix.

    :type eulerAngles: pymxs.runtime.EulerAngles
    :rtype: pymxs.runtime.Matrix3
    """

    return __euler_to_matrix3__(eulerAngles)

