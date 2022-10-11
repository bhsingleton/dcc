from functools import partial
from ...decorators import abstractdecorator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Locksmith(abstractdecorator.AbstractDecorator):
    """
    Overload of AbstractDecorator used to toggle lock states when calling plug mutators.
    """

    # region Dunderscores
    __slots__ = ('_plug', '_value', '_wasLocked', '_force')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(Locksmith, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._plug = None
        self._value = None
        self._wasLocked = False
        self._force = False

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Inspect number of arguments
        #
        numArgs = len(args)

        if numArgs != 2:

            raise TypeError('__enter__() expects 2 arguments (%s given)!' % numArgs)

        # Check if force was used
        #
        self._plug, self._value = args
        self._wasLocked = bool(self._plug.isLocked)
        self._force = kwargs.get('force', False)

        if self._force:

            self._plug.isLocked = False

        elif self._plug.isLocked and not self._force:

            raise TypeError('__enter__() cannot mutate locked plug!')

        else:

            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        # Check if plug should be relocked
        #
        if self._force and self._wasLocked:

            self._plug.isLocked = True
    # endregion


def locksmith(*args, **kwargs):
    """
    Returns an undo wrapper for the supplied function.

    :key name: str
    :rtype: Callable
    """

    # Check number of arguments
    #
    numArgs = len(args)

    if numArgs == 0:

        return partial(locksmith, **kwargs)

    elif numArgs == 1:

        return Locksmith(*args, **kwargs)

    else:

        raise TypeError('locksmith() expects at most 1 argument (%s given)!' % numArgs)

