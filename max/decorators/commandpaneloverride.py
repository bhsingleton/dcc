import pymxs

from functools import partial
from ...decorators import abstractdecorator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CommandPanelOverride(abstractdecorator.AbstractDecorator):
    """
    Overload of `AbstractDecorator` that overrides the command panel task mode at runtime.
    """

    # region Dunderscores
    __slots__ = ('_mode', '_revert', '_previous')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key mode: str
        :key revert: bool
        :rtype: None
        """

        # Call parent method
        #
        super(CommandPanelOverride, self).__init__(*args, **kwargs)

        # Declare public variables
        #
        self._mode = pymxs.runtime.Name(kwargs.get('mode', 'create'))
        self._revert = kwargs.get('revert', False)
        self._previous = pymxs.runtime.getCommandPanelTaskMode()

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Inspect current task mode
        #
        self.previous = pymxs.runtime.getCommandPanelTaskMode()

        if self.previous != self.mode:

            pymxs.runtime.setCommandPanelTaskMode(self.mode)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        # Check if override should be reverted
        #
        if self.revert:

            pymxs.runtime.setCommandPanelTaskMode(self.previous)
    # endregion

    # region Properties
    @property
    def mode(self):
        """
        Getter method that returns the override mode.

        :rtype: pymxs.runtime.Name
        """

        return self._mode

    @property
    def revert(self):
        """
        Getter method that returns the revert flag.

        :rtype: bool
        """

        return self._revert

    @property
    def previous(self):
        """
        Getter method that returns the previous mode.

        :rtype: pymxs.runtime.Name
        """

        return self._previous

    @previous.setter
    def previous(self, previous):
        """
        Setter method that updates the previous mode.

        :type previous: pymxs.runtime.Name
        :rtype: None
        """

        self._previous = previous
    # endregion


def commandPanelOverride(*args, **kwargs):
    """
    Returns a CommandPanelOverride wrapper for the supplied function.

    :key mode: str
    :key revert: bool
    :rtype: method
    """

    # Check number of arguments
    #
    numArgs = len(args)

    if numArgs == 0:

        return partial(commandPanelOverride, **kwargs)

    elif numArgs == 1:

        return CommandPanelOverride(*args, **kwargs)

    else:

        raise TypeError('commandPanelOverride() expects at most 1 argument (%s given)!' % numArgs)
