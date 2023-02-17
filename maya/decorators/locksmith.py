from functools import partial
from ...decorators import abstractdecorator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Locksmith(abstractdecorator.AbstractDecorator):
    """
    Overload of `AbstractDecorator` that toggles the lock state on plugs when mutating values.
    """

    # region Dunderscores
    __slots__ = ('_plug', '_value', '_isLocked', '_force')

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
        self._isLocked = False
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
        self._isLocked = bool(self.plug.isLocked)
        self._force = kwargs.get('force', False)

        if self._force:

            self.plug.isLocked = False

        elif self.plug.isLocked and not self.force:

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
        if self.force and self.isLocked:

            self.plug.isLocked = True
    # endregion

    # region Properties
    @property
    def plug(self):
        """
        Getter method that returns the current plug.

        :rtype: om.MPlug
        """

        return self._plug

    @property
    def value(self):
        """
        Getter method that returns the current value.

        :rtype: Any
        """

        return self._value

    @property
    def force(self):
        """
        Getter method that returns the force flag.

        :rtype: bool
        """

        return self._force

    @property
    def isLocked(self):
        """
        Getter method that returns the locked state.

        :rtype: bool
        """

        return self._isLocked
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

