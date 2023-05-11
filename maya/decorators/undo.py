import os
import sys

from maya import cmds as mc
from functools import partial
from .. import plugins
from ...decorators import abstractdecorator
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Undo(abstractdecorator.AbstractDecorator):
    """
    Overload of `AbstractDecorator` that defines Maya undo chunks.
    """

    # region Dunderscores
    __slots__ = ('_state', '_name',)
    __chunk__ = None  # Prevents nested undo chunks from closing prematurely
    __plugins__ = os.path.dirname(os.path.abspath(plugins.__file__))

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type enabled: bool
        :type name: str
        :rtype: None
        """

        # Call parent method
        #
        super(Undo, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._state = kwargs.get('state', True)
        self._name = kwargs.get('name', None)

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Evaluate undo state
        #
        if self.state:

            # Check if chunk is already open
            #
            if not stringutils.isNullOrEmpty(self.chunk):

                return

            # Ensure API undo is loaded
            #
            self.ensureLoaded()

            # Open undo chunk
            #
            self.__class__.__chunk__ = self.name
            mc.undoInfo(openChunk=True, chunkName=self.name)

        else:

            # Disable undo
            #
            mc.undoInfo(stateWithoutFlush=False)

    def __call__(self, *args, **kwargs):
        """
        Private method that is called whenever this instance is evoked.

        :rtype: Any
        """

        try:

            self.__enter__(*args, **kwargs)
            results = self.func(*args, **kwargs)
            self.__exit__(None, None, None)

            return results

        except RuntimeError as exception:

            log.error(exception)
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        # Evaluate undo state
        #
        if self.state:

            # Check if chunk can be closed
            #
            if self.name != self.chunk:

                return

            # Close undo chunk
            #
            self.__class__.__chunk__ = None
            mc.undoInfo(closeChunk=True)

        else:

            # Re-enable undo
            #
            mc.undoInfo(stateWithoutFlush=True)
    # endregion

    # region Properties
    @property
    def chunk(self):
        """
        Getter method that returns the current undo chunk.

        :rtype: Union[str, None]
        """

        return self.__class__.__chunk__

    @property
    def state(self):
        """
        Getter method that returns the undo state.

        :rtype: bool
        """

        return self._state

    @property
    def name(self):
        """
        Getter method that returns the name of this undo.

        :rtype: str
        """

        return self._name
    # endregion

    # region Methods
    def isLoaded(self):
        """
        Evaluates if the `pyUndo` plugin command has been loaded.

        :rtype: bool
        """

        return mc.pluginInfo('pyundocommand.py', query=True, loaded=True)

    def ensureLoaded(self):
        """
        Loads the `pyUndo` plugin command.

        :rtype: None
        """

        if not self.isLoaded():

            mc.loadPlugin(os.path.join(self.__plugins__, 'pyundocommand.py'), quiet=True)
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


def commit(doIt, undoIt):
    """
    Passes the supplied functions to the py-undo bridge.

    :type doIt: Callable
    :type undoIt: Callable
    :rtype: None
    """

    pyundobridge = sys.modules.get('pyundobridge')

    if pyundobridge is not None:

        log.debug(f'Sending: {doIt}, {undoIt} to py-undo bridge!')
        pyundobridge.__doit__ = doIt
        pyundobridge.__undoit__ = undoIt

        mc.pyUndo()

    else:

        log.debug('Cannot locate py-undo bridge!')
