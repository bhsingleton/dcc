import pymxs

from dcc.max.libs import controllerutils, nodeutils
from dcc.naming import namingutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getTranslation(node):
    """
    Returns the translation values from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Point3
    """

    transformController = pymxs.runtime.getTMController(node)

    if pymxs.runtime.classOf(transformController) == pymxs.runtime.PRS:

        positionController = pymxs.runtime.getPropertyController(node, pymxs.runtime.Name('Position'))
        return positionController.value

    else:

        position = decomposeTransformNode(node)[0]
        return position


def setTranslation(node, translation, **kwargs):
    """
    Updates the translation values for the supplied node.

    :type node: pymxs.runtime.Node
    :type translation: pymxs.runtime.Point3
    :key skipTranslate: bool
    :key skipTranslateX: bool
    :key skipTranslateY: bool
    :key skipTranslateZ: bool
    :rtype: None
    """

    # Get transform controller
    #
    transformController = pymxs.runtime.getTMController(node)

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

    if controllerutils.isXYZController(positionController):

        # Check if x-value can be set
        #
        skipTranslateX = kwargs.get('skipTranslateX', skipTranslate)

        if not skipTranslateX:

            positionController['X_Position'].controller.value = translation.x

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

        log.warning('setTranslation() expects a XYZ controller (%s given)!' % pymxs.runtime.classOf(positionController))


def resetTranslation(node, **kwargs):
    """
    Resets the translation values for the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    setTranslation(node, pymxs.runtime.Point3(0.0, 0.0, 0.0))


def getRotationOrder(node):
    """
    Returns the rotation order for the supplied node.
    Please be aware that not all controllers have an axis order property!

    :type node: pymxs.runtime.Node
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

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.EulerAngles
    """

    transformController = pymxs.runtime.getTMController(node)

    if pymxs.runtime.classOf(transformController) == pymxs.runtime.PRS:

        rotationController = pymxs.runtime.getPropertyController(node, pymxs.runtime.Name('Rotation'))
        return rotationController.value

    else:

        rotation = decomposeTransformNode(node)[1]
        return rotation


def setEulerRotation(node, eulerAngles, **kwargs):
    """
    Updates the euler angles for the supplied node.

    :type node: pymxs.runtime.Node
    :type eulerAngles: pymxs.runtime.EulerAngles
    :key skipRotate: bool
    :key skipRotateX: bool
    :key skipRotateY: bool
    :key skipRotateZ: bool
    :rtype: None
    """

    # Get transform controller
    #
    transformController = pymxs.runtime.getTMController(node)

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

        log.warning('setRotation() expects a XYZ controller (%s given)!' % pymxs.runtime.classOf(rotationController))


def resetEulerRotation(node, **kwargs):
    """
    Updates the euler angles for the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    setEulerRotation(node, pymxs.runtime.EulerAngles(0.0, 0.0, 0.0))


def getScale(node):
    """
    Returns the scale value from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: list[float, float, float]
    """

    transformController = pymxs.runtime.getTMController(node)

    if pymxs.runtime.classOf(transformController) == pymxs.runtime.PRS:

        scaleController = pymxs.runtime.getPropertyController(node, pymxs.runtime.Name('Scale'))
        return scaleController.value

    else:

        scale = decomposeTransformNode(node)[2]
        return scale


def setScale(node, scale, **kwargs):
    """
    Updates the scale values for the supplied node.

    :type node: pymxs.runtime.Node
    :type scale: list[float, float, float]
    :key skipScale: bool
    :key skipScaleX: bool
    :key skipScaleY: bool
    :key skipScaleZ: bool
    :rtype: None
    """

    # Get transform controller
    #
    transformController = pymxs.runtime.getTMController(node)

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

        log.warning('setScale() expects a XYZ controller (%s given)!' % pymxs.runtime.classOf(scaleController))


def resetScale(node, **kwargs):
    """
    Updates the scale values for the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    setScale(node, [1.0, 1.0, 1.0])


def getBoundingBox(node):
    """
    Returns the bounding box for the supplied node.

    :type node: pymxs.runtime.Node
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


def getMatrix(node):
    """
    Returns the transform matrix for the given node.
    Please be aware the transform controller returns the local transform matrix.
    Whereas the transform property returns the world matrix.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Matrix3
    """

    transformController = pymxs.runtime.getTMController(node)
    return pymxs.runtime.copy(transformController.value)


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


def getWorldMatrix(node):
    """
    Returns the world matrix for the given node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Matrix3
    """

    worldMatrix = getMatrix(node)

    for parent in nodeutils.iterParents(node):

        matrix = getMatrix(parent)
        worldMatrix *= matrix

    return worldMatrix


def getFrozenPositionMatrix(node):
    """
    Returns the frozen position matrix from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Matrix3
    """

    # Check if node has PRS controller
    #
    transformController = pymxs.runtime.getTMController(node)

    if pymxs.runtime.classOf(transformController) != pymxs.runtime.PRS:

        return pymxs.runtime.Matrix3(1)

    # Check if controller has position list
    #
    positionController = pymxs.runtime.getPropertyController(transformController, pymxs.runtime.Name('position'))

    if controllerutils.isListController(positionController):

        controller = pymxs.runtime.getPropertyController(positionController, pymxs.runtime.Name('frozen_position'))
        return pymxs.runtime.transMatrix(controller.value)

    else:

        return pymxs.runtime.Matrix3(1)


def getFrozenRotationMatrix(node):
    """
    Returns the frozen rotation matrix from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Matrix3
    """

    # Check if node has PRS controller
    #
    transformController = pymxs.runtime.getTMController(node)

    if pymxs.runtime.classOf(transformController) != pymxs.runtime.PRS:

        return pymxs.runtime.Matrix3(1)

    # Check if controller has rotation list
    #
    rotationController = pymxs.runtime.getPropertyController(transformController, pymxs.runtime.Name('rotation'))

    if controllerutils.isListController(rotationController):

        controller = pymxs.runtime.getPropertyController(rotationController, pymxs.runtime.Name('frozen_rotation'))
        return quatToMatrix3(controller.value)

    else:

        return pymxs.runtime.Matrix3(1)


def applyTransformMatrix(node, matrix, **kwargs):
    """
    Applies the transformation matrix to the supplied node.
    Frozen transforms have a bizarre behaviour.
    The position channel transforms in parent space whereas the rotation channel is in local space?

    :type node: pymxs.runtime.Node
    :type matrix: pymxs.runtime.Matrix3
    :rtype: None
    """

    # Define undo chunk
    #
    with pymxs.undo(True, 'Apply Transform Matrix'):

        # Derive translation in frozen space
        #
        frozenPositionMatrix = getFrozenPositionMatrix(node)
        translateMatrix = matrix * pymxs.runtime.inverse(frozenPositionMatrix)

        translation = decomposeTransformMatrix(translateMatrix)[0]

        # Derive rotation in frozen space
        #
        frozenRotationMatrix = getFrozenRotationMatrix(node)
        rotationMatrix = matrix * pymxs.runtime.inverse(frozenRotationMatrix)

        rotation = decomposeTransformMatrix(rotationMatrix)[1]

        # Decompose transform and apply to controllers
        #
        scale = decomposeTransformMatrix(matrix)[2]

        setTranslation(node, translation, **kwargs)
        setEulerRotation(node, rotation, **kwargs)
        setScale(node, scale, **kwargs)


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


def freezeTransform(node, includeTranslate=True, includeRotate=True, includeScale=False):
    """
    Freezes the transform values on the supplied node.

    :type node: pymxs.runtime.Node
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
    Unfreezes the transform values on the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: None
    """

    # Get transform controller
    #
    transformController = pymxs.runtime.getTMController(node)

    if pymxs.runtime.classOf(transformController) != pymxs.runtime.PRS:

        return

    # Copy transform components
    #
    matrix = pymxs.runtime.copy(transformController.value)

    position = pymxs.runtime.copy(matrix.translationPart)
    rotation = pymxs.runtime.copy(matrix.rotationPart)
    scale = pymxs.runtime.copy(matrix.scalePart)

    # Reset position controller
    #
    positionController = pymxs.runtime.Position_XYZ()
    positionController.value = position

    pymxs.runtime.setPropertyController(transformController, 'Position', positionController)

    # Reset rotation controller
    #
    rotationController = pymxs.runtime.Euler_XYZ()
    rotationController.value = rotation

    pymxs.runtime.setPropertyController(transformController, 'Rotation', rotationController)

    # Reset rotation controller
    #
    scaleController = pymxs.runtime.Bezier_Scale()
    scaleController.value = scale

    pymxs.runtime.setPropertyController(transformController, 'Scale', scaleController)


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
    matrix = pymxs.runtime.copy(transformController.value)

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

    # Update frozen position
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
    matrix = pymxs.runtime.copy(transformController.value)

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

    # Update frozen rotation
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
    matrix = pymxs.runtime.copy(transformController.value)

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

    # Update frozen scale
    #
    frozenController = pymxs.runtime.getPropertyController(scaleController, 'Frozen Scale')
    activeController = pymxs.runtime.getPropertyController(scaleController, 'Zero Scale XYZ')

    frozenController.value = scale
    activeController.value = [1.0, 1.0, 1.0]


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
    Breaks the transform matrix down into the translate, rotate and scale components.

    :type matrix: pymxs.runtime.Matrix3
    :type rotateOrder: int
    :rtype: pymxs.runtime.Point3, pymxs.runtime.EulerAngles, list[float, float, float]
    """

    translation = pymxs.runtime.copy(matrix.row4)
    eulerRotation = pymxs.runtime.quatToEuler(matrix.rotationPart, order=rotateOrder)
    scale = [pymxs.runtime.length(matrix.row1), pymxs.runtime.length(matrix.row2), pymxs.runtime.length(matrix.row3)]

    return translation, eulerRotation, scale


def decomposeMatrix(matrix, normalize=False):
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
    row3 = pymxs.runtime.cross(row1, row2)  # Lets keep this matrix orthogonal!
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

