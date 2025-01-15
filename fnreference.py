from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnreference import *

elif __application__ == DCC.MAX:

    from .max.fnreference import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC reference-helpers for: {__executable__}!')


def overrideFunctionSet(cls):
    """
    Overrides the imported DCC function set.
    This is important for DCC applications that require custom reference systems such as 3ds Max.

    :type cls: class
    :rtype: None
    """

    # Verify this is a class
    #
    if not inspect.isclass(cls):

        cls = type(cls)

    # Verify this is a subclass of AFnReference
    #
    if issubclass(cls, afnreference.AFnReference):

        __dict__['FnReference'] = cls

    else:

        raise TypeError(f'overrideFunctionSet() expects a AFnReference subclass ({cls.__name__} given)!')
