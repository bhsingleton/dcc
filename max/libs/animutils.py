import pymxs

from . import controllerutils, transformutils, modifierutils, attributeutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isNonDefault(controller):
    """
    Evaluates if the supplied controller has a non-default value.

    :type controller: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Evaluate controller's super class
    #
    if pymxs.runtime.isKindOf(controller, pymxs.runtime.PositionController):

        return not transformutils.isClose(controller.value, pymxs.runtime.Point3(0.0, 0.0, 0.0))

    elif pymxs.runtime.isKindOf(controller, pymxs.runtime.RotationController):

        return not transformutils.isClose(controller.value, pymxs.runtime.Quat(1))

    elif pymxs.runtime.isKindOf(controller, pymxs.runtime.ScaleController):

        return not transformutils.isClose(controller.value, pymxs.runtime.Point3(1.0, 1.0, 1.0))

    elif pymxs.runtime.isKindOf(controller, pymxs.runtime.FloatController):

        return not transformutils.isClose(controller.value, 0.0)

    else:

        return controller.value is not None


def ensureKeyed(node):
    """
    Ensures that the supplied node's non-default values are keyed.

    :type node: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Get transform controller
    #
    prs = controllerutils.getPRSController(node)

    if not pymxs.runtime.isKindOf(prs, pymxs.runtime.PRS):

        return

    # Evaluate PRS sub-controllers
    #
    subControllers = controllerutils.decomposePRSController(prs)

    for subController in subControllers:

        # Check if this is a list controller
        #
        if controllerutils.isListController(subController):

            subController = controllerutils.getActiveController(subController)

        # Check if sub-controller is non-default
        #
        numKeys = subController.keys.count

        if numKeys == 0 and isNonDefault(subController):

            log.info('Keying "%s" object!' % pymxs.runtime.exprForMaxObject(subController))
            pymxs.runtime.addNewKey(subController, pymxs.runtime.animationRange.start)

    # Evaluate empty modifier
    #
    empty = modifierutils.getModifierByClass(node, pymxs.runtime.EmptyModifier)

    for definition in attributeutils.iterDefinitions(empty):

        # Iterate through sub-anims
        #
        for subAnim in controllerutils.iterSubAnims(definition, skipNullControllers=True):

            subController = subAnim.controller

            if isNonDefault(subController):

                log.info('Keying "%s" object!' % pymxs.runtime.exprForMaxObject(subController))
                pymxs.runtime.addNewKey(subController, pymxs.runtime.animationRange.start)

            else:

                continue


def cacheTransforms(node, startFrame=None, endFrame=None):
    """
    Caches all transform data over the specified time range.

    :type node: pymxs.MXSWrapperBase
    :type startFrame: Union[int, None]
    :type endFrame: Union[int, None]
    :rtype: Dict[int, pymxs.runtime.Matrix3]
    """

    # Inspect start frame
    #
    if startFrame is None:

        startFrame = int(pymxs.runtime.AnimationRange.start)

    # Inspect end frame
    #
    if endFrame is None:

        endFrame = int(pymxs.runtime.AnimationRange.end)

    # Iterate through time range
    #
    cache = {}

    for i in range(startFrame, endFrame + 1, 1):

        with pymxs.attime(i):

            cache[i] = pymxs.runtime.copy(node.transform)

    return cache


def assumeCache(node, cache):
    """
    Applies the supplied transform cache to the specified node.

    :type node: pymxs.MXSWrapperBase
    :type cache: Dict[int, pymxs.runtime.Matrix3]
    :rtype: None
    """

    with pymxs.animate(True):

        for (time, transform) in cache.items():

            with pymxs.attime(time):

                node.transform = transform


def bakeConstraints(node, startFrame=None, endFrame=None):
    """
    Bakes any constraints on the supplied node.

    :type node: pymxs.MXSWrapperBase
    :type startFrame: Union[int, None]
    :type endFrame: Union[int, None]
    :rtype: None
    """

    # Check if node is valid
    #
    if not pymxs.runtime.isValidNode(node):

        raise TypeError('bakeConstraints() expects a valid node!')

    # Check if node has been constrained
    #
    transformController = pymxs.runtime.getTMController(node)

    if not controllerutils.isConstrained(transformController):

        log.debug('Cannot find any constraints on $%s node!' % node.name)
        return

    # Cache and decompose PRS controller
    #
    log.info('Baking $%s.transform' % node.name)
    transformCache = cacheTransforms(node, startFrame=startFrame, endFrame=endFrame)

    transformController = controllerutils.findControllerByClass(transformController, pymxs.runtime.PRS)
    positionController, rotationController, scaleController = controllerutils.decomposePRSController(transformController)

    # Inspect position controller
    #
    if controllerutils.isListController(positionController):

        # Evaluate active controller
        #
        subControllers = [subController for (subController, name, weight) in controllerutils.iterListController(positionController)]
        indices = [(i + 1) for (i, subController) in enumerate(subControllers) if controllerutils.isConstraint(subController)]

        for index in reversed(indices):

            log.info('Deleting $%s.position.controller[%s] sub-controller.' % (node.name, index))
            positionController.delete(index)

    elif controllerutils.isConstraint(positionController):

        # Revert property controller
        #
        log.info('Resetting $%s.position controller.' % node.name)

        positionXYZ = pymxs.runtime.Position_XYZ()
        pymxs.runtime.setPropertyController(transformController, 'Position', positionXYZ)

    else:

        pass

    # Inspect rotation controller
    #
    if controllerutils.isListController(rotationController):

        # Evaluate active controller
        #
        subControllers = [subController for (subController, name, weight) in controllerutils.iterListController(positionController)]
        indices = [i + 1 for (i, subController) in enumerate(subControllers) if controllerutils.isConstraint(subController)]

        for index in reversed(indices):

            log.info('Deleting $%s.rotation.controller[%s] sub-controller.' % (node.name, index))
            rotationController.delete(index)

    elif controllerutils.isConstraint(rotationController):

        # Revert property controller
        #
        log.info('Resetting $%s.rotation controller.' % node.name)

        eulerXYZ = pymxs.runtime.Euler_XYZ()
        pymxs.runtime.setPropertyController(transformController, 'Rotation', eulerXYZ)

    else:

        pass

    # Assume transform cache
    #
    assumeCache(node, transformCache)
