import pymxs

from . import propertyutils, controllerutils, transformutils
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def iterTargets(constraint):
    """
    Returns a generator that yields targets from the supplied constraint.

    :type constraint: pymxs.MXSWrapperBase
    :rtype: iter
    """

    numTargets = constraint.getNumTargets()

    for i in inclusiveRange(1, numTargets, 1):

        node = constraint.getNode(i)
        weight = constraint.getWeight(i)

        yield node, weight


def copyTargets(copyFrom, copyTo):
    """
    Copies the target-weight pairs to the specified constraint.

    :type copyFrom: pymxs.MXSWrapperBase
    :type copyTo: pymxs.MXSWrapperBase
    :rtype: None
    """

    for (node, weight) in iterTargets(copyFrom):

        copyTo.appendTarget(node, weight)


def rebuildPositionList(node, positionList):
    """
    Rebuilds the position-list on the supplied node.
    If the list controller has no constraints, or no relative constraints, then no changes are made.

    :type node: pymxs.MXSWrapperBase
    :type positionList: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Ensure frozen names
    #
    success = controllerutils.ensureFrozenNames(positionList)

    if not success:

        log.warning('Unable to rebuild "$%s.position" list controller!' % node.name)
        return False

    # Check if any sub-controllers are relative
    #
    matrix = transformutils.getMatrix(node)
    isRelative = any([getattr(subController, 'relative', False) for (name, subController, weight) in controllerutils.iterListController(positionList)])

    if not isRelative:

        # Freeze sub-controllers
        #
        frozenController = pymxs.runtime.getPropertyController(positionList, 'Frozen_Position')
        zeroController = pymxs.runtime.getPropertyController(positionList, 'Zero_Pos_XYZ')

        frozenController.value = matrix.translationPart
        zeroController.value = pymxs.runtime.Point3(0.0, 0.0, 0.0)

        log.debug('No relative constraints found on "$%s.position" controller!' % node.name)
        return True

    # Clear and rebuild list sub-controllers
    #
    positionListCopy = pymxs.runtime.copy(positionList)

    log.info('Rebuilding "$%s.position" controller!' % node.name)
    controllerutils.clearListController(positionList)

    for (i, (name, controller, weight)) in enumerate(controllerutils.iterListController(positionListCopy)):

        # Create sub-controller
        #
        index = i + 1
        controllerClass = pymxs.runtime.classOf(controller)

        log.info('Rebuilding "%s" controller @ "$%s.position.list[%s]"' % (controllerClass, node.name, index))

        if controllerutils.isConstraint(controller):

            # Add constraint sub-controller
            #
            subController = controllerClass()

            pymxs.runtime.setPropertyController(positionList, 'Available', subController)
            positionList.setName(index, name)

            # Copy constraint targets and properties
            #
            copyTargets(controller, subController)
            propertyutils.copyProperties(controller, subController)
            controllerutils.copySubAnims(controller, subController)

        else:

            # Copy controller
            #
            subController = pymxs.runtime.copy(controller)
            subController.value = matrix.translationPart if i == 0 else pymxs.runtime.Point3(0.0, 0.0, 0.0) if i == 1 else subController.value

            pymxs.runtime.setPropertyController(positionList, 'Available', subController)
            positionList.setName(index, name)

    # Copy weight sub-anims
    #
    controllerutils.copySubAnims(positionListCopy.weight, positionList.weight)

    # Reset active controller
    #
    listCount = positionList.getCount()
    positionList.setActive(listCount)

    return True


def rebuildRotationList(node, rotationList):
    """
    Rebuilds the rotation-list on the supplied node.
    If the list controller has no constraints, or no relative constraints, then no changes are made.

    :type node: pymxs.MXSWrapperBase
    :type rotationList: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Ensure frozen names
    #
    success = controllerutils.ensureFrozenNames(rotationList)

    if not success:

        log.warning('Unable to rebuild "$%s.rotation" list controller!' % node.name)
        return False

    # Check if any sub-controllers are relative
    #
    matrix = transformutils.getMatrix(node)
    isRelative = any([getattr(subController, 'relative', False) for (name, subController, weight) in controllerutils.iterListController(rotationList)])

    if not isRelative:

        # Freeze sub-controllers
        #
        frozenController = pymxs.runtime.getPropertyController(rotationList, 'Frozen_Rotation')
        zeroController = pymxs.runtime.getPropertyController(rotationList, 'Zero_Euler_XYZ')

        frozenController.value = matrix.rotationPart
        zeroController.value = pymxs.runtime.Quat(1)

        log.debug('No relative constraints found on "$%s.rotation" controller!' % node.name)
        return True

    # Clear and rebuild list sub-controllers
    #
    rotationListCopy = pymxs.runtime.copy(rotationList)

    log.info('Rebuilding "$%s.rotation" controller!' % node.name)
    controllerutils.clearListController(rotationList)

    for (i, (name, controller, weight)) in enumerate(controllerutils.iterListController(rotationListCopy)):

        # Create sub-controller
        #
        index = i + 1
        controllerClass = pymxs.runtime.classOf(controller)

        log.info('Rebuilding "%s" controller @ "$%s.rotation.list[%s]"' % (controllerClass, node.name, index))

        if controllerutils.isConstraint(controller):

            # Add constraint sub-controller
            #
            subController = controllerClass()

            pymxs.runtime.setPropertyController(rotationList, 'Available', subController)
            rotationList.setName(index, name)

            # Copy constraint targets and properties
            #
            copyTargets(controller, subController)
            propertyutils.copyProperties(controller, subController)
            controllerutils.copySubAnims(controller, subController)

        else:

            # Copy controller
            #
            subController = pymxs.runtime.copy(controller)
            subController.value = matrix.rotationPart if i == 0 else pymxs.runtime.Quat(1) if i == 1 else subController.value

            pymxs.runtime.setPropertyController(rotationList, 'Available', subController)
            rotationList.setName(index, name)

    # Copy weight sub-anims
    #
    controllerutils.copySubAnims(rotationListCopy.weight, rotationList.weight)

    # Reset active controller
    #
    listCount = rotationList.getCount()
    rotationList.setActive(listCount)

    return True


def resetInitialOffsets(node):
    """
    Resets the initial offsets on any constraints to the supplied node.
    Developer notes: As far as I'm aware there is no way to edit constraint offsets other than rebuilding the constraint.

    :type node: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Evaluate if node requires freezing
    #
    requiresFreezing = transformutils.requiresFreezing(node)

    if not requiresFreezing:

        return False

    # Decompose PRS controller
    #
    transformController = controllerutils.getPRSController(node)
    positionController, rotationController, scaleController = controllerutils.decomposePRSController(transformController)

    # Rebuild position list
    #
    positionList = controllerutils.ensureControllerByClass(positionController, pymxs.runtime.Position_List)
    rebuildPositionList(node, positionList)

    # Rebuild rotation list
    #
    rotationList = controllerutils.ensureControllerByClass(rotationController, pymxs.runtime.Rotation_List)
    rebuildRotationList(node, rotationList)

    return True
