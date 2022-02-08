import pymxs

from collections import deque

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


BASE_TYPES = {
    'Matrix3Controller': pymxs.runtime.Matrix3Controller,
    'PositionController': pymxs.runtime.PositionController,
    'RotationController': pymxs.runtime.RotationController,
    'ScaleController': pymxs.runtime.ScaleController,
    'FloatController': pymxs.runtime.FloatController,
}


CONSTRAINT_TYPES = {
    'Link_Constraint': pymxs.runtime.Link_Constraint,
    'Position_Constraint': pymxs.runtime.Position_Constraint,
    'Path_Constraint': pymxs.runtime.Path_Constraint,
    'Orientation_Constraint': pymxs.runtime.Orientation_Constraint,
    'LookAt_Constraint': pymxs.runtime.LookAt_Constraint
}


XYZ_TYPES = {
    'Color_RGB': pymxs.runtime.Color_RGB,
    'Euler_XYZ': pymxs.runtime.Euler_XYZ,
    'Local_Euler_XYZ': pymxs.runtime.Local_Euler_XYZ,
    'Point3_XYZ': pymxs.runtime.Point3_XYZ,
    'Position_XYZ': pymxs.runtime.Position_XYZ,
    'ScaleXYZ': pymxs.runtime.ScaleXYZ
}


BEZIER_TYPES = {
    'Bezier_Color': pymxs.runtime.Bezier_Color,
    'Bezier_Float': pymxs.runtime.Bezier_Float,
    'Bezier_Point2': pymxs.runtime.Bezier_Point2,
    'Bezier_Point3': pymxs.runtime.Bezier_Point3,
    'Bezier_Position': pymxs.runtime.Bezier_Position,
    'Bezier_Rotation': pymxs.runtime.Bezier_Rotation,
    'Bezier_Scale': pymxs.runtime.Bezier_Scale
}


LIST_TYPES = {
    'Float_List': pymxs.runtime.Float_List,
    'Point3_List': pymxs.runtime.Point3_List,
    'Position_List': pymxs.runtime.Position_List,
    'Rotation_List': pymxs.runtime.Rotation_List,
    'Scale_List': pymxs.runtime.Scale_List
}


def isConstraint(obj):
    """
    Evaluates if the supplied object is a constraint.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in CONSTRAINT_TYPES.values()


def isXYZController(obj):
    """
    Evaluates if the supplied object is a XYZ controller.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in XYZ_TYPES.values()


def isBezierController(obj):
    """
    Evaluates if the supplied object is a bezier controller.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in BEZIER_TYPES.values()


def isListController(obj):
    """
    Evaluates if the supplied object is a list controller.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in LIST_TYPES.values()


def isValidController(obj):
    """
    Evaluates if the supplied object is a valid controller.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.superClassOf(obj) in BASE_TYPES.values()


def iterSubAnims(obj, skipNonAnimated=False, skipNullControllers=False):
    """
    Returns a generator that yields sub anims from the supplied object.
    Optional keywords can be used to skip particular sub-anims.

    :type obj: pymxs.runtime.MXSWrapperBase
    :type skipNonAnimated: bool
    :type skipNullControllers: bool
    :rtype: iter
    """

    # Iterate through sub anims
    #
    for i in range(obj.numSubs):

        # Check if non-animated sub-anims should be skipped
        #
        subAnim = pymxs.runtime.getSubAnim(obj, i + 1)

        if skipNonAnimated and not subAnim.isAnimated:

            continue

        # Check if null controllers should be skipped
        #
        if skipNullControllers and subAnim.controller is None:

            continue

        else:

            yield subAnim


def iterMaxKeys(obj):
    """
    Returns a generator that yields max keys from the supplied controller.
    This method is more a catch all for null key properties.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: iter
    """

    # Check if this is a valid controller
    #
    if not isValidController(obj):

        log.info('Max object: %s, is not a valid controller!' % obj)
        return

    # Check if controller has keys
    # Be aware that max can return none for empty arrays!
    #
    keys = obj.keys

    if keys is None:

        log.info('Max object: %s, contains no key array!' % obj)
        return

    # Iterate through keys
    # Be aware key arrays can return negative sizes which breaks for loops!
    # Also be aware that keys can be missing value properties!
    #
    numKeys = keys.count

    for i in range(numKeys):

        key = keys[i]

        if pymxs.runtime.isProperty(key, pymxs.runtime.Name('value')):

            yield key

        else:

            continue


def iterControllers(obj):
    """
    Returns a generator that yields controllers from the supplied object.
    This method relies on the subAnim interface for parsing.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: iter
    """

    for subAnim in iterSubAnims(obj, skipNullControllers=True):

        yield subAnim.controller


def walkControllers(node):
    """
    Returns a generator that yields all of the controllers from the supplied node.

    :type node: pymxs.runtime.Node
    :rtype: iter
    """

    queue = deque([pymxs.runtime.getTMController(node)])

    while len(queue):

        controller = queue.popleft()
        yield controller

        queue.extend(list(iterControllers(controller)))


def iterConstraints(node):
    """
    Returns a generator that yields all constraint from the supplied node.
    Constraints do not share a common base class in Maxscript.
    So we have to define our own collection of constraint types...

    :type node: pymxs.runtime.Node
    :rtype: iter
    """

    for controller in walkControllers(node):

        if controller in CONSTRAINT_TYPES:

            yield controller

        else:

            continue


def findControllerByType(node, controllerType, all=False):
    """
    Finds a controller from the transform stack based on the supplied type.

    :type node: pymxs.runtime.Node
    :type controllerType: pymxs.runtime.Control
    :type all: bool
    :rtype: pymxs.runtime.Control
    """

    # Walk through transform stack
    #
    found = [x for x in walkControllers(node) if pymxs.runtime.classOf(x) == controllerType]
    numFound = len(found)

    if all:

        return found

    else:

        if numFound == 0:

            return None

        elif numFound == 1:

            return found[0]

        else:

            raise TypeError('findControllerByType() multiple controllers found!')
