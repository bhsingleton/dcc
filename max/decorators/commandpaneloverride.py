import pymxs

from functools import partial
from dcc.decorators import abstractdecorator
from dcc.max import fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CommandPanelOverride(abstractdecorator.AbstractDecorator):
    """
    Overload of AbstractDecorator that overrides the command panel task mode at runtime.
    """

    # region Dunderscores
    __slots__ = ('_mode', '_autoSelect')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(CommandPanelOverride, self).__init__(*args, **kwargs)

        # Declare public variables
        #
        self._mode = kwargs.get('mode', 'create')
        self._autoSelect = kwargs.get('autoSelect', True)

    def __enter__(self):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Inspect current task mode
        #
        currentMode = pymxs.runtime.getCommandPanelTaskMode()

        if currentMode != self.mode:

            pymxs.runtime.setCommandPanelTaskMode(self.mode)

        # Check if auto select is enabled
        #
        if self.autoSelect and isinstance(self._instance, fnnode.FnNode):

            # Check if node is selected
            # Don't want to incur cycle checks from any selection callbacks!
            #
            if not self._instance.isIsolated() and self._instance.isValid():

                self._instance.select(replace=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        pass
    # endregion

    # region Properties
    @property
    def mode(self):
        """
        Getter method that returns the override mode.

        :rtype: str
        """

        return pymxs.runtime.name(self._mode)

    @property
    def autoSelect(self):
        """
        Getter method that returns the auto select state.

        :rtype: str
        """

        return self._autoSelect
    # endregion


def commandPanelOverride(*args, **kwargs):
    """
    Returns an command panel override wrapper for the supplied function.

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
