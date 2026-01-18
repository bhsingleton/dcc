import pymxs

from . import controllerutils, transformutils, modifierutils, attributeutils, wrapperutils
from ...generators.inclusiverange import inclusiveRange

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
    transformController = pymxs.runtime.getTMController(node)

    if not wrapperutils.isKindOf(transformController, (pymxs.runtime.PRS, pymxs.runtime.LookAt)):

        log.info(f'Skipping non PRS controller on {node.name} node!')
        return

    # Evaluate PRS sub-controllers
    #
    insertAt = pymxs.runtime.animationRange.start

    for subController in controllerutils.iterControllers(transformController):

        # Check if this is a list controller
        #
        if controllerutils.isListController(subController):

            subController = controllerutils.getActiveController(subController)

        # Check if sub-controller has been keyed
        #
        numKeys = subController.keys.count

        if numKeys == 0:

            log.info('Keying "%s" object!' % pymxs.runtime.exprForMaxObject(subController))
            pymxs.runtime.addNewKey(subController, insertAt)

    # Evaluate empty modifier
    #
    empty = modifierutils.getModifierByClass(node, pymxs.runtime.EmptyModifier)

    for definition in attributeutils.iterDefinitions(empty):

        # Iterate through sub-anims
        #
        for subAnim in controllerutils.iterSubAnims(definition, skipNullControllers=True):

            # Check if sub-controller has been keyed
            #
            subController = subAnim.controller
            numKeys = subController.keys.count

            if numKeys == 0:

                log.info('Keying "%s" object!' % pymxs.runtime.exprForMaxObject(subController))
                pymxs.runtime.addNewKey(subController, insertAt)

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
    log.info(f'Caching animation range: {startFrame} > {endFrame}')

    for frame in inclusiveRange(startFrame, endFrame, 1):

        with pymxs.attime(frame):

            cache[frame] = pymxs.runtime.copy(node.transform)

    return cache


def assumeCache(node, cache):
    """
    Applies the supplied transform cache to the specified node.

    :type node: pymxs.MXSWrapperBase
    :type cache: Dict[int, pymxs.runtime.Matrix3]
    :rtype: None
    """

    # Decompose PRS controller
    #
    transformController = controllerutils.getPRSController(node)
    pymxs.runtime.deleteKeys(transformController, pymxs.runtime.Name('allKeys'))

    positionController, rotationController, scaleController = controllerutils.decomposePRSController(transformController)
    activePositionController = controllerutils.getActiveController(positionController)
    activeRotationController = controllerutils.getActiveController(rotationController)

    with pymxs.animate(True):

        # Iterate through frame cache
        #
        for (frame, worldMatrix) in cache.items():

            pymxs.runtime.addNewKey(activePositionController, frame)
            pymxs.runtime.addNewKey(activeRotationController, frame)
            pymxs.runtime.addNewKey(scaleController, frame)

            with pymxs.attime(frame):

                node.transform = worldMatrix


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
    log.info(f'Baking ${node.name}.transform')
    transformCache = cacheTransforms(node, startFrame=startFrame, endFrame=endFrame)

    transformController = controllerutils.findControllerByClass(transformController, pymxs.runtime.PRS)
    positionController, rotationController, scaleController = controllerutils.decomposePRSController(transformController)

    # Inspect position controller
    #
    if controllerutils.isListController(positionController):

        # Evaluate active controller
        #
        subControllers = [subController for (subController, name, weight) in controllerutils.iterListController(positionController)]
        indices = [i for (i, subController) in enumerate(subControllers, start=1) if controllerutils.isConstraint(subController)]

        positionController.active = 2

        for index in reversed(indices):

            log.info(f'Deleting ${node.name}.position.controller[{index}] sub-controller.')
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
        subControllers = [subController for (subController, name, weight) in controllerutils.iterListController(rotationController)]
        indices = [i for (i, subController) in enumerate(subControllers, start=1) if controllerutils.isConstraint(subController)]

        rotationController.active = 2

        for index in reversed(indices):

            log.info(f'Deleting ${node.name}.rotation.controller[{index}] sub-controller.')
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
