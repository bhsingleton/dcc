import pymxs
import re

from collections import deque

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


BASE_TYPES = {
    'Matrix3Controller': pymxs.runtime.Matrix3Controller,
    'positionController': pymxs.runtime.positionController,
    'rotationController': pymxs.runtime.rotationController,
    'scaleController': pymxs.runtime.scaleController,
    'floatController': pymxs.runtime.floatController,
}


CONSTRAINT_TYPES = {
    'Link_Constraint': pymxs.runtime.Link_Constraint,
    'Position_Constraint': pymxs.runtime.Position_Constraint,
    'Path_Constraint': pymxs.runtime.Path_Constraint,
    'Orientation_Constraint': pymxs.runtime.Orientation_Constraint,
    'LookAt_Constraint': pymxs.runtime.LookAt_Constraint
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


PROPERTY_PARSER = re.compile(r'\.{1}([a-zA-Z0-9_]+)')
CLASS_PROPERTIES = {}


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


def isValidController(obj):
    """
    Evaluates if the supplied object is a valid controller.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.superClassOf(obj) in BASE_TYPES.values()


def isSerializableValue(value):
    """
    Evaluates if the supplied max value is serializable.

    :type value: Any
    :rtype: bool
    """

    return pymxs.runtime.superClassOf(value) in (pymxs.runtime.Value, pymxs.runtime.Number)


def iterSubAnims(obj, skipNonAnimated=False, skipNullControllers=False, skipComplexValues=False):
    """
    Returns a generator that yields sub anims from the supplied object.
    Optional keywords can be used to skip particular sub-anims.

    :type obj: pymxs.MXSWrapperBase
    :type skipNonAnimated: bool
    :type skipNullControllers: bool
    :type skipComplexValues: bool
    :rtype: iter
    """

    # Iterate through sub anims
    #
    for i in range(obj.numSubs):

        # Check if non-animated sub-anims should be skipped
        #
        subAnim = pymxs.runtime.getSubAnim(obj, i + 1)

        if skipNonAnimated and not subAnim.isAnimated:

            continue

        # Check if null controllers should be skipped
        #
        if skipNullControllers and subAnim.controller is None:

            continue

        # Check if compound values should be skipped
        #
        if skipComplexValues and not isSerializableValue(subAnim.value):

            continue

        else:

            yield subAnim


def iterMaxKeys(obj):
    """
    Returns a generator that yields max keys from the supplied controller.
    This method is more a catch all for null key properties.

    :type obj: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Check if this is a valid controller
    #
    if not isValidController(obj):

        log.info('Max object: %s, is not a valid controller!' % obj)
        return

    # Check if controller has keys
    # Be aware that max can return none for empty arrays!
    #
    keys = obj.keys

    if keys is None:

        log.info('Max object: %s, contains no key array!' % obj)
        return

    # Iterate through keys
    # Be aware key arrays can return negative sizes which breaks for loops!
    # Also be aware that keys can be missing value properties!
    #
    numKeys = keys.count

    for i in range(numKeys):

        key = keys[i]

        if pymxs.runtime.isProperty(key, pymxs.runtime.Name('value')):

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
    Returns a generator that yields all of the controllers from the supplied node.

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

        if controller in CONSTRAINT_TYPES:

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


def isPropertyAnimatable(obj, name):
    """
    Evaluates if the supplied MXS object wrapper is animatable.
    Max will throw errors if the object isn't explicitly derived from MaxObject!

    :type obj: pymxs.runtime.MXSWrapperBase
    :type name: pymxs.runtime.Name
    :rtype: bool
    """

    try:

        return pymxs.runtime.isPropertyAnimatable(obj, name)

    except RuntimeError:

        return False


def inspectClassProperties(className):
    """
    Inspects the supplied class names for writable properties.

    :type className: str
    :rtype: list[str]
    """

    # Concatenate class lookup pattern
    #
    pattern = '{className}.*'.format(className=className)

    stringStream = pymxs.runtime.StringStream('')
    pymxs.runtime.showClass(pattern, to=stringStream)

    # Iterate through lines
    #
    properties = []
    CLASS_PROPERTIES[className] = properties

    pymxs.runtime.seek(stringStream, 1)

    while not pymxs.runtime.eof(stringStream):

        line = pymxs.runtime.readLine(stringStream)
        found = PROPERTY_PARSER.findall(line)

        if len(found) == 1:

            properties.append(found[0])

    return properties


def iterDynamicProperties(obj, skipAnimatable=False, skipComplexValues=False):
    """
    Returns a generator that yield property name/value pairs from the supplied object.
    This method yields both static and dynamic properties.

    :type obj: pymxs.runtime.MaxObject
    :type skipAnimatable: bool
    :type skipComplexValues: bool
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
        key = str(name).replace(' ', '_')
        value = pymxs.runtime.getProperty(obj, name)

        if skipComplexValues and not isSerializableValue(value):

            continue

        else:

            yield key, value


def iterProperties(obj, skipAnimatable=False, skipComplexValues=False, skipDefaultValues=False):
    """
    Returns a generator that yield property name/value pairs from the supplied object.
    This method only yields properties that are on the class definition.

    :type obj: pymxs.runtime.MaxObject
    :type skipAnimatable: bool
    :type skipComplexValues: bool
    :type skipDefaultValues: bool
    :rtype: iter
    """

    # Check if class has already been inspected
    #
    cls = pymxs.runtime.classOf(obj)
    className = str(cls)
    properties = CLASS_PROPERTIES.get(className, None)

    if properties is None:

        properties = inspectClassProperties(className)

    # Iterate through property names
    #
    for key in properties:

        # Check if animatable properties should be skipped
        #
        name = pymxs.runtime.Name(key)
        isAnimatable = isPropertyAnimatable(obj, name)

        if skipAnimatable and isAnimatable:

            continue

        # Check if compound values should be skipped
        #
        value = pymxs.runtime.getProperty(obj, name)

        if skipComplexValues and not isSerializableValue(value):

            continue

        # Check if non-default values should be skipped
        #
        defaultValue, result = pymxs.runtime.DefaultParamInterface.getDefaultParamValue(cls, key, pymxs.byref(None))

        if skipDefaultValues and value == defaultValue:

            continue

        else:

            yield key, value
