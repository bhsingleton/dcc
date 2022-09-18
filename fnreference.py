import inspect

from . import __application__
from .abstract import afnreference

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


if __application__ == 'maya':

    from .maya.fnreference import *

elif __application__ == '3dsmax':

    from .max.fnreference import *

else:

    raise ImportError('Unable to import dcc reference-helpers for: %s application!' % __application__)


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

        return overrideFunctionSet(type(cls))

    # Verify this is a subclass of AFnReference
    #
    if issubclass(cls, afnreference.AFnReference):

        __dict__['FnReference'] = cls

    else:

        raise TypeError('overrideFunctionSet() expects an AFnReference subclass (%s given)!' % cls.__name__)
