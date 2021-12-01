import pymxs

from six import string_types
from functools import partial

from .. import fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CoordSysOverride(object):
    """
    Class decorator used to override the co-ordinate system at runtime.
    Accepted values include: view, screen, world, parent, gimbal, local, grid and working_pivot
    """

    __slots__ = ('_mode', '_previous', '_instance', '_owner', '_func')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(CoordSysOverride, self).__init__()

        # Declare public variables
        #
        self._mode = pymxs.runtime.Name(kwargs.get('mode', 'local'))
        self._previous = pymxs.runtime.getRefCoordSys()
        self._instance = None
        self._owner = None
        self._func = None

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self._func = args[0]

    def __get__(self, instance, owner):
        """
        Private method called whenever this object is accessed via attribute lookup.

        :type instance: object
        :type owner: type
        :rtype: Undo
        """

        self._instance = instance
        self._owner = owner

        return self

    def __call__(self, *args, **kwargs):
        """
        Private method that is called whenever this instance is evoked.

        :type func: function
        :rtype: function
        """

        # Execute order of operations
        #
        self.__enter__()
        results = self.func(*args, **kwargs)
        self.__exit__(None, None, None)

        return results

    def __enter__(self):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        pymxs.runtime.toolMode.coordsys(self.mode)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        pymxs.runtime.toolMode.coordsys(self.previous)

    @property
    def mode(self):
        """
        Getter method that returns the override mode.

        :rtype: pymxs.runtime.Name
        """

        return pymxs.runtime.name(self._mode)

    @property
    def previous(self):
        """
        Getter method that returns the previous mode.

        :rtype: pymxs.runtime.Name
        """

        return self._previous

    @property
    def func(self):
        """
        Getter method used to return the wrapped function.
        If this is a descriptor then the function will be bound.

        :rtype: function
        """

        if self._instance is not None:

            return self._func.__get__(self._instance, self._owner)

        else:

            return self._func


def coordSysOverride(*args, **kwargs):
    """
    Returns an command panel override wrapper for the supplied function.

    :rtype: method
    """

    # Check number of arguments
    #
    numArgs = len(args)

    if numArgs == 0:

        return partial(coordSysOverride, **kwargs)

    elif numArgs == 1:

        return CoordSysOverride(*args, **kwargs)

    else:

        raise TypeError('commandPanelOverride() expects at most 1 argument (%s given)!' % numArgs)
