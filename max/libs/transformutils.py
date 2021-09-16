import pymxs
import math

from dcc.max.libs import controllerutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def copyTransform(copyFrom, copyTo, **kwargs):
    """
    Copies the transform matrix from one node to another.

    :rtype: None
    """

    worldMatrix = pymxs.runtime.copy(copyFrom.transform)
    applyWorldMatrix(copyTo, worldMatrix, **kwargs)


def applyTransformMatrix(node, matrix, **kwargs):
    """
    Applies the transformation matrix to the supplied node.

    :type node: pymxs.runtime.Node
    :type matrix: pymxs.runtime.Matrix3
    :rtype: None
    """

    translation, rotation, scale = decomposeMatrix(matrix)

    setTranslation(node, translation, **kwargs)
    setEulerRotation(node, rotation, **kwargs)
    setScale(node, scale, **kwargs)


def applyWorldMatrix(node, worldMatrix, **kwargs):
    """
    Applies the world matrix to the supplied node.
    Frozen transforms have a bizarre behaviour.
    The position channel transforms in parent space whereas the rotation channel is in local space?

    :type node: pymxs.runtime.Node
    :type worldMatrix: pymxs.runtime.Matrix3
    :rtype: None
    """

    # Multiply world matrix into parent space
    #
    offsetMatrix = kwargs.get('offsetMatrix', pymxs.runtime.Matrix3(1))
    parentMatrix = getParentMatrix(node)
    frozenPositionMatrix = getFrozenPositionMatrix(node)
    frozenRotationMatrix = getFrozenRotationMatrix(node)

    position = ((offsetMatrix * worldMatrix) * pymxs.runtime.inverse(frozenPositionMatrix * parentMatrix)).translationPart
    rotation = ((offsetMatrix * worldMatrix) * pymxs.runtime.inverse(frozenRotationMatrix * parentMatrix)).rotationPart

    matrix = quatToMatrix3(rotation) * pymxs.runtime.transMatrix(position)

    # Apply matrix to node
    #
    applyTransformMatrix(node, matrix, **kwargs)


def freezeTranslation(node):
    """
    Freezes the translation on the supplied node.
    If no position list is found then a new one is created.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    # Copy transform matrix
    #
    transformController = pymxs.runtime.getTMController(node)
    matrix = pymxs.runtime.copy(transformController.value) * pymxs.runtime.inverse(getParentMatrix(node))

    position = pymxs.runtime.copy(matrix.translationPart)

    if sum(position) == 0.0:

        return

    # Check if position list exists
    #
    positionController = pymxs.runtime.getPropertyController(transformController, 'Position')

    if not controllerutils.isListController(positionController):

        positionController = pymxs.runtime.Position_List()
        pymxs.runtime.setPropertyController(transformController, 'Position', positionController)

        pymxs.runtime.setPropertyController(positionController, 'Available', pymxs.runtime.Bezier_Position())
        pymxs.runtime.setPropertyController(positionController, 'Available', pymxs.runtime.Position_XYZ())

        positionController.delete(1)  # Delete the previous controller from the list!
        positionController.setName(1, 'Frozen Position')
        positionController.setName(2, 'Zero Pos XYZ')
        positionController.setActive(2)

    # Update frozen position subanim
    #
    frozenController = pymxs.runtime.getPropertyController(positionController, 'Frozen Position')
    activeController = pymxs.runtime.getPropertyController(positionController, 'Zero Pos XYZ')

    frozenController.value = position
    activeController.value = pymxs.runtime.Point3(0.0, 0.0, 0.0)


def freezeRotation(node):
    """
    Freezes the rotation on the supplied node.
    If no rotation list is found then a new one is created.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    # Copy transform matrix
    #
    transformController = pymxs.runtime.getTMController(node)
    matrix = pymxs.runtime.copy(transformController.value) * pymxs.runtime.inverse(getParentMatrix(node))

    rotation = pymxs.runtime.copy(matrix.rotationPart)

    if pymxs.runtime.isIdentity(rotation):

        return

    # Check if rotation list exists
    #
    rotationController = pymxs.runtime.getPropertyController(transformController, 'Rotation')

    if not controllerutils.isListController(rotationController):

        rotationController = pymxs.runtime.Rotation_List()
        pymxs.runtime.setPropertyController(transformController, 'Rotation', rotationController)

        pymxs.runtime.setPropertyController(rotationController, 'Available', pymxs.runtime.Bezier_Rotation())
        pymxs.runtime.setPropertyController(rotationController, 'Available', pymxs.runtime.Euler_XYZ())

        rotationController.delete(1)  # Delete the previous controller from the list!
        rotationController.setName(1, 'Frozen Rotation')
        rotationController.setName(2, 'Zero Euler XYZ')
        rotationController.setActive(2)

    # Update frozen rotation subanim
    #
    frozenController = pymxs.runtime.getPropertyController(rotationController, 'Frozen Rotation')
    activeController = pymxs.runtime.getPropertyController(rotationController, 'Zero Euler XYZ')

    frozenController.value = rotation
    activeController.value = pymxs.runtime.Quat(0.0, 0.0, 0.0, 1.0)


def freezeScale(node):
    """
    Freezes the scale on the supplied node.
    If no scale list is found then a new one is created.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    # Copy transform matrix
    #
    transformController = pymxs.runtime.getTMController(node)
    matrix = pymxs.runtime.copy(transformController.value) * pymxs.runtime.inverse(getParentMatrix(node))

    scale = pymxs.runtime.copy(matrix.scalePart)

    if sum(scale) == 3.0:

        return

    # Freeze scale controller
    #
    scaleController = pymxs.runtime.getPropertyController(transformController, 'Scale')

    if not controllerutils.isListController(scaleController):

        scaleController = pymxs.runtime.Scale_List()
        pymxs.runtime.setPropertyController(transformController, 'Scale', scaleController)

        pymxs.runtime.setPropertyController(scaleController, 'Available', pymxs.runtime.Bezier_Scale())
        pymxs.runtime.setPropertyController(scaleController, 'Available', pymxs.runtime.ScaleXYZ())

        scaleController.delete(1)  # Delete the previous controller from the list!
        scaleController.setName(1, 'Frozen Scale')
        scaleController.setName(2, 'Zero Scale XYZ')
        scaleController.setActive(2)

    # Update frozen scale subanim
    #
    frozenController = pymxs.runtime.getPropertyController(scaleController, 'Frozen Scale')
    activeController = pymxs.runtime.getPropertyController(scaleController, 'Zero Scale XYZ')

    frozenController.value = scale
    activeController.value = [1.0, 1.0, 1.0]


def freezeTransform(node):
    """
    Freezes the transform on the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    freezeTranslation(node)
    freezeRotation(node)
    #freezeScale(node)


def getFrozenPositionMatrix(node):
    """
    Returns the frozen position matrix from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Matrix3
    """

    # Check if controller has position list
    #
    transformController = pymxs.runtime.getTMController(node)
    positionController = transformController[pymxs.runtime.Name('position')].controller

    if controllerutils.isListController(positionController):

        controller = positionController[pymxs.runtime.Name('frozen_position')].controller
        return pymxs.runtime.transMatrix(controller.value)

    else:

        return pymxs.runtime.Matrix3(1)


def getFrozenRotationMatrix(node):
    """
    Returns the frozen rotation matrix from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Matrix3
    """

    # Check if controller has rotation list
    #
    transformController = pymxs.runtime.getTMController(node)
    rotationController = transformController[pymxs.runtime.Name('rotation')].controller

    if controllerutils.isListController(rotationController):

        controller = rotationController[pymxs.runtime.Name('frozen_rotation')].controller
        return quatToMatrix3(controller.value)

    else:

        return pymxs.runtime.Matrix3(1)


def getParentMatrix(node):
    """
    Returns the parent matrix for the given node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Matrix3
    """

    parent = node.parent

    if parent is not None:

        return pymxs.runtime.copy(parent.transform)

    else:

        return pymxs.runtime.Matrix3(1)


def decomposeMatrix(matrix, rotateOrder=1):
    """
    Breaks apart the matrix into its individual translate, rotate and scale components.
    A rotation order must be supplied in order to be resolved correctly.

    :type matrix: pymxs.runtime.Matrix3
    :type rotateOrder: int
    :rtype: pymxs.runtime.Point3, pymxs.runtime.EulerAngles, list[float, float, float]
    """

    translation = pymxs.runtime.copy(matrix.row4)
    eulerRotation = pymxs.runtime.quatToEuler(matrix.rotationPart, order=rotateOrder)
    scale = [pymxs.runtime.length(matrix.row1), pymxs.runtime.length(matrix.row2), pymxs.runtime.length(matrix.row3)]

    return translation, eulerRotation, scale


def quatToMatrix3(quat):
    """
    Converts the supplied quaternion to a rotation matrix.
    See the following for details:
    https://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToMatrix/index.htm

    :type quat: pymxs.runtime.Quat
    :rtype: pymxs.runtime.Matrix3
    """

    sqw = quat.w * quat.w
    sqx = quat.x * quat.x
    sqy = quat.y * quat.y
    sqz = quat.z * quat.z

    inverse = 1.0 / (sqx + sqy + sqz + sqw)
    m00 = (sqx - sqy - sqz + sqw) * inverse
    m11 = (-sqx + sqy - sqz + sqw) * inverse
    m22 = (-sqx - sqy + sqz + sqw) * inverse

    tmp1 = quat.x * quat.y
    tmp2 = quat.z * quat.w
    m10 = 2.0 * (tmp1 + tmp2) * inverse
    m01 = 2.0 * (tmp1 - tmp2) * inverse

    tmp1 = quat.x * quat.z
    tmp2 = quat.y * quat.w
    m20 = 2.0 * (tmp1 - tmp2) * inverse
    m02 = 2.0 * (tmp1 + tmp2) * inverse
    tmp1 = quat.y * quat.z
    tmp2 = quat.x * quat.w
    m21 = 2.0 * (tmp1 + tmp2) * inverse
    m12 = 2.0 * (tmp1 - tmp2) * inverse

    return pymxs.runtime.Matrix3(
        pymxs.runtime.Point3(m00, m01, m02),
        pymxs.runtime.Point3(m10, m11, m12),
        pymxs.runtime.Point3(m20, m21, m22),
        pymxs.runtime.Point3(0.0, 0.0, 0.0)
    )


def eulerAnglesToMatrix3(eulerAngles):
    """
    Converts the supplied euler angles to a rotation matrix.
    Yaw = Y, Pitch = X, Roll = Z

    :type eulerAngles: pymxs.runtime.EulerAngles
    :rtype: pymxs.runtime.Matrix3
    """

    return pymxs.runtime.rotateYPRMatrix(eulerAngles.y, eulerAngles.x, eulerAngles.z)


def getTranslation(node):
    """
    Returns the translation values from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Point3
    """

    return pymxs.runtime.getTMController(node)[pymxs.runtime.Name('Position')].controller.value


def setTranslation(node, translation, **kwargs):
    """
    Assigns the translation values to the supplied node.

    :type node: pymxs.runtime.Node
    :type translation: pymxs.runtime.Point3
    :rtype: None
    """

    # Get position controller
    #
    transformController = pymxs.runtime.getTMController(node)
    positionController = pymxs.runtime.getPropertyController(transformController, 'Position')

    # Check if this is a position list
    #
    if controllerutils.isListController(positionController):

        currentIndex = positionController.getActive() - 1
        positionController = positionController[currentIndex].controller

    # Check controller type
    #
    skipTranslate = kwargs.get('skipTranslate', False)

    if controllerutils.isXYZController(positionController):

        # Check if x-value can be set
        #
        skipTranslateX = kwargs.get('skipTranslateX', skipTranslate)

        if not skipTranslateX:

            positionController[pymxs.runtime.Name('X_Position')].controller.value = translation.x

        # Check if y-value can be set
        #
        skipTranslateY = kwargs.get('skipTranslateY', skipTranslate)

        if not skipTranslateY:

            positionController[pymxs.runtime.Name('Y_Position')].controller.value = translation.y

        # Check if z-value can be set
        #
        skipTranslateZ = kwargs.get('skipTranslateZ', skipTranslate)

        if not skipTranslateZ:

            positionController[pymxs.runtime.Name('Z_Position')].controller.value = translation.z

    elif controllerutils.isBezierController(positionController):

        positionController.value = translation

    else:

        raise TypeError('setTranslation() expects a XYZ controller!')


def getEulerRotation(node):
    """
    Returns the euler angles from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.EulerAngles
    """

    return pymxs.runtime.getTMController(node)[pymxs.runtime.Name('Rotation')].controller.value


def setEulerRotation(node, eulerAngles, **kwargs):
    """
    Assigns the euler angles to the supplied node.

    :type node: pymxs.runtime.Node
    :type eulerAngles: pymxs.runtime.EulerAngles
    :rtype: None
    """

    # Get rotation controller
    #
    transformController = pymxs.runtime.getTMController(node)
    rotationController = pymxs.runtime.getPropertyController(transformController, 'Rotation')

    # Check if this is a rotation list
    #
    if controllerutils.isListController(rotationController):

        currentIndex = rotationController.getActive() - 1
        rotationController = rotationController[currentIndex].controller

    # Check controller type
    #
    skipRotate = kwargs.get('skipRotate', False)

    if controllerutils.isXYZController(rotationController):

        # Check if x-value can be set
        #
        skipRotateX = kwargs.get('skipRotateX', skipRotate)

        if not skipRotateX:

            rotationController[pymxs.runtime.Name('X_Rotation')].controller.value = eulerAngles.x

        # Check if y-value can be set
        #
        skipRotateY = kwargs.get('skipRotateY', skipRotate)

        if not skipRotateY:

            rotationController[pymxs.runtime.Name('Y_Rotation')].controller.value = eulerAngles.y

        # Check if z-value can be set
        #
        skipRotateZ = kwargs.get('skipRotateZ', skipRotate)

        if not skipRotateZ:

            rotationController[pymxs.runtime.Name('Z_Rotation')].controller.value = eulerAngles.z

    elif controllerutils.isBezierController(rotationController):

        rotationController.value = eulerAngles

    else:

        raise TypeError('setRotation() expects a XYZ controller!')


def getScale(node):
    """
    Returns the scale value from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: list[float, float, float]
    """

    return pymxs.runtime.getTMController(node)[pymxs.runtime.Name('scale')].controller.value


def setScale(node, scale, **kwargs):
    """
    Assigns the scale values to the supplied node.

    :type node: pymxs.runtime.Node
    :type scale: list[float, float, float]
    :rtype: None
    """

    # Get rotation controller
    #
    transformController = pymxs.runtime.getTMController(node)
    scaleController = pymxs.runtime.getPropertyController(transformController, 'Scale')

    # Check if this is a rotation list
    #
    if controllerutils.isListController(scaleController):

        currentIndex = scaleController.getActive() - 1
        scaleController = scaleController[currentIndex].controller

    # Check controller type
    #
    skipScale = kwargs.get('skipScale', False)

    if controllerutils.isXYZController(scaleController):

        # Check if x-value can be set
        #
        skipScaleX = kwargs.get('skipScaleX', skipScale)

        if not skipScaleX:

            scaleController[pymxs.runtime.Name('X_Scale')].controller.value = scale[0]

        # Check if y-value can be set
        #
        skipScaleY = kwargs.get('skipScaleY', skipScale)

        if not skipScaleY:

            scaleController[pymxs.runtime.Name('Y_Scale')].controller.value = scale[1]

        # Check if z-value can be set
        #
        skipScaleZ = kwargs.get('skipScaleZ', skipScale)

        if not skipScaleZ:

            scaleController[pymxs.runtime.Name('Z_Scale')].controller.value = scale[2]

    elif controllerutils.isBezierController(scaleController):

        scaleController.value = scale

    else:

        raise TypeError('setScale() expects a XYZ controller!')
