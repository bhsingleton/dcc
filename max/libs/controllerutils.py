import pymxs

from collections import deque

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


CONSTRAINT_TYPES = (
    pymxs.runtime.Link_Constraint,
    pymxs.runtime.Position_Constraint,
    pymxs.runtime.Path_Constraint,
    pymxs.runtime.Orientation_Constraint,
    pymxs.runtime.LookAt_Constraint
)


XYZ_TYPES = (
    pymxs.runtime.Color_RGB,
    pymxs.runtime.Euler_XYZ,
    pymxs.runtime.Local_Euler_XYZ,
    pymxs.runtime.Point3_XYZ,
    pymxs.runtime.Position_XYZ,
    pymxs.runtime.ScaleXYZ
)


BEZIER_TYPES = (
    pymxs.runtime.Bezier_Color,
    pymxs.runtime.Bezier_Float,
    pymxs.runtime.Bezier_Point2,
    pymxs.runtime.Bezier_Point3,
    pymxs.runtime.Bezier_Position,
    pymxs.runtime.Bezier_Rotation,
    pymxs.runtime.Bezier_Scale
)


LIST_TYPES = (
    pymxs.runtime.Float_List,
    pymxs.runtime.Point3_List,
    pymxs.runtime.Position_List,
    pymxs.runtime.Rotation_List,
    pymxs.runtime.Scale_List
)


def isConstraint(obj):
    """
    Evaluates if the supplied object is a constraint.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in CONSTRAINT_TYPES


def isXYZController(obj):
    """
    Evaluates if the supplied object is a XYZ controller.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in XYZ_TYPES


def isBezierController(obj):
    """
    Evaluates if the supplied object is a bezier controller.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in BEZIER_TYPES


def isListController(obj):
    """
    Evaluates if the supplied object is a list controller.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in LIST_TYPES


def iterControllers(obj):
    """
    Returns a generator that yields controllers from the supplied object.
    This method relies on the subAnim interface for parsing.

    :type obj: pymxs.runtime.MXSWrapperBase
    :rtype: iter
    """

    subAnimNames = pymxs.runtime.getSubAnimNames(obj)

    for subAnimName in subAnimNames:

        subAnim = obj[subAnimName]
        controller = subAnim.controller

        if controller is not None:

            yield controller

        else:

            continue


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
