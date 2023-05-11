from functools import partial
from ...maya.libs import sceneutils
from ...decorators import abstractdecorator

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Animate(abstractdecorator.AbstractDecorator):
    """
    Overload of `AbstractDecorator` that toggles the auto-key state.
    """

    # region Dunderscores
    __slots__ = ('_autoKey',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(Animate, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._autoKey = None

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Cache auto-key state
        #
        self._autoKey = sceneutils.autoKey()

        # Enable auto-key
        #
        if not self.autoKey:

            sceneutils.enableAutoKey()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        # Reset auto-key state
        #
        autoKey = sceneutils.autoKey()

        if autoKey != self.autoKey:

            sceneutils.setAutoKey(self.autoKey)
    # endregion

    # region Properties
    @property
    def autoKey(self):
        """
        Getter method that returns the auto-key state.

        :rtype: bool
        """

        return self._autoKey
    # endregion


def animate(*args, **kwargs):
    """
    Returns an auto-key wrapper for the supplied function.

    :rtype: Callable
    """

    # Check number of arguments
    #
    numArgs = len(args)

    if numArgs == 0:

        return partial(animate, **kwargs)

    elif numArgs == 1:

        return Animate(*args, **kwargs)

    else:

        raise TypeError('autokey() expects at most 1 argument (%s given)!' % numArgs)

