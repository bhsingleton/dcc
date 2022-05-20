import pymxs
import re

from collections import deque, namedtuple
from ...python import stringutils
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__property_parser__ = re.compile(r'\.([a-zA-Z0-9_]+)')
__properties__ = {}  # Used with inspectClassProperties
__dependents__ = {}  # Used with findAssociatedSubAnim


BASE_TYPES = {
    'floatController': pymxs.runtime.floatController,
    'point3Controller': pymxs.runtime.point3Controller,
    'Matrix3Controller': pymxs.runtime.Matrix3Controller,
    'positionController': pymxs.runtime.positionController,
    'rotationController': pymxs.runtime.rotationController,
    'scaleController': pymxs.runtime.scaleController,
    'MorphController': pymxs.runtime.MorphController
}


CONSTRAINT_TYPES = {
    'Link_Constraint': pymxs.runtime.Link_Constraint,
    'Position_Constraint': pymxs.runtime.Position_Constraint,
    'Path_Constraint': pymxs.runtime.Path_Constraint,
    'Orientation_Constraint': pymxs.runtime.Orientation_Constraint,
    'LookAt_Constraint': pymxs.runtime.LookAt_Constraint,
    'Surface_position': pymxs.runtime.Surface_position,
    'Attachment': pymxs.runtime.Attachment
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
    'bezier_color': pymxs.runtime.bezier_color,
    'bezier_float': pymxs.runtime.bezier_float,
    'bezier_point2': pymxs.runtime.bezier_point2,
    'bezier_point3': pymxs.runtime.bezier_point3,
    'bezier_position': pymxs.runtime.bezier_position,
    'bezier_rotation': pymxs.runtime.bezier_rotation,
    'bezier_scale': pymxs.runtime.bezier_scale
}


LIST_TYPES = {
    'float_list': pymxs.runtime.float_list,
    'point3_list': pymxs.runtime.point3_list,
    'position_list': pymxs.runtime.position_list,
    'rotation_list': pymxs.runtime.rotation_list,
    'scale_list': pymxs.runtime.scale_list
}


SCRIPT_TYPES = {
    'float_script': pymxs.runtime.float_script,
    'transform_script': pymxs.runtime.transform_script,
    'point3_script': pymxs.runtime.point3_script,
    'position_script': pymxs.runtime.position_script,
    'rotation_script': pymxs.runtime.rotation_script,
    'scale_script': pymxs.runtime.scale_script,
}


WIRE_TYPES = {
    'Float_Wire': pymxs.runtime.Float_Wire,
    'Point3_Wire': pymxs.runtime.Point3_Wire,
    'Point4_Wire': pymxs.runtime.Point4_Wire,
    'Position_Wire': pymxs.runtime.Position_Wire,
    'Rotation_Wire': pymxs.runtime.Rotation_Wire,
    'Scale_Wire': pymxs.runtime.Scale_Wire
}


DUMMY_TYPES = {
    'position_ListDummyEntry': pymxs.runtime.position_ListDummyEntry,
    'rotation_ListDummyEntry': pymxs.runtime.rotation_ListDummyEntry,
    'scale_ListDummyEntry': pymxs.runtime.scale_ListDummyEntry
}


Dependent = namedtuple('Dependent', ('handle', 'subAnimName'))


def isConstraint(obj):
    """
    Evaluates if the supplied object is a constraint.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in CONSTRAINT_TYPES.values()


def isXYZController(obj):
    """
    Evaluates if the supplied object is a XYZ controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in XYZ_TYPES.values()


def isBezierController(obj):
    """
    Evaluates if the supplied object is a bezier controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in BEZIER_TYPES.values()


def isListController(obj):
    """
    Evaluates if the supplied object is a list controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in LIST_TYPES.values()


def isScriptController(obj):
    """
    Evaluates if the supplied object is a script controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in SCRIPT_TYPES.values()


def isWireParameter(obj):
    """
    Evaluates if the supplied object is a wire parameter.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in WIRE_TYPES.values()


def isDummyController(obj):
    """
    Evaluates if the supplied object is a dummy controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.classOf(obj) in DUMMY_TYPES.values()


def isValidController(obj):
    """
    Evaluates if the supplied object is a valid controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.superClassOf(obj) in BASE_TYPES.values()


def isValidSubAnim(obj):
    """
    Evaluates if the supplied object is a valid sub anim.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isKindOf(obj, pymxs.runtime.SubAnim)


def hasSubAnims(obj):
    """
    Evaluates if the supplied object is derived from an animatable.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isProperty(obj, 'numSubs')


def isValue(value):
    """
    Evaluates if the supplied max value is serializable.

    :type value: Any
    :rtype: bool
    """

    return pymxs.runtime.superClassOf(value) in (pymxs.runtime.Value, pymxs.runtime.Number)


def cacheSubAnim(subAnim):
    """
    Caches the supplied sub-anim to optimize getAssociatedSubAnim lookups.

    :type subAnim: pymxs.runtime.MXSWrapperBase
    :rtype: Union[Dependent, None]
    """

    # Get object handles
    #
    parentHandle = int(pymxs.runtime.getHandleByAnim(subAnim.parent))
    subAnimName = stringutils.slugify(subAnim.name, whitespace='_', illegal='_')

    handle = None

    if pymxs.runtime.isValidObj(subAnim.controller):

        handle = int(pymxs.runtime.getHandleByAnim(subAnim.controller))

    elif pymxs.runtime.isValidObj(subAnim.value):

        handle = int(pymxs.runtime.getHandleByAnim(subAnim.value))

    else:

        return

    # Add dependent to cache
    #
    dependent = Dependent(handle=parentHandle, subAnimName=subAnimName)
    __dependents__[handle] = dependent

    return dependent


def getCachedSubAnim(obj):
    """
    Returns the cached sub-anim associated with the given max object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: Union[pymxs.MXSWrapperBase, None]
    """

    # Check if parent was cached
    #
    handle = int(pymxs.runtime.getHandleByAnim(obj))
    dependent = __dependents__.get(handle, None)

    if dependent is None:

        return None

    # Verify max-object belongs to sub-anim
    #
    parent = pymxs.runtime.getAnimByHandle(dependent.handle)
    subAnim = pymxs.runtime.getSubAnim(parent, dependent.subAnimName)

    controller = getattr(subAnim, 'controller', None)
    value = getattr(subAnim, 'value', None)

    if controller == obj or value == obj:

        return subAnim

    else:

        del __dependents__[handle]
        return None


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

        # Get indexed sub-anim
        # Be sure to cache this to optimize reverse lookups
        #
        subAnim = pymxs.runtime.getSubAnim(obj, i)
        cacheSubAnim(subAnim)

        # Check if non-animated sub-anims should be skipped
        #
        if skipNonAnimated and not subAnim.isAnimated:

            continue

        # Check if null controllers should be skipped
        #
        if skipNullControllers and subAnim.controller is None:

            continue

        # Check if compound values should be skipped
        #
        if skipNonValues and not isValue(subAnim.value):

            continue

        else:

            yield subAnim


def getAssociatedSubAnim(obj):
    """
    Returns the sub-anim associated with the given max object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: Union[pymxs.MXSWrapperBase, None]
    """

    # Check if sub-anim was cached
    #
    subAnim = getCachedSubAnim(obj)

    if subAnim is not None:

        return subAnim

    # Evaluate which dependent the object is derived from
    # Dependents are returned from closest to furthest!
    #
    dependents = pymxs.runtime.refs.dependents(obj)

    for dependent in dependents:

        # Check if this is a valid object
        #
        if not pymxs.runtime.isValidObj(dependent):

            continue

        # Iterate through sub-anims
        #
        for subAnim in iterSubAnims(dependent):

            # Check if sub-anim contains object
            #
            if subAnim.controller == obj or subAnim.value == obj:

                cacheSubAnim(subAnim)
                return subAnim

            else:

                continue

    return None


def iterMaxKeys(controller):
    """
    Returns a generator that yields max keys from the supplied controller.
    This method is more of a catch-all for null key properties.

    :type controller: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Check if this is a valid controller
    #
    if not isValidController(controller):

        log.info('Max object: %s, is not a valid controller!' % controller)
        return

    # Check if controller has keys
    # Be aware that max can return none for empty arrays!
    #
    keys = getattr(controller, 'keys', None)

    if keys is None:

        log.info('Max object: %s, contains no key array!' % controller)
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


def iterControllers(obj):
    """
    Returns a generator that yields controllers from the supplied object.
    This method relies on the subAnim interface for parsing.

    :type obj: pymxs.MXSWrapperBase
    :rtype: iter
    """

    for subAnim in iterSubAnims(obj, skipNullControllers=True):

        yield subAnim.controller


def walkControllers(obj):
    """
    Returns a generator that yields all the controllers from the supplied node.

    :type obj: pymxs.runtime.MaxObject
    :rtype: iter
    """

    queue = deque([pymxs.runtime.getTMController(obj)])

    while len(queue):

        controller = queue.popleft()
        yield controller

        queue.extend(list(iterControllers(controller)))


def iterConstraints(obj):
    """
    Returns a generator that yields all constraint from the supplied node.
    Constraints do not share a common base class in Maxscript.
    So we have to define our own collection of constraint types...

    :type obj: pymxs.runtime.MaxObject
    :rtype: iter
    """

    for controller in walkControllers(obj):

        cls = pymxs.runtime.classOf(controller)
        clsName = str(cls)

        if clsName in CONSTRAINT_TYPES:

            yield controller

        else:

            continue


def findControllerByType(node, controllerType, all=False):
    """
    Finds a controller from the transform stack based on the supplied type.

    :type node: pymxs.runtime.Node
    :type controllerType: type
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


def isPropertyAnimatable(obj, name):
    """
    Evaluates if the supplied MXS object wrapper is animatable.
    Max will throw errors if the object isn't explicitly derived from MaxObject!

    :type obj: pymxs.MXSWrapperBase
    :type name: pymxs.runtime.Name
    :rtype: bool
    """

    try:

        return pymxs.runtime.isPropertyAnimatable(obj, name)

    except RuntimeError:

        return False


def getDefaultPropertyValue(cls, name):
    """
    Returns the default value for the specified property.

    :type cls: pymxs.MXSWrapperBase
    :type name: str
    :rtype: Any
    """

    try:

        return pymxs.runtime.DefaultParamInterface.getDefaultParamValue(cls, name, None)

    except SystemError:

        log.error('Error encountered while retrieving "%s::%s" default value!' % (cls, name))
        return None


def inspectClassProperties(className):
    """
    Inspects the supplied class names for writable properties.

    :type className: str
    :rtype: list[str]
    """

    # Check if class has already been inspected
    #
    properties = __properties__.get(className, None)

    if properties is not None:

        return properties

    # Concatenate class lookup pattern
    #
    pattern = '{className}.*'.format(className=className)

    stringStream = pymxs.runtime.StringStream('')
    pymxs.runtime.showClass(pattern, to=stringStream)

    # Iterate through string stream
    #
    properties = []
    pymxs.runtime.seek(stringStream, 1)

    while not pymxs.runtime.eof(stringStream):

        line = pymxs.runtime.readLine(stringStream)
        found = __property_parser__.findall(line)

        if len(found) == 1:

            properties.append(found[0])

    # Cache list for later use
    #
    __properties__[className] = properties
    return properties


def iterDynamicProperties(obj, skipAnimatable=False, skipNonValues=False):
    """
    Returns a generator that yields dynamic property name-value pairs from the supplied object.
    Unlike static properties, dynamic properties are created at runtime and cannot be found on the class definition!

    :type obj: pymxs.runtime.MaxObject
    :type skipAnimatable: bool
    :type skipNonValues: bool
    :rtype: iter
    """

    # Iterate through property names
    #
    properties = pymxs.runtime.getPropNames(obj)

    for name in properties:

        # Check if animatable properties should be skipped
        #
        isAnimatable = isPropertyAnimatable(obj, name)

        if skipAnimatable and isAnimatable:

            continue

        # Check if compound values should be skipped
        #
        key = stringutils.slugify(str(name), whitespace='_')
        value = pymxs.runtime.getProperty(obj, name)

        if skipNonValues and not isValue(value):

            continue

        else:

            yield key, value


def iterStaticProperties(obj, skipAnimatable=False, skipNonValues=False, skipDefaultValues=False):
    """
    Returns a generator that yields property name/value pairs from the supplied object.
    Unlike dynamic properties, static properties can be found on the class definition!

    :type obj: pymxs.runtime.MaxObject
    :type skipAnimatable: bool
    :type skipNonValues: bool
    :type skipDefaultValues: bool
    :rtype: iter
    """

    # Iterate through property names
    #
    cls = pymxs.runtime.classOf(obj)
    clsName = str(cls)

    properties = inspectClassProperties(clsName)

    for key in properties:

        # Check if property is accessible
        # The class inspector can yield private properties that are not accessible!
        #
        name = pymxs.runtime.Name(key)

        if not pymxs.runtime.isProperty(obj, name):

            continue

        # Check if animatable properties should be skipped
        #
        isAnimatable = isPropertyAnimatable(obj, name)

        if skipAnimatable and isAnimatable:

            continue

        # Check if non-values should be skipped
        #
        value = pymxs.runtime.getProperty(obj, name)

        if skipNonValues and not isValue(value):

            continue

        # Check if non-default values should be skipped
        #
        default = getDefaultPropertyValue(cls, key)

        if skipDefaultValues and (value == default):

            continue

        else:

            yield key, value
