import maya.cmds as mc

from functools import partial
from dcc.decorators import abstractdecorator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Undo(abstractdecorator.AbstractDecorator):
    """
    Base class used to manage undo chunks either as a decorator or with statement.
    """

    # region Dunderscores
    __slots__ = ('_name',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type name: str
        :rtype: None
        """

        # Call parent method
        #
        super(Undo, self).__init__(*args, **kwargs)

        # Declare public variables
        #
        self._name = kwargs.get('name')

    def __call__(self, *args, **kwargs):
        """
        Private method that is called whenever this instance is evoked.

        :type func: function
        :rtype: function
        """

        # Execute order of operations
        #
        results = None

        try:

            self.__enter__(*args, **kwargs)
            results = self.func(*args, **kwargs)
            self.__exit__(None, None, None)

        except RuntimeError as exception:

            log.error(exception)

        finally:

            return results

    def __enter__(self, *args, **kwargs):
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
    # endregion

    # region Properties
    @property
    def name(self):
        """
        Getter method that returns the name of this undo.

        :rtype: str
        """

        return self._name
    # endregion


def undo(*args, **kwargs):
    """
    Returns an undo wrapper for the supplied function.

    :key name: str
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
