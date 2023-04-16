import pymxs

from fnmatch import fnmatch
from . import propertyutils, controllerutils, transformutils, wrapperutils
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

    # Iterate through targets
    #
    numTargets = constraint.getNumTargets()

    for i in inclusiveRange(1, numTargets, 1):

        # Check if node is valid
        #
        node = constraint.getNode(i)
        weight = constraint.getWeight(i)

        if pymxs.runtime.isValidNode(node):

            yield node, weight

        else:

            continue


def copyTargets(copyFrom, copyTo):
    """
    Copies the target-weight pairs to the specified constraint.

    :type copyFrom: pymxs.MXSWrapperBase
    :type copyTo: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Iterate through targets
    #
    for (node, weight) in iterTargets(copyFrom):

        log.debug('Copying "%s" constraint target!' % node.name)
        copyTo.appendTarget(node, weight)


def clearTargets(constraint):
    """
    Removes all targets from the supplied constraint.

    :type constraint: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Iterate through targets
    #
    numTargets = constraint.getNumTargets()

    for i in inclusiveRange(numTargets, 1, -1):

        constraint.deleteTarget(i)


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

        log.warning(f'Unable to locate PRS controller from ${node.name}!' % node.name)
        return False

    # Get rotation list
    #
    positionController = controllerutils.decomposePRSController(prs)[0]
    positionList = controllerutils.findControllerByClass(positionController, pymxs.runtime.Position_List)
    success = controllerutils.ensureFrozenNames(positionList)

    if not success:

        log.warning(f'Unable to rebuild ${node.name}[#position].controller!')
        return False

    # Freeze rotation using current matrix
    #
    frozenPosition = transformutils.getMatrix(node).translationPart

    frozenController = pymxs.runtime.Bezier_Position()
    frozenController.value = frozenPosition
    pymxs.runtime.setPropertyController(prs, 'Position', frozenController)

    # Rebuild list sub-controllers
    #
    controller = pymxs.runtime.Position_List()
    pymxs.runtime.setPropertyController(prs, 'Position', controller)

    log.info(f'Rebuilding ${node.name}[#position].controller!')

    for (i, (subController, name, weight)) in enumerate(controllerutils.iterListController(positionList), start=1):

        # Evaluate sub-controller
        #
        if fnmatch(name, 'Frozen*'):  # Frozen Position

            controller.setName(i, name)

        elif fnmatch(name, 'Zero Pos ???'):  # Zero Pos XYZ

            subController.value = pymxs.runtime.Point3(0.0, 0.0, 0.0)
            pymxs.runtime.setPropertyController(controller, 'Available', subController)
            controller.setName(i, name)

        elif controllerutils.isConstraint(subController):  # Constraints

            # Create new constraint
            #
            constraintClass = pymxs.runtime.classOf(subController)
            log.info(f'Rebuilding "{constraintClass}" controller @ ${node.name}[#position].controller[{i}]')

            constraint = constraintClass()
            pymxs.runtime.setPropertyController(controller, 'Available', constraint)
            controller.setName(i, name)

            # Copy constraint targets and properties
            #
            copyTargets(subController, constraint)
            propertyutils.copyProperties(subController, constraint)
            controllerutils.copySubAnims(subController, constraint)

        else:  # Default

            pymxs.runtime.setPropertyController(controller, 'Available', subController)
            controller.setName(i, name)

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

        log.warning(f'Unable to locate PRS controller from ${node.name}!')
        return False

    # Get rotation list
    #
    positionController, rotationController, scaleController = controllerutils.decomposePRSController(prs)
    rotationList = controllerutils.findControllerByClass(rotationController, pymxs.runtime.Rotation_List)
    success = controllerutils.ensureFrozenNames(rotationList)

    if not success:

        log.warning(f'Unable to rebuild ${node.name}[#rotation].controller!')
        return False

    # Evaluate if node utilizes pre-rotations
    # This will affect which value we use to freeze the rotation-list
    #
    pathConstraint = controllerutils.findControllerByClass(rotationList, pymxs.runtime.Path_Constraint)
    attachmentConstraint = controllerutils.findControllerByClass(rotationList, pymxs.runtime.Attachment)

    frozenRotation = transformutils.getMatrix(node).rotationPart

    if pymxs.runtime.isValidObj(pathConstraint):

        follow = pathConstraint.follow
        frozenRotation = rotationList.value if follow else frozenRotation

    elif pymxs.runtime.isValidObj(attachmentConstraint):

        align = attachmentConstraint.align
        frozenRotation = rotationList.value if align else frozenRotation

    else:

        pass

    # Freeze rotation
    #
    frozenController = pymxs.runtime.Euler_XYZ()
    frozenController.value = frozenRotation
    pymxs.runtime.setPropertyController(prs, 'Rotation', frozenController)

    # Rebuild list sub-controllers
    #
    controller = pymxs.runtime.Rotation_List()
    pymxs.runtime.setPropertyController(prs, 'Rotation', controller)

    log.info(f'Rebuilding ${node.name}[#rotation].controller!')

    for (i, (subController, name, weight)) in enumerate(controllerutils.iterListController(rotationList), start=1):

        # Evaluate sub-controller
        #
        if fnmatch(name, 'Frozen*'):  # Frozen Rotation

            controller.setName(i, name)

        elif fnmatch(name, 'Zero Euler ???'):  # Zero Euler XYZ

            subController.value = pymxs.runtime.Quat(1)
            pymxs.runtime.setPropertyController(controller, 'Available', subController)
            controller.setName(i, name)

        elif controllerutils.isConstraint(subController):  # Constraints

            # Create new constraint
            #
            constraintClass = pymxs.runtime.classOf(subController)
            log.info(f'Rebuilding "{constraintClass}" controller @ "${node.name}[#rotation].controller[{i}]"')

            constraint = constraintClass()
            pymxs.runtime.setPropertyController(controller, 'Available', constraint)
            controller.setName(i, name)

            # Copy constraint targets and properties
            #
            copyTargets(subController, constraint)
            propertyutils.copyProperties(subController, constraint)
            controllerutils.copySubAnims(subController, constraint)

        else:  # Default

            pymxs.runtime.setPropertyController(controller, 'Available', subController)
            controller.setName(i, name)

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

    # Decompose PRS controller
    #
    transformController = controllerutils.getPRSController(node)
    positionController, rotationController, scaleController = controllerutils.decomposePRSController(transformController)

    # Rebuild position list
    #
    startMatrix = transformutils.getMatrix(node)

    if wrapperutils.isKindOf(positionController, pymxs.runtime.Position_List):

        rebuildPositionList(node)

    elif wrapperutils.isKindOf(positionController, pymxs.runtime.Position_XYZ):

        transformutils.freezeTranslation(node)

    else:

        pass

    # Rebuild rotation list
    #
    if wrapperutils.isKindOf(rotationController, pymxs.runtime.Rotation_List):

        rebuildRotationList(node)

    elif wrapperutils.isKindOf(rotationController, pymxs.runtime.Euler_XYZ):

        transformutils.freezeRotation(node)

    else:

        pass

    # Check for any significant matrix changes
    #
    endMatrix = transformutils.getMatrix(node)

    if not transformutils.isClose(startMatrix, endMatrix, tolerance=0.01):

        log.error(f'{startMatrix} != {endMatrix}')
        raise RuntimeError(f'resetInitialOffsets() unable to reset ${node.name} initial offset!')

    return True
