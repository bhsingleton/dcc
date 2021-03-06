import pymxs
import re

from collections import deque
from . import propertyutils, attributeutils, wrapperutils
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__property_parser__ = re.compile(r'\.([a-zA-Z0-9_]+)')
__properties__ = {}  # Used with inspectClassProperties


SUPER_TYPES = dict(wrapperutils.iterClassesByPattern('*Controller', superOnly=True))
XYZ_TYPES = dict(wrapperutils.iterClassesByPattern('*XYZ'))
BEZIER_TYPES = dict(wrapperutils.iterClassesByPattern('bezier_*'))
LIST_TYPES = dict(wrapperutils.iterClassesByPattern('*_list'))
CONSTRAINT_TYPES = dict(wrapperutils.iterClassesByPattern('*_Constraint'))
SCRIPT_TYPES = dict(wrapperutils.iterClassesByPattern('*_script'))
WIRE_TYPES = dict(wrapperutils.iterClassesByPattern('*_Wire'))
DUMMY_TYPES = dict(wrapperutils.iterClassesByPattern('*_ListDummyEntry'))


def isBezierController(obj):
    """
    Evaluates if the supplied object is a bezier controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in BEZIER_TYPES.values()


def isXYZController(obj):
    """
    Evaluates if the supplied object is a XYZ controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in XYZ_TYPES.values()


def isListController(obj):
    """
    Evaluates if the supplied object is a list controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in LIST_TYPES.values()


def isConstraint(obj):
    """
    Evaluates if the supplied object is a constraint.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in CONSTRAINT_TYPES.values()


def isConstrained(obj):
    """
    Evaluates if the supplied object contains any constraints.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return any([isConstraint(controller) for controller in walkControllers(obj)])


def isWire(obj):
    """
    Evaluates if the supplied object is a wire parameter.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in WIRE_TYPES.values()


def isScriptController(obj):
    """
    Evaluates if the supplied object is a script controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in SCRIPT_TYPES.values()


def isDummyController(obj):
    """
    Evaluates if the supplied object is a dummy controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in DUMMY_TYPES.values()


def isFrozen(node):
    """
    Evaluates if the supplied node is frozen.

    :type node: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Evaluate if this is a valid node
    #
    if not pymxs.runtime.isValidNode(node):

        return False

    # Get PRS controller
    #
    transformController = getPRSController(node)

    if not pymxs.runtime.isKindOf(transformController, pymxs.runtime.PRS):

        return False

    # Evaluate if position/rotation lists exist
    #
    positionController, rotationController, scaleController = decomposePRSController(transformController)

    positionList = ensureControllerByClass(positionController, pymxs.runtime.Position_List)
    rotationList = ensureControllerByClass(rotationController, pymxs.runtime.Rotation_List)

    return positionList is not None and rotationList is not None


def ensureFrozenNames(controller):
    """
    Ensures the supplied controller has the correct frozen sub-anim names.
    Returns a boolean that determines if the operation was a success.

    :type controller: pymxs.MXSWrapperBase
    :rtype: bool
    """

    # Evaluate controller type
    #
    frozenSubAnims = []

    if pymxs.runtime.isKindOf(controller, pymxs.runtime.Position_List):

        frozenSubAnims = [(pymxs.runtime.Bezier_Position, 'Frozen Position'), (pymxs.runtime.Position_XYZ, 'Zero Pos XYZ')]

    elif pymxs.runtime.isKindOf(controller, pymxs.runtime.Rotation_List):

        frozenSubAnims = [(pymxs.runtime.Euler_XYZ, 'Frozen Rotation'), (pymxs.runtime.Euler_XYZ, 'Zero Euler XYZ')]

    elif pymxs.runtime.isKindOf(controller, pymxs.runtime.Scale_List):

        frozenSubAnims = [(pymxs.runtime.Bezier_Scale, 'Frozen Scale'), (pymxs.runtime.ScaleXYZ, 'Zero Scale XYZ')]

    else:

        return False

    # Check if there are enough sub-controllers
    #
    listCount = controller.getCount()

    if len(frozenSubAnims) > listCount:

        return False

    # Evaluate sub-anim names
    #
    for (i, (maxClass, name)) in enumerate(frozenSubAnims):

        # Get indexed sub-anim
        # Evaluate sub-controller class
        #
        index = i + 1
        subAnim = pymxs.runtime.getSubAnim(controller, index)

        if not pymxs.runtime.isKindOf(subAnim.controller, maxClass):

            return False

        # Check if names match
        #
        if subAnim.name != name:

            log.info('Renaming list sub-controller: "%s" > "%s"' % (subAnim.name, name))
            controller.setName(index, name)

    return True


def isValidSubAnim(obj):
    """
    Evaluates if the supplied object is a valid sub anim.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isKindOf(obj, pymxs.runtime.SubAnim)


def isValidController(obj):
    """
    Evaluates if the supplied obj is a valid controller.
    This method does not accept dummy controllers as valid since they are just placeholders!

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.superClassOf(obj) in SUPER_TYPES.values()


def isInstancedController(controller):
    """
    Evaluates if the supplied controller is instanced.

    :type controller: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.InstanceMgr.canMakeControllersUnique([], [controller])


def hasSubAnims(obj):
    """
    Evaluates if the supplied object is derived from an animatable.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isProperty(obj, 'numSubs')


def iterSubAnims(obj, skipNonAnimated=False, skipNullControllers=False, skipNonValues=False):
    """
    Returns a generator that yields sub-anims from the supplied object.
    Optional keywords can be used to skip particular sub-anims.

    :type obj: pymxs.MXSWrapperBase
    :type skipNonAnimated: bool
    :type skipNullControllers: bool
    :type skipNonValues: bool
    :rtype: iter
    """

    # Iterate through sub-anims
    #
    numSubs = getattr(obj, 'numSubs', 0)

    for i in inclusiveRange(1, numSubs, 1):

        # Check if non-animated sub-anims should be skipped
        #
        subAnim = pymxs.runtime.getSubAnim(obj, i)

        if skipNonAnimated and not subAnim.isAnimated:

            continue

        # Check if null controllers should be skipped
        #
        if skipNullControllers and subAnim.controller is None:

            continue

        # Check if compound values should be skipped
        #
        if skipNonValues and not propertyutils.isValue(subAnim.value):

            continue

        else:

            yield subAnim


def copySubAnims(copyFrom, copyTo):
    """
    Copies the sub-anim controller-value pairs to the specified object.

    :type copyFrom: pymxs.MXSWrapperBase
    :type copyTo: pymxs.MXSWrapperBase
    :rtype: None
    """

    # Iterate through sub-anims
    #
    subAnims = {subAnim.name: subAnim for subAnim in iterSubAnims(copyFrom)}

    for subAnim in iterSubAnims(copyTo):

        # Check if source sub-anim exists
        #
        otherSubAnim = subAnims.get(subAnim.name, None)

        if otherSubAnim is None:

            log.warning('Unable to copy "%s" sub-anim!' % subAnim.name)
            continue

        # Copy value and controller
        #
        subAnim.value = pymxs.runtime.copy(otherSubAnim.value)
        subAnim.controller = pymxs.runtime.copy(otherSubAnim.controller)


def iterMaxKeys(controller):
    """
    Returns a generator that yields max keys from the supplied controller.
    This method is more of a catch-all for null key properties.

    :type controller: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Check if this is a valid controller
    #
    if not pymxs.runtime.isController(controller):

        log.warning('iterMaxKeys() expects a valid controller (%s given)!' % pymxs.runtime.getClassName(controller))
        return

    # Check if controller has keys
    # Be aware that max can return none for empty arrays!
    #
    keys = getattr(controller, 'keys', None)

    if keys is None:

        log.warning('iterMaxKeys() expects an animatable controller (%s given)!' % pymxs.runtime.getClassName(controller))
        return

    # Iterate through keys
    # Be aware key arrays can return negative sizes which breaks for loops!
    # Also be aware that keys can be missing value properties!
    #
    numKeys = getattr(keys, 'count', 0)

    for i in range(numKeys):

        key = keys[i]

        if hasattr(key, 'value'):

            yield key

        else:

            continue


def iterAMaxKeys(controller):
    """
    Returns a generator that yields attachment keys from the supplied controller.

    :type controller: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Check if this is a valid controller
    #
    if not pymxs.runtime.isKindOf(controller, pymxs.runtime.Attachment):

        log.warning('iterAMaxKeys() expects an attachment controller (%s given)!' % pymxs.runtime.getClassName(controller))
        return

    # Iterate through keys
    #
    numKeys = controller.keys.count

    for i in inclusiveRange(1, numKeys, 1):

        yield pymxs.runtime.AttachCtrl.getKey(controller, i)


def iterControllers(obj, includeCustomAttributes=False):
    """
    Returns a generator that yields controllers from the supplied object.
    This method relies on the subAnim interface for parsing.

    :type obj: pymxs.MXSWrapperBase
    :type includeCustomAttributes: bool
    :rtype: iter
    """

    # Iterate through sub-anims
    #
    for subAnim in iterSubAnims(obj, skipNullControllers=True):

        yield subAnim.controller

    # Check if custom attributes should be yielded
    #
    if includeCustomAttributes:

        for attributeDefinition in attributeutils.iterDefinitions(obj, baseObject=False):

            for subAnim in iterSubAnims(attributeDefinition):

                yield subAnim.controller


def walkControllers(obj, includeCustomAttributes=False):
    """
    Returns a generator that yields all the sub-controllers from the supplied Max-object.

    :type obj: pymxs.MXSWrapperBase
    :type includeCustomAttributes: bool
    :rtype: iter
    """

    queue = deque([obj])

    while len(queue):

        controller = queue.popleft()
        yield controller

        queue.extendleft(list(iterControllers(controller, includeCustomAttributes=includeCustomAttributes)))


def walkTransformControllers(node, includeCustomAttributes=False):
    """
    Returns a generator that yields all the sub-controllers from the supplied node's transform controller..

    :type node: pymxs.MXSWrapperBase
    :type includeCustomAttributes: bool
    :rtype: iter
    """

    return walkControllers(pymxs.runtime.getTMController(node), includeCustomAttributes=includeCustomAttributes)


def iterConstraints(node):
    """
    Returns a generator that yields all the constraint from the supplied node.
    Constraints do not share a common base class in Maxscript.
    See CONSTRAINT_TYPES constant for a collection of contraint types.

    :type node: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Iterate through controllers
    #
    for controller in walkTransformControllers(node):

        # Evaluate controller class
        #
        controllerClass = pymxs.runtime.classOf(controller)

        if controllerClass in CONSTRAINT_TYPES.values():

            yield controller

        else:

            continue


def iterListController(controller):
    """
    Returns a generator that yields controller-weight pairs from the supplied list controller.

    :type controller: pymxs.MXSWrapperBase
    :rtype: iter
    """

    listCount = controller.getCount()
    weights = controller.weight

    for i in inclusiveRange(1, listCount, 1):

        subControllerName = controller.getName(i)
        subControllerWeight = pymxs.runtime.getSubAnim(weights, i).value
        subController = pymxs.runtime.getPropertyController(controller, subControllerName)

        yield subControllerName, subController, subControllerWeight


def ensureControllerByClass(obj, controllerClass):
    """
    Returns a controller derived from the specified class on the supplied object.
    This is useful when you know a controller should exist but is nested under something else.
    Such as a position_list under a spring controller.
    Otherwise, if the supplied is derived from the specified class then that object is returned.

    :type obj: pymxs.MXSWrapperBase
    :type controllerClass: pymxs.runtime.MaxClass
    :rtype: pymxs.MXSWrapperBase
    """

    # Redundancy check
    #
    if pymxs.runtime.isKindOf(obj, controllerClass):

        return obj

    else:

        return getControllerByClass(obj, controllerClass)


def getControllerByClass(obj, controllerClass, all=False):
    """
    Returns a controller derived from the specified class on the supplied object.
    An optional "all" keyword can be specified to return an array instead.

    :type obj: pymxs.MXSWrapperBase
    :type controllerClass: pymxs.runtime.MaxClass
    :type all: bool
    :rtype: Union[pymxs.MXSWrapperBase, List[pymxs.MXSWrapperBase]]
    """

    # Walk through transform stack
    #
    found = [x for x in walkControllers(obj) if pymxs.runtime.isKindOf(x, controllerClass)]
    numFound = len(found)

    if all:

        return found

    else:

        if numFound == 0:

            return None

        elif numFound == 1:

            return found[0]

        else:

            raise TypeError('getControllerByClass() expects a unique controller (%s found)!' % numFound)


def getPRSController(node):
    """
    Returns the PRS controller from the supplied node.

    :type node: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    return ensureControllerByClass(pymxs.runtime.getTMController(node), pymxs.runtime.PRS)


def decomposePRSController(controller):
    """
    Returns the position, rotation and scale sub-controllers from the supplied PRS controller.

    :type controller: pymxs.MXSWrapperBase
    :rtype: Tuple[pymxs.MXSWrapperBase, pymxs.MXSWrapperBase, pymxs.MXSWrapperBase]
    """

    positionController = pymxs.runtime.getPropertyController(controller, 'Position')
    rotationController = pymxs.runtime.getPropertyController(controller, 'Rotation')
    scaleController = pymxs.runtime.getPropertyController(controller, 'Scale')

    return positionController, rotationController, scaleController


def clearListController(controller):
    """
    Deletes all the controllers from the supplied list controller.
    
    :type controller: pymxs.MXSWrapperBase
    :rtype: None
    """
    
    # Redundancy check
    #
    if not isListController(controller):

        return

    # Iterate through controller list
    #
    listCount = controller.list.getCount()
    
    for i in range(listCount, 0, -1):
        
        controller.list.delete(i)
