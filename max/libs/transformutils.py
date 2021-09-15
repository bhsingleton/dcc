import pymxs
import math

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def copyTransform(copyFrom, copyTo, **kwargs):
    """
    Copies the transform matrix from one node to another.

    :rtype: None
    """

    # Multiply transform into parent space
    #
    worldMatrix = pymxs.runtime.copy(copyFrom.transform)
    parentMatrix = getParentMatrix(copyTo)
    frozenMatrix = getFrozenMatrix(copyTo)

    matrix = worldMatrix * pymxs.runtime.inverse(frozenMatrix * parentMatrix)

    # Apply matrix to node
    #
    applyTransformMatrix(copyTo, matrix)


def applyTransformMatrix(node, matrix, **kwargs):
    """
    Applies the transform matrix to the supplied node.

    :type node: pymxs.runtime.Node
    :type matrix: pymxs.runtime.Matrix3
    :rtype: None
    """

    translation, rotation, scale = decomposeMatrix(matrix)

    setTranslation(node, translation, **kwargs)
    setEulerRotation(node, rotation, **kwargs)
    setScale(node, scale, **kwargs)


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


def getFrozenMatrix(node):
    """
    Returns the frozen matrix for the supplied node.
    If the node has not been frozen then an identity matrix is returned instead.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Matrix3
    """

    # Get transform controller
    #
    transformController = pymxs.runtime.getTMController(node)
    matrix = pymxs.runtime.Matrix3(1)

    # Check if controller has scale list
    #
    scaleController = transformController[pymxs.runtime.Name('scale')].controller

    if pymxs.runtime.classOf(scaleController) == pymxs.runtime.Scale_list:

        controller = scaleController[pymxs.runtime.Name('frozen_scale')].controller
        matrix *= pymxs.runtime.scaleMatrix(controller.value)

    # Check if controller has rotation list
    #
    rotationController = transformController[pymxs.runtime.Name('rotation')].controller

    if pymxs.runtime.classOf(rotationController) == pymxs.runtime.Rotation_list:

        controller = rotationController[pymxs.runtime.Name('frozen_rotation')].controller
        matrix *= quatToMatrix3(controller.value)

    # Check if controller has position list
    #
    positionController = transformController[pymxs.runtime.Name('position')].controller

    if pymxs.runtime.classOf(positionController) == pymxs.runtime.Position_list:

        controller = positionController[pymxs.runtime.Name('frozen_position')].controller
        matrix *= pymxs.runtime.transMatrix(controller.value)

    return matrix


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


def getTranslation(node):
    """
    Returns the translation values from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.Point3
    """

    pass


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
    positionController = transformController[pymxs.runtime.Name('position')].controller

    # Check if this is a position list
    #
    if pymxs.runtime.classOf(positionController) == pymxs.runtime.Position_List:

        currentIndex = positionController.getActive() - 1
        positionController = positionController[currentIndex].controller

    # Check if translateX can be set
    #
    skipTranslate = kwargs.get('skipTranslate', False)
    skipTranslateX = kwargs.get('skipTranslateX', skipTranslate)

    if not skipTranslateX:

        positionController[pymxs.runtime.Name('position_x')].controller.value = translation.x

    # Check if translateY can be set
    #
    skipTranslateY = kwargs.get('skipTranslateY', skipTranslate)

    if not skipTranslateY:

        positionController[pymxs.runtime.Name('position_y')].controller.value = translation.y

    # Check if translateZ can be set
    #
    skipTranslateZ = kwargs.get('skipTranslateZ', skipTranslate)

    if not skipTranslateZ:

        positionController[pymxs.runtime.Name('position_z')].controller.value = translation.z


def getEulerRotation(node):
    """
    Returns the euler angles from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: pymxs.runtime.EulerAngles
    """

    pass


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
    rotationController = transformController[pymxs.runtime.Name('rotation')].controller

    # Check if this is a rotation list
    #
    if pymxs.runtime.classOf(rotationController) == pymxs.runtime.Rotation_List:

        currentIndex = rotationController.getActive() - 1
        rotationController = rotationController[currentIndex].controller

    # Check if translateX can be set
    #
    skipRotate = kwargs.get('skipRotate', False)
    skipRotateX = kwargs.get('skipRotateX', skipRotate)

    if not skipRotateX:

        rotationController[pymxs.runtime.Name('position_x')].controller.value = eulerAngles.x

    # Check if translateY can be set
    #
    skipRotateY = kwargs.get('skipRotateY', skipRotate)

    if not skipRotateY:

        rotationController[pymxs.runtime.Name('position_y')].controller.value = eulerAngles.y

    # Check if translateZ can be set
    #
    skipRotateZ = kwargs.get('skipRotateZ', skipRotate)

    if not skipRotateZ:

        rotationController[pymxs.runtime.Name('position_z')].controller.value = eulerAngles.z


def getScale(node):
    """
    Returns the scale value from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: list[float, float, float]
    """

    pass


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
    scaleController = transformController[pymxs.runtime.Name('scale')].controller

    # Check if this is a rotation list
    #
    if pymxs.runtime.classOf(scaleController) == pymxs.runtime.Scale_List:

        currentIndex = scaleController.getActive() - 1
        scaleController = scaleController[currentIndex].controller

    # Check if translateX can be set
    #
    skipScale = kwargs.get('skipScale', False)
    skipScaleX = kwargs.get('skipScaleX', skipScale)

    if not skipScaleX:

        scaleController[pymxs.runtime.Name('scale_x')].controller.value = scale[0]

    # Check if translateY can be set
    #
    skipScaleY = kwargs.get('skipScaleY', skipScale)

    if not skipScaleY:

        scaleController[pymxs.runtime.Name('scale_y')].controller.value = scale[1]

    # Check if translateZ can be set
    #
    skipScaleZ = kwargs.get('skipScaleZ', skipScale)

    if not skipScaleZ:

        scaleController[pymxs.runtime.Name('scale_z')].controller.value = scale[2]
