import inspect

from . import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def bindProperty(instance, func):
    """
    Returns a bound method from the supplied instance and function.

    :type instance: object
    :type func: function
    :rtype: function
    """

    # Check if function is valid
    #
    if inspect.isfunction(func) and hasattr(func, '__get__'):

        return func.__get__(instance, type(instance))

    else:

        return None


def getPropertyAccessors(obj, name):
    """
    Returns the property accessors from the associated name and object.

    :type obj: object
    :type name: str
    :rtype: function, function
    """

    # Check if name is valid
    #
    if stringutils.isNullOrEmpty(name):

        return None, None

    # Inspect object's base class
    #
    cls = type(obj)
    func = getattr(cls, name, None)

    if isinstance(func, property):

        return bindProperty(obj, func.fget), bindProperty(obj, func.fset)

    elif inspect.isfunction(func):

        otherName = 'set{name}'.format(name=stringutils.pascalize(func.__name__))
        otherFunc = getattr(cls, otherName, None)

        return bindProperty(obj, func), bindProperty(obj, otherFunc)

    else:

        return None, None
