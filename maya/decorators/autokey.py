from maya.api import OpenMaya as om
from functools import partial
from ...maya.libs import sceneutils, plugutils, animutils
from ...decorators import abstractdecorator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AutoKey(abstractdecorator.AbstractDecorator):
    """
    Overload of `AbstractDecorator` that ensures that any plugs are keyed when auto-key is enabled.
    """

    # region Dunderscores
    __slots__ = ('_autoKey', '_plugs')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(AutoKey, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._autoKey = None
        self._plugs = []

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Check if auto-key is enabled
        #
        self._autoKey = sceneutils.autoKey()

        if not self.autoKey:

            return

        # Iterate through plugs
        #
        self._plugs = [arg for arg in args if isinstance(arg, om.MPlug)]

        for plug in self.plugs:

            # Check if plug requires key
            #
            if not plugutils.isAnimated(plug) and plug.isKeyable:

                animutils.ensureKeyed(plug)

            else:

                continue

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
    def autoKey(self):
        """
        Getter method that returns the auto-key state.

        :rtype: bool
        """

        return self._autoKey

    @property
    def plugs(self):
        """
        Getter method that returns the plugs to be keyed.

        :rtype: List[om.MPlug]
        """

        return self._plugs
    # endregion


def autokey(*args, **kwargs):
    """
    Returns an auto-key wrapper for the supplied function.

    :rtype: Callable
    """

    # Check number of arguments
    #
    numArgs = len(args)

    if numArgs == 0:

        return partial(autokey, **kwargs)

    elif numArgs == 1:

        return AutoKey(*args, **kwargs)

    else:

        raise TypeError('autokey() expects at most 1 argument (%s given)!' % numArgs)

