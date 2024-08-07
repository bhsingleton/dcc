import pymxs

from dcc.decorators import abstractdecorator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CoordSysOverride(abstractdecorator.AbstractDecorator):
    """
    Overload of AbstractDecorator that overrides the co-ordinate system at runtime.
    Accepted values include: view, screen, world, parent, gimbal, local, grid and working_pivot
    """

    # region Dunderscores
    __slots__ = ('_mode', '_revert', '_previous')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(CoordSysOverride, self).__init__(*args, **kwargs)

        # Declare public variables
        #
        self._mode = pymxs.runtime.Name(kwargs.get('mode', 'local'))
        self._revert = kwargs.get('revert', False)
        self._previous = pymxs.runtime.getRefCoordSys()

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        self.previous = pymxs.runtime.getRefCoordSys()

        if self.previous != self.mode:

            mode = kwargs.get('mode', self.mode)
            pymxs.runtime.setRefCoordSys(mode)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        if self.revert:

            pymxs.runtime.setRefCoordSys(self.previous)
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
