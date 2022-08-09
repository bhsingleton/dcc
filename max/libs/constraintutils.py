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

        log.debug('Copying "%s" constraint target!' % node.name)
        copyTo.appendTarget(node, weight)


def rebuildPositionList(node):
    """
    Rebuilds the position-list on the supplied node.
    If the list controller has no constraints, or no relative constraints, then no changes are made.

    :type node: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Get transform controller
    #
    prs = controllerutils.getPRSController(node)

    if not pymxs.runtime.isKindOf(prs, pymxs.runtime.PRS):

        log.warning('Unable to locate PRS controller from "%s" node!' % node.name)
        return False

    # Get rotation list
    #
    rotationController = controllerutils.decomposePRSController(prs)[0]
    positionList = controllerutils.ensureControllerByClass(rotationController, pymxs.runtime.Position_List)
    success = controllerutils.ensureFrozenNames(positionList)

    if not success:

        log.warning('Unable to rebuild "$%s.position" list controller!' % node.name)
        return False

    # Freeze rotation using current matrix
    #
    matrix = transformutils.getMatrix(node)

    frozenController = pymxs.runtime.Bezier_Position()
    frozenController.value = matrix.translationPart
    pymxs.runtime.setPropertyController(prs, 'Position', frozenController)

    # Rebuild list sub-controllers
    #
    controller = pymxs.runtime.Position_List()
    pymxs.runtime.setPropertyController(prs, 'Position', controller)

    log.info('Resetting "$%s.position" list controller!' % node.name)

    for (i, (subController, name, weight)) in enumerate(controllerutils.iterListController(positionList)):

        # Evaluate sub-controller
        #
        index = i + 1

        if i == 0:  # Frozen_Position

            controller.setName(index, name)

        elif i == 1:  # Zero_Pos_XYZ

            subController.value = pymxs.runtime.Point3(0.0, 0.0, 0.0)
            pymxs.runtime.setPropertyController(controller, 'Available', subController)
            controller.setName(index, name)

        elif controllerutils.isConstraint(subController):  # Constraints

            # Create new constraint
            #
            constraintClass = pymxs.runtime.classOf(subController)
            log.info('Rebuilding "%s" controller @ "$%s.position.list[%s]"' % (constraintClass, node.name, index))

            constraint = constraintClass()
            pymxs.runtime.setPropertyController(controller, 'Available', constraint)
            controller.setName(index, name)

            # Copy constraint targets and properties
            #
            copyTargets(subController, constraint)
            propertyutils.copyProperties(subController, constraint)
            controllerutils.copySubAnims(subController, constraint)

        else:  # Default

            pymxs.runtime.setPropertyController(controller, 'Available', subController)
            controller.setName(index, name)

    # Copy weight sub-anims
    # Update active sub-controller
    #
    controllerutils.copySubAnims(positionList.weight, controller.weight)
    controller.setActive(positionList.getActive())

    return True


def rebuildRotationList(node):
    """
    Rebuilds the rotation-list on the supplied node.
    If the list controller has no constraints, or no relative constraints, then no changes are made.

    :type node: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Get transform controller
    #
    prs = controllerutils.getPRSController(node)

    if not pymxs.runtime.isKindOf(prs, pymxs.runtime.PRS):

        log.warning('Unable to locate PRS controller from "%s" node!' % node.name)
        return False

    # Get rotation list
    #
    rotationController = controllerutils.decomposePRSController(prs)[1]
    rotationList = controllerutils.ensureControllerByClass(rotationController, pymxs.runtime.Rotation_List)
    success = controllerutils.ensureFrozenNames(rotationList)

    if not success:

        log.warning('Unable to rebuild "$%s.rotation" list controller!' % node.name)
        return False

    # Freeze rotation using current matrix
    #
    matrix = transformutils.getMatrix(node)

    frozenController = pymxs.runtime.Euler_XYZ()
    frozenController.value = matrix.rotationPart
    pymxs.runtime.setPropertyController(prs, 'Rotation', frozenController)

    # Rebuild list sub-controllers
    #
    controller = pymxs.runtime.Rotation_List()
    pymxs.runtime.setPropertyController(prs, 'Rotation', controller)

    log.info('Resetting "$%s.rotation" list controller!' % node.name)

    for (i, (subController, name, weight)) in enumerate(controllerutils.iterListController(rotationList)):

        # Evaluate sub-controller
        #
        index = i + 1

        if i == 0:  # Frozen_Rotation

            controller.setName(index, name)

        elif i == 1:  # Zero_Euler_XYZ

            subController.value = pymxs.runtime.Quat(1)
            pymxs.runtime.setPropertyController(controller, 'Available', subController)
            controller.setName(index, name)

        elif controllerutils.isConstraint(subController):  # Constraints

            # Create new constraint
            #
            constraintClass = pymxs.runtime.classOf(subController)
            log.info('Rebuilding "%s" controller @ "$%s.rotation.list[%s]"' % (constraintClass, node.name, index))

            constraint = constraintClass()
            pymxs.runtime.setPropertyController(controller, 'Available', constraint)
            controller.setName(index, name)

            # Copy constraint targets and properties
            #
            copyTargets(subController, constraint)
            propertyutils.copyProperties(subController, constraint)
            controllerutils.copySubAnims(subController, constraint)

        else:  # Default

            pymxs.runtime.setPropertyController(controller, 'Available', subController)
            controller.setName(index, name)

    # Copy weight sub-anims
    # Update active sub-controller
    #
    controllerutils.copySubAnims(rotationList.weight, controller.weight)
    controller.setActive(rotationList.getActive())

    return True


def resetInitialOffsets(node):
    """
    Resets the initial offsets on any constraints to the supplied node.
    Developer notes: As far as I'm aware there is no way to edit constraint offsets other than rebuilding the constraint...

    :type node: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Evaluate if node requires freezing
    #
    requiresFreezing = transformutils.requiresFreezing(node)

    if not requiresFreezing:

        return False

    # Rebuild PRS list controllers
    #
    rebuildPositionList(node)
    rebuildRotationList(node)

    return True
