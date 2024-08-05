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
    __slots__ = ('_state', '_previousState')

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
        self._state = kwargs.get('state', True)
        self._previousState = None

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Edit auto-key state
        #
        self._previousState = sceneutils.autoKey()

        if self.state != self.previousState:

            sceneutils.setAutoKey(self.state)

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
        if self.state != self.previousState:

            sceneutils.setAutoKey(self.previousState)
    # endregion

    # region Properties
    @property
    def state(self):
        """
        Getter method that returns the requested auto-key state.

        :rtype: bool
        """

        return self._state

    @property
    def previousState(self):
        """
        Getter method that returns the previous auto-key state.

        :rtype: bool
        """

        return self._previousState
    # endregion
