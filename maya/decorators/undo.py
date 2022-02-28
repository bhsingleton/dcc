import maya.cmds as mc

from six import string_types
from functools import partial

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Undo(object):
    """
    Base class used to manage undo chunks either as a decorator or with statement.
    """

    __slots__ = ('_name', '_instance', '_owner', '_func')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type name: str
        :rtype: None
        """

        # Call parent method
        #
        super(Undo, self).__init__()

        # Declare public variables
        #
        self._name = kwargs.get('name')
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

    def __enter__(self, *args):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        mc.undoInfo(openChunk=True, chunkName=self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        mc.undoInfo(closeChunk=True)

    @property
    def name(self):
        """
        Getter method that returns the name of this undo.

        :rtype: str
        """

        return self._name

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


def undo(*args, **kwargs):
    """
    Returns an undo wrapper for the supplied function.

    :keyword name: str
    :rtype: function
    """

    # Check number of arguments
    #
    numArgs = len(args)

    if numArgs == 0:

        return partial(undo, **kwargs)

    elif numArgs == 1:

        return Undo(*args, **kwargs)

    else:

        raise TypeError('undo() expects at most 1 argument (%s given)!' % numArgs)
