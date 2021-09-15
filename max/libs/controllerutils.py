import pymxs

from collections import deque

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


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


def findControllerByType(node, controllerType):
    """
    Finds a controller from the controller stack based on the requested type.
    If multiple controllers are found then a type error is raised!

    :type node: pymxs.runtime.Node
    :type controllerType: pymxs.runtime.MXSWrapperBase
    :rtype: pymxs.runtime.MXSWrapperBase
    """

    found = [x for x in walkControllers(node) if pymxs.runtime.classOf(x) == controllerType]
    numFound = len(found)

    if numFound == 0:

        return None

    elif numFound == 1:

        return found[0]

    else:

        raise TypeError('findControllerByType() multiple controllers found!')
