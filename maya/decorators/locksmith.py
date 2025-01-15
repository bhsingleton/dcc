from maya.api import OpenMaya as om
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
    __slots__ = ('_plug', '_isLocked', '_force')

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
        self._plug = om.MPlug()
        self._isLocked = False
        self._force = False

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Search arguments for plug
        #
        plugs = [arg for arg in args if isinstance(arg, om.MPlug)]
        numPlugs = len(plugs)

        if numPlugs != 1:

            return

        # Check if force was used
        #
        self._plug = plugs[0]
        self._isLocked = bool(self.plug.isLocked)
        self._force = kwargs.get('force', False)

        if self._force:

            self.plug.isLocked = False

        elif self.plug.isLocked and not self.force:

            log.debug(f'Cannot mutate locked "{self.plug.info}" plug!')

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
        if not self.plug.isNull and (self.force and self.isLocked):

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
