import pymxs
import re

from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__property_parser__ = re.compile(r'\.([a-zA-Z0-9_]+)')
__properties__ = {}  # Used by `inspectClassProperties` method for caching purposes!


def isValue(value):
    """
    Evaluates if the supplied max value is serializable.

    :type value: Any
    :rtype: bool
    """

    return pymxs.runtime.superClassOf(value) in (pymxs.runtime.Value, pymxs.runtime.Number)


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

    except RuntimeError as exception:

        log.debug(exception)
        return False


def copyProperties(copyFrom, copyTo):
    """
    Copies the key-value pairs to the specified object.

    :type copyFrom: pymxs.MXSWrapperBase
    :type copyTo: pymxs.MXSWrapperBase
    :rtype: None
    """

    for (key, value) in iterStaticProperties(copyFrom, skipNonValues=True, skipDefaultValues=True):

        pymxs.runtime.setProperty(copyTo, key, value, applyUIScalling=False)


def getDefaultPropertyValue(cls, name):
    """
    Returns the default value for the specified property.

    :type cls: pymxs.MXSWrapperBase
    :type name: str
    :rtype: Any
    """

    try:

        return pymxs.runtime.DefaultParamInterface.getDefaultParamValue(cls, name, None)

    except (SystemError, RuntimeError):

        log.debug(f'Error encountered while retrieving "{cls}::{name}" default value!')
        return None


def tryGetPropertyValue(obj, name, default=None):
    """
    Returns the value from the specified property.
    If no property exists then the default value is returned instead.

    :type obj: pymxs.MXSWrapperBase
    :type name: str
    :type default: Any
    :rtype: Any
    """

    if pymxs.runtime.isProperty(obj, name):

        return pymxs.runtime.getProperty(obj, name)

    else:

        return default


def inspectClassProperties(maxClassName):
    """
    Inspects the supplied class names for writable properties.

    :type maxClassName: str
    :rtype: list[str]
    """

    # Check if class has already been inspected
    #
    properties = __properties__.get(maxClassName, None)

    if properties is not None:

        return properties

    # Concatenate class lookup pattern
    #
    pattern = '{maxClassName}.*'.format(maxClassName=maxClassName)

    stringStream = pymxs.runtime.StringStream('')
    pymxs.runtime.showClass(pattern, to=stringStream)

    # Iterate through string stream
    #
    properties = []
    pymxs.runtime.seek(stringStream, 0)

    while not pymxs.runtime.eof(stringStream):

        line = pymxs.runtime.readLine(stringStream)
        found = __property_parser__.findall(line)

        if len(found) == 1:

            properties.append(found[0])

    # Cache list for later use
    #
    __properties__[maxClassName] = properties
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
    maxClass = pymxs.runtime.classOf(obj)
    maxClassName = str(maxClass)

    properties = inspectClassProperties(maxClassName)

    for key in properties:

        # Check if property is accessible
        # The class inspector can yield private properties that are not accessible!
        #
        name = pymxs.runtime.Name(key)

        if not pymxs.runtime.isProperty(obj, name):

            continue

        # Check if animatable properties should be skipped
        #
        if skipAnimatable:

            isAnimatable = isPropertyAnimatable(obj, name)

            if isAnimatable:

                continue

        # Check if non-values should be skipped
        #
        value = pymxs.runtime.getProperty(obj, name)

        if skipNonValues:

            isNonValue = not isValue(value)

            if isNonValue:

                continue

        # Check if non-default values should be skipped
        #
        if skipDefaultValues:

            default = getDefaultPropertyValue(maxClass, key)
            isDefault = (value == default)

            if isDefault:

                continue

        yield key, value
