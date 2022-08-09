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
